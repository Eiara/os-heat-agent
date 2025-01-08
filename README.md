## os-heat-agent

OS Heat Agent is a small agent program intended to interface with the `OS::Heat::SoftwareComponent`, `OS::Heat::SoftwareConfig`, `OS::Heat::SoftwareDeployment`, `OS::Heat::SoftwareDeploymentGroup`,  `OS::Heat::StructuredConfig`, `OS::Heat::StructuredDeployment`, and `OS::Heat::StructuredDeploymentGroup` resources in OpenStack Heat.

This agent provides different interfaces for SoftwareConfig, SoftwareComponent, and StructuredConfig resources, as these have different configuration inputs.

This agent will enforce the existence of specific inputs and outputs.

Example configurations, including generic Terraform setup, can be found in the [examples/]() directory.

## Usage

### Configuration

This software requires the existence of `/etc/os_heat_agent.ini` for configuration. For example,

```ini
[agent]
# How frequently to poll OpenStack for changes, in seconds
polling_interval = 60
# Where to look for the initial OpenStack configuration
init_file = /var/lib/heat-cfn-tools/cfn-init-data

[cache]
# Where to write our most recent cached file
dir = /var/lib/heat-cfntools/
# What to name the file
filename = os-cfn-current

[cloud]
region = "cloud_region"

[tools.babashka]
path = /usr/bin/babashka
variables = /etc/babashka/variables

[tools.shell.runners]
bash = /bin/bash
python = /usr/bin/python
# Other runners here
```

### SoftwareConfig

A OS::Heat::SoftwareConfig resource is expected to provide a script or command arguments to be passed to a Runner.

#### Runner definitions

Per the OpenStack Heat documentation, the `group:` value is used to determine the runner to use, such as:

```yaml
config:
  type: "OS::Heat::SoftwareConfig"
  properties:
    group: Web::Shell::Bash
    config: |
      #!/bin/bash
      code=0
      while [ $code -ne 200 ]; do
        sleep 10
        code=$(/usr/bin/curl -i -o /dev/null --silent -w "%{http_code}" $url)
      done
    options:
      # Required
      os_heat_agent_tool: /usr/bin/bash
      os_heat_agent_serialize: true
    inputs:
      - name: envar_url
        type: String
        description: "URL to ping for health check, to verify that the node is online."
        
    outputs:
      # Required
      - name: "os_heat_agent_is_error"
        description: "Did the job fail?"
        type: Boolean
        error_output: true
```

In the above, `Web` is the group name (currently unused), `Shell` is the runner, and `Bash` is the sub-runner that will be used.

In the event of an undeclared `group` value, the trailing value in `os_heat_agent_tool`, in the above case `bash`, will be used instead.


#### Options

- `os_heat_agent_tool`: **required**. Tells the Agent what tool to use to run the config.
- `os_heat_agent_serialize`: **optional**. Tells the Agent if the config should be written to disk before being executed by the tool.

#### Inputs

- `envar_`: Any input prefixed as `envar_` will be treated by an environment variable by the Agent, and passed down to the `subprocess.run` call.

#### Outputs

- `os_heat_agent_is_error`: **required**. The agent will signal on this output if there was an error, which will be used by Heat to trigger a rollback

#### Example configuration
```yaml
resources:
  config:
    type: "OS::Heat::SoftwareConfig"
    properties:
      config: |
        #!/bin/bash
        code=0
        while [ $code -ne 200 ]; do
          sleep 10
          code=$(/usr/bin/curl -i -o /dev/null --silent -w "%{http_code}" $url)
        done
      options:
        # Required
        os_heat_agent_tool: /bin/bash
        os_heat_agent_serialize: true
      inputs:
        - name: envar_some_envar
          type: String
          description: "Environment variables that should be passed to the tool should be prefixed with envar_. More than one can be added."
      outputs:
        # Required
        - name: "os_heat_agent_is_error"
          description: "Did the job fail?"
          type: Boolean
          error_output: true
```

### StructuredConfig

A StructuredConfig is an OpenStack Heat configuration that uses a dictionary configuration instead of a string. Being a dictionary, it permits more nuance and control to be passed to the underlying runner.

Currently supported runners:

- Shell
- Babashka

#### Shell

The Shell runner operates largely the same as the SoftwareConfig variant, with minor changes.

An example configuration would be:

##### Example

```yaml
resources:
config:
  type: "OS::Heat::StructuredConfig"
  group: "Web::Shell::Bash"
  properties:
    config:
      command: touch /tmp/test_file
      # Optional, defaults to False
      serialize: true
    inputs:
      - name: envar_some_variable
        type: String
        description: "An environment variable that will be passed through to the command run."
    outputs:
      # Required
      - name: "os_heat_agent_is_error"
        description: "Did the job fail?"
        type: Boolean
        error_output: true
```

#### Babashka

The Babashka runner is designed to serialize a variables file to a pre-determined path and run a pre-defined Babashka function. The variables file is populated from values in the input variables, allowing OpenStack to trigger an `update` instead of a `destroy`/`create` cycle.

An example configuration is:

```yaml
resources:
config:
  type: "OS::Heat::StructuredConfig"
  group: "Web::Babashka"
  properties:
    config:
      function: heat.function
      variable_file: heat_variables.sh
      # Optional
      directory: /path/to/babashka
    options:
      # Required
    inputs:
      - name: some_variable
        type: String
        description: "a variable that will get serialized to /etc/babashka/variables/heat_variables.sh"
    outputs:
      # Required
      - name: "os_heat_agent_is_error"
        description: "Did the job fail?"
        type: Boolean
        error_output: true
```

In the above example, Babashka will be run as `babashka -d /path/to/babashka heat.function`. The user of Babashka is expected to load `/etc/babashka/variables/heat_variables.sh` in the function being called.

### StructuredConfig

TODO: Not yet implemented.