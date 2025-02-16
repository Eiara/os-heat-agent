import click
# import configparser
import requests
import json
import os
import sys
import time
import copy

# from os_heat_agent.deployments import get_deployment
from os_heat_agent import deployments
from os_heat_agent.heat import get_config
from os_heat_agent.config import config
from os_heat_agent.errors import ConfigurationError, MissingRuntimeError
import configparser

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
  
  structlog.configure(
      wrapper_class=structlog.make_filtering_bound_logger(log_levels[log_level.upper()]),
  )
   
  log.info("starting os-heat-agent")
  if not os.path.exists(config_file):
    log.warn("missing config file %s", config_file)
    log.warn("using default configuration.")
  
  config.read(config_file)
  if config["cloud"]["region"] == "" and fetch_region:
    try:
      config["cloud"]["region"] = dynamically_fetch_region()
    except KeyError as e:
      # For whatever reason, the region fetch failed, because the metadata
      #   fetch failed. 
      # That's not great, obviously.
      log.fatal(f"No region defined and unable to fetch region: {e}")
      sys.exit(10)
  
  log.info("polling interval: %s", config["agent"]["polling_interval"])
  log.info("cache directory: %s", config["cache"]["dir"])
  log.info("cache filename: %s", config["cache"]["filename"])
  
  if not os.path.exists(config["cache"]["dir"]):
    log.fatal("Missing cache directory: %s", config["cache"]["dir"])
    sys.exit(11)
  
  if not os.path.exists(init_file):
    log.fatal("Initial Heat configuration missing: %s", init_file)
    sys.exit(12)
  
  # Main program is loaded up.
  # Now, we want to initialize all our deployment handlers, disable any
  #   that aren't enabled, and log out which ones _are_ enabled.
  #   If none are enabled, we should error out.
  # Jan 21, 2025
  #   - Tools are only enabled via hardcoding in `deployments.py`. This is
  #     obviously not ideal, and will be improved once the configuration file
  #     is moved to `toml` and uses something more akin to modern Python's
  #     tooling configurations.
  enabled_tools = {}
  for name, module in deployments.TOOLS.items():
    log.debug("Attempting to initialize tool %s", name)
    try:
      module.init()
      enabled_tools[name] = module
    except (configparser.NoSectionError, KeyError):
      # Module isn't configured, therefore should be disabled
      log.debug("Disabling tool %s", name)
    except MissingRuntimeError:
      log.error("Missing runtime; disabling %s", name)
      # Continue on, since we don't
    except (FileNotFoundError, ConfigurationError) as e:
      log.error(str(e))
      log.error("Disabling tool %s", name)
  
  deployments.TOOLS = enabled_tools
  
  if not enabled_tools:
    log.error("No enabled tools...")
  else:
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
        try:
          current_config = json.loads(fh.read())
        except json.decoder.JSONDecodeError:
          # assume the current config is empty, and continue from there.
          log.error("Could not load cache file %s; defaulting to first run.", cache_file)
          with open(init_file) as fh:
            current_config = json.loads(fh.read())
    
    # Fetch new config
    # The new configuration is expected to have a different metadata blob as
    #   compared to the current, saved metadata.
    
    new_config = get_config(current_config["os-collect-config"]["cfn"], config["cloud"]["region"])
    
    # != in Python does a deep comparison of dictionaries
    if new_config["deployments"] != current_config["deployments"]:
      # We have a different set of deployment. Great! 
      for deployment in new_config["deployments"]:
        dep = deployments.get_deployment(copy.deepcopy(deployment))
        response = None
        signal = {
          "deploy_stdout": "",
          "deploy_stderr": "",
          "deploy_status_code": ""
        }
        try:
          # Try to generate a response
          response = dep.run()
        except Exception as e:
          # Generic exception sucks, but we do want any error at all to throw
          #   back to OpenStack that the system is in a fucked state so it
          #   rolls back and shit.
          log.error(str(e))
          signal["deploy_stderr"] = str(e)
          signal["os_heat_agent_is_error"] = str(e)
          signal["deploy_status_code"] = str(-254)
        else:
          # This part runs on success
          signal["deploy_stdout"] = response.stdout
          signal["deploy_stderr"] = response.stderr
          signal["deploy_status_code"] = str(response.exit_code)
          
          if response.exit_code != 0:
            log.debug("Reporting error")
            signal["os_heat_agent_is_error"] = response.stderr
        finally:
          # The dependency object is expected to know how to send a signal
          #   back to OpenStack, since the deployment signalling values are
          #   expected to be present in the deployment blob.
          resp = dep.signal(signal)
          if resp.status_code >= 300:
            log.error("Unsuccessful signal: %s", resp.status_code)
        
    
    # Save the cached file out
    with open(cache_file, "w") as fh:
      fh.write(json.dumps(new_config))
      
    log.debug("sleep %s", int(config["agent"]["polling_interval"]))
    time.sleep(int(config["agent"]["polling_interval"]))


# Why isn't this just named "get_region"
def dynamically_fetch_region():
  
  # Using a static URL here because this is the AWS well-known IP address,
  #   combined with the OpenStack directory structure.
  url = "http://169.254.169.254/openstack/latest/meta_data.json"
  metadata = requests.get(url).json()
  # Strip the trailing `a` because it's unused in Catalyst Cloud.
  # TODO: Find a better way of achieving this.
  return metadata["availability_zone"][:-1]
  
