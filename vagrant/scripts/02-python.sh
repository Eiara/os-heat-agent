#!/bin/bash

sudo apt-get install -y pipx --no-install-recommends
sudo apt-get install -y jq --no-install-recommends
sudo apt-get install -y git --no-install-recommends
sudo apt-get install -y python-is-python3

sudo pipx ensurepath --global

sudo pipx install hatch