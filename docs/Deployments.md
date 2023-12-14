## Deployments reference

An example Deployment JSON blob looks like:

```json
{
  "config": {
    "configs": [
      {
        "actions": [
          "CREATE"
        ],
        "config": "configuration script, manifest, or other value",
        "tool": "name_of_tool"
      }
    ]
  },
  "creation_time": "2023-01-28T22:10:07Z",
  "group": "name_of_heat_resource",
  "id": "unique_id",
  "inputs": [
    {
      "description": "ID of the server being deployed to",
      "name": "deploy_server_id",
      "type": "String",
      "value": "server_id"
    },
    {
      "description": "Name of the current action being deployed",
      "name": "deploy_action",
      "type": "String",
      "value": "CREATE"
    },
    {
      "description": "ID of the stack this deployment belongs to",
      "name": "deploy_stack_id",
      "type": "String",
      "value": "deployment_stack_name/id"
    },
    {
      "description": "Name of this deployment resource in the stack",
      "name": "deploy_resource_name",
      "type": "String",
      "value": "name of the OS::Heat::SoftwareDeployment this OS::Heat::SoftwareConfig belongs to"
    },
    {
      "description": "How the server should signal to heat with the deployment output values.",
      "name": "deploy_signal_transport",
      "type": "String",
      "value": "CFN_SIGNAL"
    },
    {
      "description": "ID of signal to use for signaling output values",
      "name": "deploy_signal_id",
      "type": "String",
      "value": "https://signal_url"
    },
    {
      "description": "HTTP verb to use for signaling output values",
      "name": "deploy_signal_verb",
      "type": "String",
      "value": "POST"
    }
  ],
  "name": "deployment_name",
  "options": {
    "a": "map",
    "of": "options"
  },
  "outputs": []
}
```

