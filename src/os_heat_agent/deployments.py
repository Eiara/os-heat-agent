import os
import requests
import logging
import tempfile
import subprocess

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

class MissingInputs(Exception): pass

# Schemas!


###
###
###

def get_deployment(data):
  
  if type(data["config"]) == str:
    # It's an OS::Heat::SoftwareConfig
    return SoftwareConfig(data)
  elif type(data["config"]) == dict:
    # It could be one of two things ...
    if type(tasks.get("configs", None)) == list:
      # It's an OS::Heat::SoftwareComponent
      return SoftwareComponent(data)
    else:
      # It's an OS::Heat::StructuredDeployment
      return StructuredDeployment(data)

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

# inputs that we expect/require to be present
agent_inputs = [
  "os_heat_agent_tool",
  "os_heat_agent_serialize"
]

agent_outputs = [
  # Just the one that we need to be here.
  "os_heat_agent_is_error"
]

def log_test(val):
  logger.warn(val)


class Deployment:
  
  def __init__(self, data):
    self._data = data
    
    self._heat_inputs = {}
    self._internal_inputs = {}
    self._environment_variables = {}
    self._passthrough_inputs = {}
    for input in data["inputs"]:
      logger.debug(input["name"])
      if input["name"] in heat_inputs:
        self._heat_inputs[ input["name"] ] = input
      elif input["name"].startswith("os_heat_agent_"):
        self._internal_inputs[input["name"]] = input
      elif input["name"].startswith("envar_"):
        self._environment_variables[input["name"]] = input
      else:
        self._passthrough_inputs[ input["name"] ] = input
        
    # Now is when we can make some validity assertions about our 
    # inputs and outputs, since we control the spec that gets asserted for 
    # this! Yay us!
    
    # If the set of 
    if set(agent_inputs) < set(data["options"].keys()):
      missing = set(agent_inputs) - set(data["options"].keys())
      logger.fatal("Missing os_heat_agent options {}", str(missing))
      raise MissingInputs(list(missing))
    
    outputs = [ output["name"] for output in data["outputs"] ]
    if set(agent_outputs) < set(outputs):
      missing_outputs = set(agent_inputs) - set(outputs)
      logger.fatal("missing os_heat_agent outputs {}", str(missing_outputs))
    
    self._outputs = data["outputs"]
    self._options = data["options"]
  
  @property
  def environment(self):
    env = {}
    for name, obj in self._environment_variables.items():
      # Extract the name=value pairs
      # We're not really bothering with the additional detail in these
      # inputs, yet anyway.
      env[name.replace("envar_", "")] = obj["value"]
    return env
    
  def signal(self, payload):
    # Sends the signal, if applicable, back to OpenStack.
    # Payload is expected to be a dict.
    deploy_signal = self._heat_inputs.get("deploy_signal_id", None)
    logger.debug(self._heat_inputs)
    if not deploy_signal:
      # If there's no signal, we don't have anything to do.
      logger.debug("No signal")
      return None
    
    # TODO:
    # Support things that aren't CFN Signal
    url = deploy_signal["value"]
    # Default to POST.
    verb = self._internal_inputs.get("deploy_signal_verb", {}).get("value", "POST")
    return requests.request(verb, url, json=payload)
    

class SoftwareConfig(Deployment):
  # 
  # def validate(self):
  #   # validate ourself
  # 
  @property
  def tool(self):
    return self._options["os_heat_agent_tool"]
    
  @property
  def serialize(self):
    return self._options["os_heat_agent_serialize"]
  
  def run(self):
    # run the config!
    tool = self.tool
    
    logger.debug("using tool %s" % tool)
    
    manifest = self._data["config"]
    if self.serialize:
      logger.debug("serializing config")
      logger.debug(manifest)
      # Write config out to disk and run it like that
      serialised = tempfile.NamedTemporaryFile()
      serialised.write(bytes(manifest, "utf-8"))
      serialised.flush() # Write it to disk so that things can work as expected
      manifest = serialised.name
      logger.debug(serialised.name)
    
    env = self.environment
    # Inject PATH into the subprocess call
    # TODO: What else should we inject here
    logger.debug(env)
    env["PATH"] = os.environ["PATH"]
    response = subprocess.run(
      [tool, manifest], 
      capture_output=True,
      env=env,
      # Treat output as pure text
      text=True
    )
    if self.serialize:
      # Deletes the file
      serialised.close()
    
    logger.debug(response.stdout)
    logger.debug(response.stderr)
    logger.debug(response.returncode)
    
    resp = {
      "deploy_stdout": response.stdout,
      "deploy_stderr": response.stderr,
      "deploy_status_code": str(response.returncode)
    }
    
    if response.returncode != 0:
      logger.debug("Reporting error")
      resp["os_heat_agent_is_error"] = True
    
    return resp

class SoftwareComponent(Deployment):
  def run(self):
    pass
    
    
class StructuredDeployment(Deployment):
  def run(self):
    pass