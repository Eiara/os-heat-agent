from abc import ABCMeta, abstractmethod, ABC
import os
import requests
import tempfile
import subprocess
import structlog as logging
from pathlib import Path

from .runners import babashka, shell, legacy, Output

from .errors import *

logger = logging.getLogger(__name__)
# logger.addHandler(logging.NullHandler())

TOOLS = {
  "babashka": babashka,
  "shell":    shell,
}

# Schemas!
# TODO: Add schemas



# Inputs that come from OpenStack directly
heat_inputs = [
  "deploy_server_id",
  "deploy_action",
  "deploy_stack_id",
  "deploy_resource_name",
  "deploy_signal_transport",
  "deploy_signal_id",
  "deploy_signal_verb"
]

# inputs that we've defined to be present.
# These may not always be present, and will depend on the specific
#   implementation as to whether or not they'll be necessary.
#   But these are a reference for those.
agent_inputs = [
  "os_heat_agent_tool",
  "os_heat_agent_serialize"
]

agent_outputs = [
  # Just the one that we need to be here.
  # Do we expect any others here?
  "os_heat_agent_is_error"
]


class Deployment(ABC):
  
  """
  Base deployment class. Should not be used.
  """
  
  required_options = []
  
  def __init__(self, data: dict):
    self._data = data
    
    self._heat_inputs = {}
    self._internal_inputs = {}
    self._environment_variables = {}
    self._passthrough_inputs = {}
    # Put our inputs in the appropriate places.
    
    for input in data["inputs"]:
      logger.debug(input["name"])
      if input["name"] in heat_inputs:
        self._heat_inputs[ input["name"] ] = input
      elif input["name"].startswith("os_heat_agent_"):
        self._internal_inputs[input["name"]] = input
      elif input["name"].startswith("envar_"):
        self._environment_variables[input["name"]] = input
      else:
        self._passthrough_inputs[ input["name"] ] = input["value"]
    
    # Step one: Pull our tooling out
    tooling = self._data["group"].split("::")
    self._group = tooling[0]
    
    # Save the tooling as an array, since the self.tool property will expect
    #   the first member to be the name of the tool, and the second value to
    #   be any arguments to the runner, if needed.
    self._tool = [t.lower() for t in tooling[1:]]
    
    # This uses the Shell runner to handle the legacy style of SoftwareConfig,
    #   since it was relatively easy to adapt the Shell runner to work in the
    #   expected way.
        
    # Now is when we can make some validity assertions about our 
    # inputs and outputs, since we control the spec that gets asserted for 
    # this! Yay us!
    
    self._outputs = data.get("outputs", {})
    self._options = data.get("options", {})
    
    self.normalize()
  
  @abstractmethod
  def normalize(self) -> None:
    pass
  
  @property
  def inputs(self):
    return self._passthrough_inputs
  
  def validate(self) -> bool:
    """
    Validate this deployment.
    
    Returns:
      True, if the deployment is validated.
    Raises:
      MissingInputs, if required OS Heat inputs are not present.
      MissingOutputs, if required OS Heat Agent outputs are not present.
      NoSuchRunner, if the requested tool does not exist
    """
    # Validate ourself, make sure we just received a valid update
    # This will check a couple of things:
    #   - presence of options, in self.required_options
    #   - presence of outputs, in self.required_outputs
    if set(self.required_options) - set(self._options.keys()):
      missing = set(self.required_options) - set(self._options.keys())
      logger.fatal("Missing os_heat_agent options %s", str(missing))
      raise MissingInputs(list(missing))
    
    outputs = [ output["name"] for output in self._outputs ]
    
    if set(agent_outputs) - set(outputs):
      missing_outputs = set(agent_outputs) - set(outputs)
      logger.fatal("missing os_heat_agent outputs %s", str(missing_outputs))
      raise MissingOutputs(list(missing_outputs))
      
    # Check the tool is valid
    try:
      TOOLS[self._tool[0]]
    except KeyError:
      logger.error("Tool %s not loaded", self._tool[0])
      raise NoSuchRunner(f"Tool {self._tool[0]} not found")
    return True
  
  @property
  def environment(self) -> dict:
    env = {}
    for name, obj in self._environment_variables.items():
      # Extract the name=value pairs
      # We're not really bothering with the additional detail in these
      # inputs, yet anyway.
      env[name.replace("envar_", "")] = obj["value"]
    return env
  
  
  def signal(self, payload: dict) -> requests.Response: 
    """Signals completion of the deployment to OpenStack.
    
    If a signal has been defined by the orchestration configuration, attempt to
      signal to OpenStack that the result has, or hasn't, been successfully
      completed.
    
    Args:
      payload (dict): Signal value for OpenStack. Expected schema is:
        
    
    Returns:
      :obj:`requests.Response` or None: a Requests response.
    """
    # Sends the signal, if applicable, back to OpenStack.
    # Payload is expected to be a dict.
    deploy_signal = self._heat_inputs.get("deploy_signal_id", None)
    logger.debug(self._heat_inputs)
    if not deploy_signal:
      # If there's no signal, we don't have anything to do.
      logger.debug("No signal")
      return None
    
    
    url = deploy_signal["value"]
    # Default to POST.
    verb = self._internal_inputs.get("deploy_signal_verb", {}).get("value", "POST")
    return requests.request(verb, url, json=payload)
    
  @property
  def tool(self):
    """
    Returns the name of the tool that this Deployment will be using.
    This will either be a path to a callable, such as /bin/bash, or the
      name of the runner itself, for lookup to find the exact runner.
    Tool is set via the incoming "group" value from the OpenStack deployment
      JSON.
    """
    
    # The group name, per OpenStack documentation, is intended to be the tool
    #   to be used.
    # Currently we only support shell (via running a bash script) and Babashka
    # This will eventually be extended to support other things as interest
    #   and need allow.
    # So we should define some mappings.
    # GroupName::Tool::Subtool ?
    # So, Web::Shell::Bash?
    # Or Shell::Bash::Web
    # Or Web::Babashka?
    # Nah, group then tool I think, since the group name may end up being
    #   important later.
    # If it's heat::ungrouped, we should throw an error as well.
    # return self._options["os_heat_agent_tool"]
    # 
    # if self._data["group"] == "Heat::Ungrouped":
    #   # os_heat_agent_tool needs to be set, which will be enforced by the init
    #   # check for required options.
    #   return self._options["os_heat_agent_tool"]
    # 
    # So now we check for the mappings of tools we know about
    
    # Pull the group name off the top.
    # This will get logged somewhere I guess?
    # Hmm maybe it should be Heat::Groupname::Tool ?
    # So like Heat::Web::Babashka?
    
    return self._tool[0]
  
  @property
  def config(self) -> dict:
    # Sets up our group information, if needed, for downstream consumers that 
    #   make use of a sub-group setup.
    #   Currently:
    #     - Shell
    # 
    
    return self._data["config"]
    
  @property
  def inputs(self) -> dict:
    return self._passthrough_inputs
    
  def run(self) -> Output:
    """
    Run the configuration management.
    Structured config expects to hand off to a runner to execute.
    Currently supported runners are Shell and Babashka.
    """
    try:
      runner = TOOLS[self.tool.lower()]
    except KeyError:
      logger.fatal("No such runner: %s", self.tool.lower())
      raise NoSuchRunner(self.tool.lower())
    runner = TOOLS[self.tool]
    
    logger.debug("using tool %s", self.tool)
    
    # Configuration data is always a string for a SoftwareConfig.
    # Input options are expected to be environment variables.
    
    if not runner.supports(self.__class__.__name__):
      raise NotImplementedError(f"Runner {self.tool} not supported by {self.__class__.__name__}")
    
    manifest = self.config
    runner.pre(manifest, self.inputs)
    response = runner.run(manifest, self.environment)
    runner.post(manifest)
    
    logger.debug(response.stdout)
    logger.debug(response.stderr)
    logger.debug(response.exit_code)
    
    return response
    
    resp = {
      "deploy_stdout": response.stdout,
      "deploy_stderr": response.stderr,
      "deploy_status_code": str(response.exit_code)
    }
    
    if response.exit_code != 0:
      logger.debug("Reporting error")
      resp["os_heat_agent_is_error"] = True
    
    return resp
    
