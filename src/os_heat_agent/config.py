import configparser

# Create our config parser and set our defaults



config = configparser.ConfigParser()
# Add our default values
config.read_dict(
  {
    "agent": {
      "polling_interval": 60,
      "init_file": "/var/lib/heat-cfntools/cfn-init-data"
    },
    "cache": {
      "dir": "/var/lib/heat-cfntools/",
      "filename": "os-cfn-current"
    },
    "cloud": {
      "region": ""
    }
  }
)
# config.add_section("agent")
# config["agent"].setdefault("polling_interval", "60")
# config["agent"].setdefault("init_file", "/var/lib/heat-cfntools/cfn-init-data")
# 
# config["DEFAULT"] = {
#   "agent": {
#     "polling_interval": 60,
#     "init_file": "/var/lib/heat-cfntools/cfn-init-data"
#   },
#   "cache": {
#     "dir": "/var/lib/heat-cfntools/",
#     "filename": "os-cfn-current"
#   },
#   "cloud": {
#     "region": ""
#   }
# }
# 
# 
# config["agent"] = {
#   # Default to 60 seconds
#   "polling_interval": 60,
#   "init_file": "/var/lib/heat-cfntools/cfn-init-data"
# }
# config["cache"] = {
#   "dir": "/opt/os-heat-agent",
#   "filename": "os-cfn-current"
# }
# 
# config["cloud"] = {
#   "region": ""
# }