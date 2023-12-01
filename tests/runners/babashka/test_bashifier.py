import pytest
from os_heat_agent.config import config
from os_heat_agent.runners import babashka

def test_bashify():
  output = """a="b"
b=1
declare -A d
d["q"]="r"
"""
  output = output.strip()
  data = {
    "a":"b",
    "b":1,
    "d":{
      "q":"r"
    }
  }
  assert "\n".join(babashka.bashify(data)) == output
  
def test_bashify_complex():
  output = """a="b"
b=1
c="b b b"
declare -A d
d["q"]="r"
foo=("bar" "baz" "bar baz")
"""
  output = output.strip()
  data = {
    "a":"b",
    "b":1,
    "c": "b b b",
    "d":{
      "q":"r"
    },
    "foo": ["bar","baz", "bar baz"]
  }
  assert "\n".join(babashka.bashify(data)) == output
  
def test_bashify_dict_exception():
  data = {
    "a": {
      "b": {
        
      }
    }
  }
  with pytest.raises(babashka.SerializerError):
    babashka.bashify(data)

def test_bashify_list_exception():
  data = {
    "a": {
      "b": []
    }
  }
  with pytest.raises(babashka.SerializerError):
    babashka.bashify(data)