###
###
###

class SoftwareConfig(Deployment):
  # required_fields = [
  #   "os_heat_agent_tool"
  # ]
  # 
  # def validate(self):
  #   # validate ourself
  #
  required_options = [
    "os_heat_agent_tool",
    "os_heat_agent_serialize"
  ]
  
  
  def normalize(self) -> None:
    data = {}
    
    if self._tool[0] == "ungrouped":
      self._tool = ["shell", Path(self._options["os_heat_agent_tool"]).name]
    
    if isinstance(self._data["config"], dict):
      return
    # Command becomes
    data["command"] = self._data["config"]
    data["group"] = self._tool[1:]
    data["serialize"] = self.should_serialize
    self._data["config"] = data
  
  @property
  def should_serialize(self) -> bool:
    try:
      return self._options["os_heat_agent_serialize"]
    except:
      return False
      
    
  # def run(self) -> dict:
  #   # run the config!
  #   runner = TOOLS[self.tool]
  #   
  #   logger.debug("using tool %s" % tool)
  #   
  #   # Configuration data is always a string for a SoftwareConfig.
  #   # Input options are expected to be environment variables.
  #   
  #   if not runner.supports(self.__class__.__name__):
  #     raise NotImplementedError(f"Runner {self.tool} not supported by SoftwareConfig")
  #   
  #   manifest = self._data["config"]
  #   runner.pre(manifest, self.input)
  #   response = runner.run(manifest, self.environment)
  #   runner.post(manifest)
  #   
  #   logger.debug(response.stdout)
  #   logger.debug(response.stderr)
  #   logger.debug(response.returncode)
  #   
  #   resp = {
  #     "deploy_stdout": response.stdout,
  #     "deploy_stderr": response.stderr,
  #     "deploy_status_code": str(response.returncode)
  #   }
  #   
  #   if response.returncode != 0:
  #     logger.debug("Reporting error")
  #     resp["os_heat_agent_is_error"] = True
  #   
  #   return resp
    
    # if self.should_serialize:
    #   logger.debug("serializing config")
    #   logger.debug(manifest)
    #   # Write config out to disk and run it like that
    #   serialised = tempfile.NamedTemporaryFile()
    #   serialised.write(bytes(manifest, "utf-8"))
    #   serialised.flush() # Write it to disk so that things can work as expected
    #   manifest = serialised.name
    #   logger.debug(serialised.name)
    # 
    # env = self.environment
    # # Inject PATH into the subprocess call
    # # TODO: What else should we inject here
    # logger.debug(env)
    # env["PATH"] = os.environ["PATH"]
    # response = subprocess.run(
    #   [tool, manifest], 
    #   capture_output=True,
    #   env=env,
    #   # Treat output as pure text
    #   text=True
    # )
    # if self.should_serialize:
    #   # Deletes the file
    #   # I guess the entire above could be done with a context manager instead
    #   #   of like this. Hm.
    #   serialised.close()
    # 
    # logger.debug(response.stdout)
    # logger.debug(response.stderr)
    # logger.debug(response.returncode)
    # 
    # resp = {
    #   "deploy_stdout": response.stdout,
    #   "deploy_stderr": response.stderr,
    #   "deploy_status_code": str(response.returncode)
    # }
    # 
    # if response.returncode != 0:
    #   logger.debug("Reporting error")
    #   resp["os_heat_agent_is_error"] = True
    # 
    # return resp


