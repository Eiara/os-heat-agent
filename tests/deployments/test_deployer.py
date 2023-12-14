import pytest
import json
from pathlib import Path

from os_heat_agent import deployments, config, errors

@pytest.mark.parametrize("load_file", ["os-cfn-current-missing-config.json"], indirect=True)
def test_deployer_missing_config(load_file):
  with pytest.raises(KeyError) as excinfo:
    for deployment in load_file["deployments"]:
      # should fail here
      deployer = deployments.get_deployment(deployment)
      # should never reach here
      deployer.validate()
