"""Test doing a "full" run of Babashka.
"""
import pytest
import os
import tempfile
from os_heat_agent.config import config
from os_heat_agent.runners import babashka
import configparser
import json
from pathlib import Path

variables_directory = "tests/fixtures/variables"
config_directory = "tests/fixtures/babashka/config"

@pytest.fixture
def temp_config():
  config.clear()
  with tempfile.TemporaryDirectory() as variables_dir:
    config.update(
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
          "path": "/usr/bin/babashka",
          "variables": variables_dir
        }
    })
    yield config
  
@pytest.fixture
def output_directory():
  with tempfile.TemporaryDirectory() as outputdir:
    yield outputdir

###
###
###

@pytest.mark.integration
def test_inputless_run(temp_config, tmpdir):
  data = {
    "function": "inputless.test.case",
    # Add in the 
    "directory": str(Path(config_directory).resolve())
  }
  env = {
    "OUTPUT_DIR": tmpdir,
    "TEST_VALUE": "test value"
  }
  resp = babashka.run(data, env)
  assert resp.exit_code == 0
  p = Path(f"{tmpdir}/test_file")
  assert p.exists()
  with open(p) as fh:
    assert f"{env['TEST_VALUE']}\n" == fh.read()

###
###
###

@pytest.mark.integration
def test_input_run(temp_config, tmpdir):
  data = {
    "function": "input.test.case",
    # Add in the 
    "directory": str(Path(config_directory).resolve()),
    "variable_file": "test_file"
  }
  input = {
    "TEST_VALUE": "another test value",
    "OUTPUT_DIR": tmpdir,
    "FILE_NAME": "test_file"
  }
  variable_file = Path(config["tools.babashka"]["variables"]).joinpath(input["FILE_NAME"])
  env = {
    "VARIABLE_FILE": variable_file
  }
  babashka.pre(data, input)
  # print(babashka.bashify(input))
  assert variable_file.exists()
  p = Path(f"{str(tmpdir)}/{input['FILE_NAME']}")
  
  with open(str(variable_file.resolve())) as fh:
    print(fh.read())
  
  resp = babashka.run(data, env)
  # print(resp.stdout)
  
  assert p.exists()
  with open(str(p.resolve())) as fh:
    # print(fh.read())
    fh.seek(0)
    assert f"{input['TEST_VALUE']}\n" == fh.read()