###
###
###

class StructuredConfig(Deployment):
  
  # A structured config doesn't(?) require any agent options
  # required_options = []
  
  def normalize(self) -> bool:
    self._data["config"]["group"] = self._tool[1:]
  
  def validate(self) -> bool:
    super().validate()
  
  # def run(self) -> Output:
  #   """
  #   Run the configuration management.
  #   Structured config expects to hand off to a runner to execute.
  #   Currently supported runners are Shell and Babashka.
  #   """
  #   try:
  #     runner = TOOLS[self.tool.lower()]
  #   except KeyError:
  #     logger.fatal("No such runner: ", self.tool.lower())
  #     raise NoSuchRunner(self.tool.lower())
  #   
  #   runner.pre(self.config, self.inputs)
  #   resp = runner.run(self.config, self.environment)
  #   # 
  #   # try:
  #   # except FileNotFoundError as e:
  #   #   pass
  #   # except RunnerError as e:
  #   #   pass
  #   runner.post(self.config)
  #   return resp

class SoftwareComponent(Deployment):
  # required_fields = [
  #   "os_heat_agent_tool", # What tool we're using to run the configuration?
  #   "os_heat_agent_serialize", # Should we be serializing the configuration we've gotten?
  #   "os_heat_agent_serialization_path",  # where should we be serializing it?
  #   "os_head_agent_serialization_strategy" # how we should be serializing? accepted options are "json", "yaml", and "shell"
  # ]
  # 
  # @property
  # def serialization_path(self):
  #   return self._options["os_heat_agent_serialization_path"]
  # @property
  # def serialization_strategy(self):
  #   return self._options["os_heat_agent_serialization_strategy"].lower()
  # 
  # def serialize(self):
  #   pass
  # 
  def run(self):
    pass
    
    
    
###
### 
###

def get_deployment(data: dict) -> Deployment:
  
  if type(data["config"]) == str:
    # It's an OS::Heat::SoftwareConfig
    return SoftwareConfig(data)
  elif type(data["config"]) == dict:
    # It could be one of two things ...
    if type(data.get("configs", None)) == list:
      # It's an OS::Heat::SoftwareComponent
      return SoftwareComponent(data)
    else:
      # It's an OS::Heat::StructuredConfig
      return StructuredConfig(data)