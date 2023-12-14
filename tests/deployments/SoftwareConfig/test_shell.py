import pytest
from os_heat_agent import deployments, config
from os_heat_agent.runners import shell
from pathlib import Path

@pytest.mark.parametrize(
  "init_shell_config", 
  [
    {"bash":"/bin/bash"},
  ],
  indirect=True
)
@pytest.mark.parametrize(
  "load_heat_fixture", 
  [
    "software_config/shell/nonserialized.json", 
    "software_config/shell/serialized.json",
    "software_config/shell/legacy_serialized.json",
    "software_config/shell/legacy_nonserialized.json",
    
  ], 
  indirect=True
)
@pytest.mark.integration
def test_shell(init_shell_config, load_heat_fixture):
  shell.init()
  for deployment in load_heat_fixture["deployments"]:
    d = deployments.get_deployment(deployment)
    assert isinstance(d, deployments.SoftwareConfig)
    d.validate()
    resp = d.run()
    assert resp.exit_code == 0
    p = Path("/tmp/test_file")
    assert p.exists()
    # Do cleanup
    p.unlink()