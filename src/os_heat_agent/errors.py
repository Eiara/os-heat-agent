from public import public

## Base errors

@public
class AgentError(Exception):
  pass
@public
class ValidationError(AgentError):
  pass

## Loading errors

@public
class MissingRuntimeError(FileNotFoundError):
  pass

@public
class ConfigurationError(AgentError):
  pass

## Runtime errors

@public
class MissingInputs(ValidationError):
  pass
@public
class MissingOutputs(ValidationError):
  pass
@public
class NoSuchRunner(ValidationError):
  pass
