import pytest
from os_heat_agent.config import config
from os_heat_agent.runners import babashka
import configparser
import json
from pathlib import Path

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
      }
  })
  return config

@pytest.fixture
def babashka_bad_tool(set_config):
  set_config.read_dict({
    "tools.babashka": {
      "path": "/bad/path"
    }
  })
  return set_config
  
@pytest.fixture
def babashka_bad_variable_path(set_config):
  set_config.read_dict({
    "tools.babashka": {
      "path": "tests/fixtures/scripts/babashka.sh",
      "variables": "/a/bad/path"
    }
  })
@pytest.fixture
def babashka_variable_not_a_directory(set_config):
  set_config.read_dict({
    "tools.babashka": {
      "path": "tests/fixtures/scripts/babashka.sh",
      "variables": "tests/fixtures/scripts/babashka.sh"
    }
  })

@pytest.fixture
def babashka_good_config(set_config):
  set_config.read_dict({
    "tools.babashka": {
      "path": "tests/fixtures/scripts/babashka.sh",
      "variables": "tests/fixtures/variables"
    }
  })


# def test_init(set_config):
#   babashka.init_config()

def test_normalize_no_babashka_config(set_config):
  with pytest.raises(configparser.NoSectionError):
    babashka.normalize({})

def test_babashka_badtool( babashka_bad_tool ):
  
  assert config.has_section("tools.babashka")
  with pytest.raises(FileNotFoundError) as excinfo:
    babashka.normalize({})
  assert config.get("tools.babashka","path") in str(excinfo.value)

def test_babashka_bad_variables( babashka_bad_variable_path ):
  
  assert config.has_section("tools.babashka")
  with pytest.raises(FileNotFoundError) as excinfo:
    babashka.normalize({})
  assert f"{config.get('tools.babashka','variables')} doesn't exist" in str(excinfo.value)

def test_babashka_variable_not_a_directory( babashka_variable_not_a_directory ):
  
  with pytest.raises(FileNotFoundError) as excinfo:
    babashka.normalize({})
  assert f"{config.get('tools.babashka','variables')} is not a directory" in str(excinfo.value)
  
def test_babashka_missing_directory(babashka_good_config):
  with pytest.raises(FileNotFoundError) as excinfo:
    babashka.normalize({
      "directory": "tests/fixtures/variables/asdf"
    })
  assert "tests/fixtures/variables/asdf does not exist" in str(excinfo.value)

def test_babashka_not_a_directory(babashka_good_config):
  with pytest.raises(FileNotFoundError) as excinfo:
    babashka.normalize({
      "directory": "tests/fixtures/scripts/babashka.sh"
    })
  assert "tests/fixtures/scripts/babashka.sh is not a directory" in str(excinfo.value)

def test_babashka_good_directory(babashka_good_config):
  data = {
    "directory": "tests/fixtures/variables"
  }
  path = Path(data["directory"])
  with pytest.raises(babashka.RunnerError):
    babashka.normalize(data)
  assert data["directory"] == path.resolve()

def test_babashka_good_config(babashka_good_config):
  data = {
    "directory": "tests/fixtures/variables",
    "function": "test.function"
  }
  path = Path(data["directory"])
  babashka.normalize(data)
  assert data["directory"] == path.resolve()