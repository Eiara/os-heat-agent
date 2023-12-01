import click
# import configparser
import requests, json
import os, sys
import time

# from os_heat_agent.deployments import get_deployment
from os_heat_agent import deployments
from os_heat_agent.heat import get_config
from os_heat_agent.config import config

import logging
import structlog

log = structlog.getLogger(__name__)

log_levels = {
  "DEBUG": logging.DEBUG,
  "WARN": logging.WARN,
  "WARNING": logging.WARN,
  "INFO": logging.INFO,
  "ERROR": logging.ERROR,
  "FATAL": logging.FATAL,
  "CRITICAL": logging.CRITICAL
}

LOG_FORMAT='%(asctime)s:%(levelname)s:%(name)s  %(message)s'

# config = configparser.ConfigParser()
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

@click.command()
@click.option("-c", "--config_file", default="/etc/os_heat_agent.ini", show_default=True)
@click.option("-i", "--init_file", default="/var/lib/heat-cfntools/cfn-init-data", show_default=True)
@click.option("-r", "--fetch_region", is_flag=True, default=False)
@click.option("-l", "--log-level", default="WARN", show_default=True)
def main(config_file, init_file, fetch_region, log_level):
  # logging.basicConfig(
  #   format=LOG_FORMAT,
  #   level=log_levels[log_level.upper()]
  # )
  
  structlog.configure(
      wrapper_class=structlog.make_filtering_bound_logger(log_levels[log_level.upper()]),
  )
   
  log.info("starting os-heat-agent")
  if not os.path.exists(config_file):
    log.warn("missing config file %s", config_file)
    log.warn("using default configuration.")
  
  config.read(config_file)
  if config["cloud"]["region"] == "" and fetch_region:
    config["cloud"]["region"] = dynamically_fetch_region()
  
  log.info("polling interval: %s", config["agent"]["polling_interval"])
  log.info("cache directory: %s", config["cache"]["dir"])
  log.info("cache filename: %s", config["cache"]["filename"])
  
  if not os.path.exists(config["cache"]["dir"]):
    log.fatal("Missing cache directory: %s", config["cache"]["dir"])
    sys.exit(1)
  
  if not os.path.exists(init_file):
    log.fatal("Initial Heat configuration missing: %s", init_file)
    sys.exit(1)
  
  # Main program is loaded up.
  # Now, we want to initialize all our deployment handlers, disable any
  #   that aren't enabled, and log out which ones _are_ enabled.
  #   If none are enabled, we should error out.
  
  for name, module in deployments.TOOLS.items():
    try:
      module.init()
    except configparser.NoSectionError:
      # Module isn't configured, therefore should be disabled
      del(deployments.TOOLS, name)
      log.debug("Disabling tool %s", name)
    except FileNotFoundError as e:
      log.fatal(str(e))
      sys.exit(1)
  
  log.info("Enabled runners: %s", list(deployments.TOOLS.keys()))
  
  # Okay now we can load our default values
  while 1:
    cache_file = "%s/%s" % (
      config["cache"]["dir"],
      config["cache"]["filename"]
    )
    current_config = ""
    # Should we have guards around this? Hmm...
    if not os.path.exists(cache_file):
      log.info("Missing cache file %s", cache_file)
      log.info("Assuming first run")
      # Step 1, get our injected metadata from OS::Heat::SoftwareComponent
      # This is a hardcoded path, set by OpenStack directly.
      with open(init_file) as fh:
        current_config = json.loads(fh.read())
    else:
      with open(cache_file) as fh:
        # current config becomes the cached file
        current_config = json.loads(fh.read())
    
    # Fetch new config
    # Hmm
    # Where is the right place to do this?
    
    new_config = get_config(current_config["os-collect-config"]["cfn"], config["cloud"]["region"])
    
    if new_config["deployments"] != current_config["deployments"]:
      for deployment in new_config["deployments"]:
        dep = deployments.get_deployment(deployment)
        resp = dep.run()
        dep.signal(resp)
    
    # Save the cached file out
    with open(cache_file, "w") as fh:
      fh.write(json.dumps(new_config))
      
    log.debug("sleep %s" % int(config["agent"]["polling_interval"]))
    time.sleep(int(config["agent"]["polling_interval"]))


def dynamically_fetch_region():
  
  url = "http://169.254.169.254/openstack/latest/meta_data.json"
  metadata = requests.get(url).json()
  return metadata["availability_zone"][:-1]
  
