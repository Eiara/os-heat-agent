## os-heat-agent

OS Heat Agent is a small agent program intended to interface with the OS::Heat::SoftwareComponent, OS::Heat::SoftwareConfig, OS::Heat::SoftwareDeployment, OS::Heat::SoftwareDeploymentGroup,  OS::Heat::StructuredConfig, OS::Heat::StructuredDeployment, and OS::Heat::StructuredDeploymentGroup resources in OpenStack Heat.

This agent provides different interfaces for SoftwareConfig, SoftwareComponent, and StructuredConfig resources, as these have different configuration inputs.

This agent will enforce the existence of specific inputs and outputs.

Example configurations, including generic Terraform setup, can be found in the [examples/]() directory.

## Usage

### SoftwareConfig

A OS::Heat::SoftwareConfig resource is expected to provide a script or command arguments to be passed to the runner.

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

### SoftwareComponent

TODO: Not yet implemented.

### StructuredConfig

TODO: Not yet implemented.