import pytest
from pathlib import Path
from os_heat_agent.runners import shell
from os_heat_agent.runners import RunnerError, Output
from os_heat_agent.config import config

@pytest.mark.parametrize(
  "init_shell_config", 
  [
    {"bash":"/usr/bin/bash"},
  ],
  indirect=True
)
def test_normalize_missing_tool(init_shell_config):
  data = {
    "command": "/bin/ls -al /etc",
  }
  shell.init()
  with pytest.raises(shell.MissingRunner) as excinfo:
    output = shell.normalize(data)
    assert "No defined group." in str(excinfo.value)

###
###
###

@pytest.mark.parametrize(
  "init_shell_config", 
  [
    {"bash":"/usr/bin/bash"},
  ],
  indirect=True
)
def test_normalize_bad_runner(init_shell_config):
  data = {
    "command": "/bin/ls -al /etc",
    "group" : "asdf"
  }
  shell.init()
  with pytest.raises(shell.MissingRunner) as excinfo:
    output = shell.normalize(data)
    assert "is not a list." in str(excinfo.value)

@pytest.mark.parametrize(
  "init_shell_config", 
  [
    {"bash":"/usr/bin/bash"},
  ],
  indirect=True
)
def test_normalize_no_enabled_runner(init_shell_config):
  data = {
    "command": "/bin/ls -al /etc",
    "group" : ["python"]
  }
  shell.init()
  with pytest.raises(shell.MissingRunner) as excinfo:
    output = shell.normalize(data)
    assert f"{data['group'][0]} not enabled." in str(excinfo.value)

###
###
###

@pytest.mark.parametrize(
  "init_shell_config", 
  [
    {"bash":"/usr/bin/bash"},
  ],
  indirect=True
)
def test_normalize_no_command(init_shell_config):
  data = {
    "group" : ["bash"],
  }
  shell.init()
  with pytest.raises(RunnerError) as excinfo:
    output = shell.normalize(data)
    assert f"Command not defined." in str(excinfo.value)
  
###
###
###

@pytest.mark.parametrize(
  "init_shell_config", 
  [
    {"bash":"/usr/bin/bash"},
  ],
  indirect=True
)
def test_pre_serializes(init_shell_config):
  data = {
    "group" : ["bash"],
    "command": "/bin/ls -al /etc",
    "serialize": True
  }
  # initialize things correctly.
  shell.init()
  
  shell.pre(data, {})
  assert data["filehandle"]
  data["filehandle"].seek(0)
  assert data["filehandle"].read().decode("utf-8") == data["command"]
  data["filehandle"].close()

###
###
###

@pytest.mark.parametrize(
  "init_shell_config", 
  [
    {"bash":"/usr/bin/bash"},
  ],
  indirect=True
)
def test_post_closes(init_shell_config):
  data = {
    "group" : ["bash"],
    "command": "/bin/ls -al /etc",
    "serialize": True
  }
  # initialize things correctly.
  shell.init()
  
  shell.pre(data, {})
  filename = data["filehandle"].name
  shell.post(data)
  
  with pytest.raises(KeyError):
    data["filehandle"]
  
  assert Path(filename).exists() is False

###
###
###

@pytest.mark.parametrize(
  "init_shell_config", 
  [
    {"bash":"/usr/bin/bash"},
  ],
  indirect=True
)
def test_command_serialized(init_shell_config):
  data = {
    "group" : ["bash"],
    "command": "/bin/ls -al /etc",
    "serialize": True
  }

###
###
###

@pytest.mark.parametrize(
  "init_shell_config", 
  [
    {"bash":"/usr/bin/bash"},
  ],
  indirect=True
)
def test_command_bare(init_shell_config):
  data = {
    "group" : ["bash"],
    "command": "/bin/ls -al /etc",
  }
  shell.init()
  shell.normalize(data)
  shell.pre(data, {})
  cmd = shell.command(data)
  expected = [
    "/usr/bin/bash",
    "-c",
    "/bin/ls -al /etc",
    # "-al",
    # "/etc"
  ]
  assert cmd == expected

###
###
###

@pytest.mark.parametrize(
  "init_shell_config", 
  [
    {"bash":"/usr/bin/bash"},
  ],
  indirect=True
)
def test_run_bare(init_shell_config):
  data = {
    "group" : ["bash"],
    "command": "ls -al",
  }
  shell.init()
  shell.normalize(data)
  shell.pre(data, {})
  print (shell.command(data))
  resp = shell.run(data)
  assert resp.exit_code == 0

###
###
###

@pytest.mark.parametrize(
  "init_shell_config", 
  [
    {"bash":"/usr/bin/bash"},
  ],
  indirect=True
)
def test_run_serialized(init_shell_config):
  data = {
    "group" : ["bash"],
    "command": "ls -al",
    "serialize": True
  }
  shell.init()
  shell.normalize(data)
  shell.pre(data, {})
  print (shell.command(data))
  resp = shell.run(data)
  assert resp.exit_code == 0


###
###
###

@pytest.mark.parametrize(
  "init_shell_config", 
  [
    {"bash":"/usr/bin/bash"},
  ],
  indirect=True
)
def test_run_bare_exit(init_shell_config):
  data = {
    "group" : ["bash"],
    "command": "exit 1;",
    "serialize": True
  }
  shell.init()
  shell.normalize(data)
  shell.pre(data, {})
  # print (shell.command(data))
  resp = shell.run(data)
  assert resp.exit_code == 1