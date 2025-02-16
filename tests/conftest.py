import pytest
import json
from os_heat_agent.config import config

@pytest.fixture(scope="function")
def config_file(request):
  return f"tests/fixtures/runtime/{request.param}"
  

@pytest.fixture(scope="function")
def load_metadata(request):
  with open(f"tests/fixtures/openstack/metadata/{request.param}") as fh:
    return json.loads(fh.read()) 

@pytest.fixture(scope="function")
def load_file(request):
  # Parameterized to make this not require writing multiple versions of the
  #   fixture load since that'd be ridiculous
  with open(f"tests/fixtures/openstack/structured_config/{request.param}") as fh:
    return json.loads(fh.read())

@pytest.fixture(scope="function")
def load_heat_fixture(request):
  # Parameterized to make this not require writing multiple versions of the
  #   fixture load since that'd be ridiculous
  with open(f"tests/fixtures/openstack/{request.param}") as fh:
    return json.loads(fh.read())

@pytest.fixture(scope="function")
def load_heat_stack_response(request):
  with open(f"tests/fixtures/openstack/StackComponent/{request.param}") as fh:
    return json.loads(fh.read())

@pytest.fixture
def init_config():
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
  })
  return config

@pytest.fixture
def init_config_babashka(set_config):
  config.read_dict({
    "tools.babashka": {
      "path": "tests/fixtures/scripts/babashka.sh",
      "variables": ""
    }})

@pytest.fixture
def init_babashka(init_config):
  config.read_dict({
    "tools.babashka": {
      "path": "/usr/bin/babashka",
      "variables": "/etc/babashka/variables"
    }})

@pytest.fixture
def init_shell_config(request, init_config):
  config.remove_section("tools.shell.runners")
  config.read_dict({
    "tools.shell.runners": request.param
  })
  return request.param
