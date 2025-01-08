from . import Output, RunnerError
import subprocess
import shlex
from pathlib import Path
from public import public, private
# Load the configuration
#   This assumes that configuration has, in fact, been loaded
#   Which is not necessarily true ...
#   Hmmm...
#   Hrm.
#   Ideally the Runner object would, like ... take a configuration value as
#   its init value? so that it can be correctly configured? And then the test
#   cases can pass in its own configuration value?
from os_heat_agent.config import config
import structlog

logger = structlog.getLogger(__name__)

VARIABLES_PATH="/etc/babashka/variables"

SUPPORTED_CONFIGS = ["StructuredConfig","SoftwareComponent"]

class SerializerError(RunnerError): 
  pass

@public
def init() -> None:
  """Initialize this runner.
  
  Checks values in configuration to ensure they're valid and set up correctly,
    so that the tool can raise an exception and error out before starting up
    and before causing issues with the runtime environment.
  
  Raises:
    FileNotFoundError: If the variables path is not found.
    FileNotFoundError: If the Babashka executable is not found.
  """
  
  babashka = Path(config.get("tools.babashka","path"))
  
  if not babashka.exists() or babashka.is_dir():
    # Babashka isn't installed, which we need to except on
    logger.error("Babashka not installed or incorrectly configured: %s", babashka.resolve())
    raise FileNotFoundError("Babashka not installed or incorrectly configured: %s", babashka.resolve())
  
  # Validate the variables path stuff.
  variable_path = Path(config.get("tools.babashka", "variables"))
  
  if not variable_path.exists():
    logger.error("Babashka variables path %s doesn't exist", variable_path.resolve())
    raise FileNotFoundError(f"Babashka variables path {variable_path.resolve()} doesn't exist")
  
  if not variable_path.is_dir():
    logger.error("Babashka variables path %s is not a directory", variable_path.resolve())
    raise FileNotFoundError(f"Babashka variables path {variable_path.resolve()} is not a directory")

@public
def init_config() -> None:
  """Initialize configuration for this runner.
  
  Sets up initial configuration defaults for this runner. Uses the namespace
    `tools.babashka`.
  """
  
  config.read_dict({
    "tools.babashka": {
      "path": "/usr/bin/babashka",
      "variables_path": VARIABLES_PATH
    }
  })

@public
def supports(runner: str) -> bool:
  return runner in SUPPORTED_CONFIGS

@private
def normalize(data: dict) -> bool:
  """Normalizes and validates the incoming OpenStack data
  
  This function will verify that Babashka is installed in an accessible
  location on the system, and that the directory that will be been passed to
  Babashka exists.
  
  Args:
    data (dict): Incoming data from OpenStack Heat.This function will modify
      the original dict in-place.
  
  Returns:
    bool: If the input data successfully validated. Only returns "True", as
      invalid inputs are expected to raise exceptions.
    
  Raises:
    FileNotFoundError: If either the Babashka executable or the passed Babashka
      directory do not exist.
    RunnerError: If the Babashka `function` has not been defined.
  """
  
  if not isinstance(data, dict):
    raise NotImplementedError("Babashka runner requires StructuredConfig or SoftwareComponent")
  
  # Test if Babashka is actually installed where we think it is
  babashka = Path(config.get("tools.babashka","path"))
  
  if not babashka.exists() or babashka.is_dir():
    # Babashka isn't installed, which we need to except on
    logger.error("Babashka not installed or incorrectly configured: %s", babashka.resolve())
    raise FileNotFoundError("Babashka not installed or incorrectly configured: %s", babashka.resolve())
  data["runner"] = babashka
  
  # Validate the variables path stuff.
  variable_path = Path(config.get("tools.babashka", "variables"))
  
  if not variable_path.exists():
    logger.error("Babashka variables path %s doesn't exist", variable_path.resolve())
    raise FileNotFoundError(f"Babashka variables path {variable_path.resolve()} doesn't exist")
  
  if not variable_path.is_dir():
    logger.error("Babashka variables path %s is not a directory", variable_path.resolve())
    raise FileNotFoundError(f"Babashka variables path {variable_path.resolve()} is not a directory")
  
  if data.get("directory", ""):
    directory = Path(data.get("directory", ""))
    # we should check if the directory exists, right?
    if not directory.exists():
      logger.error("Babashka directory %s does not exist", directory.resolve())
      raise FileNotFoundError(f"Babashka directory {directory.resolve()} does not exist", )
    if not directory.is_dir():
      logger.error("Babashka directory %s is not a directory", directory.resolve())
      raise FileNotFoundError(f"Babashka directory {directory.resolve()} is not a directory")
      
    data["directory"] = directory.resolve()
    
    if not data.get("function", None):
      # There is currently no way to validate if Babashka has given function
      #   name exported.
      logger.error("Babashka function is not defined.")
      raise RunnerError("Babashka function is not defined.")
  return True

