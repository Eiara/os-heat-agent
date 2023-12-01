import pytest
import json
from pathlib import Path

from os_heat_agent import deployments, config, errors
  
@pytest.mark.parametrize("load_file", ["os-cfn-current-missing-outputs.json"], indirect=True)
def test_validation_missing_outputs(load_file):
  with pytest.raises(errors.MissingOutputs) as excinfo:
    for deployment in load_file["deployments"]:
      d = deployments.StructuredConfig(deployment)
      d.validate()

@pytest.mark.parametrize("load_file", ["os-cfn-current-bad-deployer.json"], indirect=True)
def test_validation_bad_deployer(load_file):
  with pytest.raises(errors.NoSuchRunner) as excinfo:
    for deployment in load_file["deployments"]:
      d = deployments.StructuredConfig(deployment)
      d.validate()

@pytest.mark.parametrize("load_file", ["os-cfn-current-good.json"], indirect=True)
def test_validation_success(load_file):
  for deployment in load_file["deployments"]:
    d = deployments.StructuredConfig(deployment)
    d.validate()