import pytest
from pathlib import Path
from os_heat_agent.runners import shell
from os_heat_agent.config import config

def test_init_fails_no_configuration(init_config):
  with pytest.raises(KeyError) as exc:
    shell.init()

@pytest.mark.parametrize(
  "init_shell_config", 
  [
    {"bash":"/a/bad/path"},
  ],
  indirect=True
)
def test_init_fails_no_runners(init_shell_config):
  with pytest.raises(shell.NoEnabledRunners) as exc:
    shell.init()

@pytest.mark.parametrize(
  "init_shell_config", 
  [
    {"bash":"/bin/bash"},
    {"bash":"/bin/bash", "python": "/usr/bin/python3"},
  ],
  indirect=True
)
def test_init_fails_no_runners(init_shell_config):
  shell.init()
  for key, value in init_shell_config.items():
    assert shell.enabled_runners[key] == Path(value)