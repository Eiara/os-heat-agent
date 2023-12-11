"""This runner provides a system shell integration.

This runner exports the ability to run scripts provided via OpenStack Heat
  on a system using the configured shell.
  
Scripts will be serialized to a temporary location on disk and will be run
  from there.

Config format is expected to be
[tools.shell.runners]
bash="/bin/bash" 
python="/usr/bin/python"
"""
import subprocess
import structlog
import os
import copy
from pathlib import Path
import shlex
import tempfile
from public import public, private
from os_heat_agent.config import config
from . import RunnerError, Output

logger = structlog.getLogger(__name__)

SUPPORTED_CONFIGS = ["SoftwareConfig","StructuredConfig","SoftwareComponent"]

enabled_runners = {}

known_modifiers = {
  "bash": "-c",
  "python": "-e"
}

class NoEnabledRunners(RunnerError): pass
class MissingRunner(RunnerError): pass

@public
def supports(runner: str) -> bool:
  return runner in SUPPORTED_CONFIGS

@public
def init() -> None:
  """Initialize the Shell runner.
  
  Checks values in configuration to ensure that this runner can be enabled and
    is going to work more or less as expected.
  
  Raises:
    NoEnabledRunners: If no runners passed the enable check
    KeyError: If tool.shell.runners is not populated at all
  """
  
  # Clear the existing runners
  global enabled_runners
  enabled_runners = {}
  
  for name, path in config["tools.shell.runners"].items():
    runner = Path(path).resolve()
    if not runner.exists():
      # If the runner doesn't exist, we should error
      logger.error("Command %s not found", runner.resolve())
      continue
    if not runner.is_file():
      # If the runner isn't a file, IE it's a directory, we should error
      logger.error("Command %s is not a file", runner.resolve())
      continue
    
    if not os.access(runner.resolve(), os.X_OK):
      logger.error("Command %s is not executable", runner.resolve())
      continue
    
    enabled_runners[name] = runner
  
  if not enabled_runners:
    raise NoEnabledRunners("No enabled shell runners.")

@public
def normalize(data: dict, options: dict = {}) -> dict:
  """Validate and normalize the data from OpenStack.
  
  Args:
    data (dict): Incoming data from OpenStack.
      - command (str): The command to run or the runner to use.
      - serialize (bool): if the payload should be serialized to disk
      - group (list | tuple): Values from after the Shell:: deployer value. Expects a
          list as other deployers may have more sub-context going forward.
  Raises:
    MissingRunner: If the runner is not defined in the data dict
    MissingRunner: If the group input is not a list or tuple
    RunnerError: if the command has not been defined.
  """
  
  global enabled_runners
  try:
    if not isinstance(data["group"], list):
      raise MissingRunner(f"Runner {data['group']} is not a list.")
  except KeyError:
    raise MissingRunner("No defined group.")
    
  if data["group"][0] not in enabled_runners:
    raise MissingRunner(f"Runner {data['group'][0]} not enabled.")
  
  if not data.get("command", None):
    raise RunnerError("Command not defined.")
  
  data["runner"] = enabled_runners[data["group"][0]]
  return data
  
@public
def pre(data: dict, input: dict) -> bool:
  """Pre-run commands for the Shell runner.
  
  Serializes the payload, if the payload needs to be serialized.
  
  Args:
    data (dict): The data to be run.
    input (dict): Inputs provided from OpenStack. Unused.
  """
  
  if data.get("serialize", False):
    # Serialize out to a temporary file, and hold the filehandle until we 
    #   can close it later.
    logger.debug("Serializing shell command.")
    # Write config out to disk and run it like that
    serialized = tempfile.NamedTemporaryFile()
    serialized.write(bytes(data["command"], "utf-8"))
    serialized.flush() # Force the command to be written to disk.
    data["filehandle"] = serialized
    logger.debug("Serialized path: %s:", serialized.name)
    return True
  return False

@public
def post(data: dict) -> bool:
  """Post-run commands for the Shell runner.
  
  If the command was serialized to disk, we need to close the filehandle and
    delete it, to not leak memory.
  """
  
  if data.get("filehandle", None):
    logger.debug("Closing filehandle %s", data["filehandle"].name)
    data["filehandle"].close()
    del data["filehandle"]
    return True
  return False
  

@private
def command(data: dict) -> list:
  """Generate the subprocess run command.
  
  Generates a list appropriate to be used with subprocess.run. Requires that
    `normalize` and `pre` have already been run.
  """
  cmd = [
    str(data["runner"].resolve())
  ]
  if data.get("serialize", None):
    # simple command, then.
    cmd.append(data["filehandle"].name)
  else:
    cmd.append(known_modifiers[data["group"][0]])
    cmd.append(subprocess.check_output(['bash', '-c', f'printf %s {shlex.quote(data["command"])}']).decode('utf-8'))
    # cmd.extend(data["command"].split(" "))
  return cmd

@public
def run(data: dict, environment: dict = None) -> Output:
  """Run the selected runner.
  
  Args:
    data (dict): Incoming configuration data from OpenStack. This is expected
      to be in the format of:
      command (str): The command to run
      runner (Path): Path object to the runner to run the command
  """
  
  if not environment:
    environment = {}
    
  data = normalize(data)
  
  cmd = command(data)
  env = copy.copy(environment)
  env["PATH"] = os.environ["PATH"]
  response = subprocess.run(
    cmd, 
    capture_output=True,
    env=env,
    # Treat output as pure text
    text=True,
  )
  
  logger.debug(response.stdout)
  logger.debug(response.stderr)
  logger.debug(response.returncode)
  
  return Output(
    stdout=response.stdout,
    stderr=response.stderr,
    exit_code=response.returncode
  )