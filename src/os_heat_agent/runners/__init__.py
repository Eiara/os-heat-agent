from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from public import public
from ..errors import AgentError

@public
class RunnerError(AgentError): 
  pass

# some kind of registration system here? something to load in files and map
# them against the incoming "what is a tool even" system.
# So Babashka registers itself as "babashka" and then the runner system can
# attempt to import the file and work with it like that.
# Hmm, I've done this pattern before, I should look at how I did it last time.

@public
@dataclass
class Output:
  """
  Output datatype that is returned by a Runner.
  """
  
  stdout: str
  stderr: str
  exit_code: int

class Runner(metaclass=ABCMeta):
  """
  Runner interface class.
  Runners should have a "run", obvs.
  A Runner ought to have, like, configuration input, so it ought to define that somehow
  """
  
  @abstractmethod
  def run(self) -> Output:
    pass