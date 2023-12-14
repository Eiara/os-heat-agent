#!/bin/bash

cat <<EOF | sudo tee /etc/apt/apt.conf.d/00-norecommends.conf > /dev/null
APT::Install-Recommends "false";
APT::Install-Suggests "false"; 
EOF