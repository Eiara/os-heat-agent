from public import public

@public
class AgentError(Exception): pass

@public
class ValidationError(AgentError): pass
@public
class MissingInputs(ValidationError): pass
@public
class MissingOutputs(ValidationError): pass
@public
class NoSuchRunner(ValidationError): pass