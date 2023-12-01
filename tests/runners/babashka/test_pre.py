import pytest
import os
from os_heat_agent.config import config
from os_heat_agent.runners import babashka
import configparser
import json
from pathlib import Path

variables_directory = "tests/fixtures/variables"
variables_filename = "test.sh"

@pytest.fixture
def set_config():
  config.clear()
  config.read_dict(
    {
      "agent": {
        "polling_interval": 60,
        "init_file": "tests/data"
      },
      "cache": {
        "dir": "/var/lib/heat-cfntools/",
        "filename": "os-cfn-current"
      },
      "cloud": {
        "region": ""
      },
      "tools.babashka": {
        "path": "tests/fixtures/scripts/babashka.sh",
        "variables": variables_directory
      }
  })
  return config
  
@pytest.fixture
def cleanup_files():
  # Cleans up after the test runs that are expected to create files in the
  # `variables` directory
  
  yield
  p = Path(variables_directory).joinpath(Path(variables_filename)).resolve()
  # raise RuntimeError(str(p.resolve()))
  os.unlink(p)

def test_pre_no_file(set_config):
  assert False == babashka.pre(
      data={},
      input={}
    )
def test_pre_bad_input(set_config):
  with pytest.raises(RuntimeError) as excinfo:
    babashka.pre(
      data={
        "variable_file": "variable.sh"
      },
      input={}
    )
  assert "Variable file declared but no input values provided" in str(excinfo.value)

def test_pre_bad_filename(set_config):
  p = Path(config.get("tools.babashka", "variables"))
  p = p.joinpath("empty")
  with pytest.raises(RuntimeError) as excinfo:
    babashka.pre(
      data={
        "variable_file": "empty"
      },
      input={}
    )
  assert f"{p.resolve()} is a directory" in str(excinfo.value)

def test_pre_good_file(set_config, cleanup_files):
  data={
    "variable_file": variables_filename
  }
  input={
    "foo": "bar"
  }
  assert babashka.pre(data, input)
  p = Path(config.get("tools.babashka", "variables"))
  p = p.joinpath(Path("test.sh"))
  assert p.exists()
  # read the file and assert the contents are what we expect
  with open(p.resolve()) as fh:
    contents = fh.read() # slurp
  assert contents == "\n".join(babashka.bashify(input))