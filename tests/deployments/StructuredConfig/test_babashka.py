import pytest
from os_heat_agent import deployments, config
from pathlib import Path

@pytest.mark.parametrize("load_file", ["babashka/test_babashka_deployer.json"], indirect=True)
@pytest.mark.integration
def test_babashka_deployer(load_file, init_babashka):
  for deployment in load_file["deployments"]:
    deployment["config"]["directory"] = str(Path("tests/fixtures/babashka/config").resolve())
    d = deployments.get_deployment(deployment)
    assert isinstance(d, deployments.StructuredConfig)
    d.validate()
    # Run the thing
    resp = d.run()
    assert resp.exit_code == 0