@private
def command(data: dict) -> list:
  """Generate the run command list for the Babashka runner.

  Arguments:
    data (dict) Incoming data from OpenStack Heat.
  
  Returns:
    list (str): A command list, suitable for use with subprocess.run
  """
  
  
  command = [
    data["runner"].resolve()
  ]
  if data.get("directory", ""):
    command.extend(["-d", data["directory"].resolve()])
  command.append(data["function"])
  return command
  

@public
def run(config: dict, environment: dict=None) -> Output:
  """Runs Babashka with the input data.
  
  Babashka is run with the input function, and optional directory.
  
  Args:
    data (dict): Full input data from OpenStack
    Dict topology is expected to be:
      `function` (str)
        The function that will be run by Babashka
      `directory` (str, optional):
        What directory to include in the Babashka run.
    environment (dict, optional): System environment variables that will be
      passed to ``subprocess.run``.
  
  Returns:
    :obj:`Output`: An Output object representing the results of the command run.
  
  Raises:
    FileNotFoundError: Babashka runtime or the provided directory are not found.
    RunnerError: Babashka function not defined.
  """
  
  normalize(config)
  
  if not environment:
    environment = {}
  
  # Generate the command list for subprocess
  cmd = command(config)
  
  # Run subprocess.
  response = subprocess.run(
    cmd,
    capture_output=True,
    env=environment,
    # Treat output as pure text
    text=True
  )
  # Add the subprocess outputs to the Output object.
  # Wait why does it do this and not just return the subprocess.run response directly?
  return Output(
    stdout=response.stdout,
    stderr=response.stderr,
    exit_code=response.returncode
  )

@public
def pre(data: dict, input: dict) -> bool:
  """Write out any Babashka variables to disk at the specified location.
  
  The Babashka integration will have defined 0..n values that are expected to
    be written out as on-disk values as part of the setting variables system.
  
  Args:
    data (dict): Incoming data from OpenStack Heat
  
  Returns:
    None: No return value
  
  Raises:
    RuntimeError: Trying to pass an invalid filename to the serializer.
    RuntimeError: Passing a variable filename but not providing any input 
      values.
    SerializerError: Inability to serialize some input values to disk.
    OSError: Inability to open the file for writing.
  """
  p = data.get("variable_file", None)
  if not p:
    # we're not serializing anything, so just return
    return False
    
  variable_path = Path(config.get("tools.babashka", "variables"))
  
  # Forcibly remove anything that's not the filename from the incoming
  #   variable file
  # This is done to ensure that rogue data can't be used to write random stuff
  #   to the filesystem.
  path = variable_path.joinpath(Path(p).name)
  
  if path.is_dir():
    # Throw an error, since this isn't going to work properly
    logger.error("Path %s is a directory, not a file", path.resolve())
    raise RuntimeError(f"Babashka serializer: path {path.resolve()} is a directory")
  
  # Clobber the file
  # This might actually throw an exception if we can't write to the folder
  
  if not input:
    # No input? Curious
    logger.error("Variable file declared but no input values provided.")
    raise RuntimeError("Variable file declared but no input values provided.")
  
  # Assumes this will raise an OSError if we can't write to the location.
  # Which seems like a reasonable assumption.
  with open(path.resolve(), "w", encoding="utf-8") as fn:
    fn.write("\n".join(bashify(input)))
  
  # And done.
  return True
  
@public
def post(data: dict) -> None:
  """Post-process step. Babashka runner does not need post-processing.
  """
  pass
  
  
@private
def bashify(config: dict) -> list:
  bash_vars = []
  
  for key, value in config.items():
    if isinstance(value, dict):
      # Use the built-in Bash associative arrays
      
      bash_vars.append(f'declare -A {key}')
      for k, v in value.items():
        # Raise an error because we can't serialize nested structures
        if isinstance(v, dict) or isinstance(v, list):
          raise SerializerError("Nested data structures cannot be serialized.")
        # Use shlex.quote to escape special characters in keys and values
        escaped_key = subprocess.check_output(['bash', '-c', f'printf %s {shlex.quote(k)}']).decode('utf-8').strip()
        escaped_value = subprocess.check_output(['bash', '-c', f'printf %s {shlex.quote(v)}']).decode('utf-8').strip()
        bash_vars.append(f'{key}["{escaped_key}"]="{escaped_value}"')
    elif isinstance(value, list):
        # Use Bash array syntax for lists
        escaped_values = []
        for v in value:
          escaped = subprocess.check_output(['bash', '-c', f'printf %s {shlex.quote(v)}']).decode('utf-8').strip()
          escaped_values.append(
            f'"{escaped}"'
          )
        array_elements = ' '.join(escaped_values)
        bash_vars.append(f'{key}=({array_elements})')
    elif isinstance(value, str):
        # Use shlex.quote to escape special characters
        escaped_value = subprocess.check_output(['bash', '-c', f'printf %s {shlex.quote(value)}']).decode('utf-8').strip()
        bash_vars.append(f'{key}="{escaped_value}"')
    else:
        bash_vars.append(f'{key}={value}')
  return bash_vars