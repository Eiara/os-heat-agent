import pytest
import requests_mock
from click.testing import CliRunner
from os_heat_agent import main, deployments

@pytest.mark.parametrize("load_metadata",
  ["bad_meta_data.json"],
  indirect=True
)
def test_main_no_region_exits(load_metadata):
  with requests_mock.Mocker() as mock:
    mock.get("http://169.254.169.254/openstack/latest/meta_data.json", json=load_metadata)
    runner = CliRunner()
    result = runner.invoke(main, ["--fetch_region"])
    assert result.exit_code == 10

##
##
##

def test_main_no_cache_directory_exits():
  # with requests_mock.Mocker() as mock:
    # mock.get("http://169.254.169.254/openstack/latest/meta_data.json", json=load_metadata)
  runner = CliRunner()
  result = runner.invoke(main, [])
  assert result.exit_code == 11
  
  
##
##
##

@pytest.mark.parametrize("config_file",
  ["missing_cache.ini"],
  indirect=True
)
def test_main_tool_missing_init_file(config_file):
  runner = CliRunner()
  result = runner.invoke(main, [
    "-c", config_file
  ])
  assert result.exit_code == 12
  
##
##
##

# def test_deployment_tools():
#   