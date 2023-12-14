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
@pytest.mark.parametrize("load_file", ["shell/test_serialize.json"], indirect=True)
@pytest.mark.integration
def test_serialized(init_shell_config, load_file, init_babashka):
  shell.init()
  for deployment in load_file["deployments"]:
    d = deployments.get_deployment(deployment)
    assert isinstance(d, deployments.StructuredConfig)
    d.validate()
    # Run the thing
    resp = d.run()
    assert resp.exit_code == 0
    p = Path("/tmp/test_file")
    assert p.exists()
    # Do cleanup
    p.unlink()


@pytest.mark.parametrize(
  "init_shell_config", 
  [
    {"bash":"/bin/bash"},
  ],
  indirect=True
)
@pytest.mark.parametrize("load_file", ["shell/test_non_serialize.json"], indirect=True)
@pytest.mark.integration
def test_bare(init_shell_config, load_file, init_babashka):
  shell.init()
  for deployment in load_file["deployments"]:
    d = deployments.get_deployment(deployment)
    assert isinstance(d, deployments.StructuredConfig)
    d.validate()
    # Run the thing
    resp = d.run()
    assert resp.exit_code == 0
    p = Path("/tmp/test_file")
    assert p.exists()
    # Do cleanup
    p.unlink()