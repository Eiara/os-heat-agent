
Vagrant.configure("2") do |config|
  # Change this to your supported box/architecture as needed.
  config.vm.box = "generic/ubuntu2404-arm"
  
  
  # Disable installing recommended programs with apt-get install
  config.vm.provision "norecommends", type: "shell", path: "vagrant/scripts/00-norecommends.sh"
  # Install Babashka, for integration tests
  config.vm.provision "babashka", type: "shell", path: "vagrant/scripts/01-init.sh"
  # Install the requisite Python components
  config.vm.provision "python", type: "shell", path: "vagrant/scripts/02-python.sh"
end
