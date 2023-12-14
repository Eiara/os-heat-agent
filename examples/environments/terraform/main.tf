terraform {
required_version = "~> 1.1"
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = ">= 1.49.0"
    }
  }
}

data "openstack_images_image_v2" "image" {
  name        = var.image_name
  most_recent = true
}

##
## Networking
##

data "openstack_networking_network_v2" "public" {
   name = var.public_network
}

resource "openstack_networking_floatingip_v2" "ip" {
  # This is Catalyst Cloud specific; maybe should be a variable
  pool = var.public_network
}

resource "openstack_networking_network_v2" "network" {
  name           = "example_network"
  admin_state_up = "true"
}

resource "openstack_networking_subnet_v2" "subnet" {
  name       = "example_network_subnet"
  network_id = openstack_networking_network_v2.network.id
  cidr       = "192.168.199.0/24"
  ip_version = 4
}

resource "openstack_networking_router_v2" "router" {
  name                = "example_router"
  external_network_id = data.openstack_networking_network_v2.public.id
}

resource "openstack_networking_router_interface_v2" "router" {
  router_id = openstack_networking_router_v2.router.id
  subnet_id = openstack_networking_subnet_v2.subnet.id
}

##
## Orchestration stack
##

locals {
  orchestration_outputs = { for s in openstack_orchestration_stack_v1.stack.outputs : s["output_key"] => s["output_value"] }
}

resource "openstack_orchestration_stack_v1" "stack" {
  name = var.name
  parameters = {
    name             = var.name
    flavor           = var.flavor
    image_id         = data.openstack_images_image_v2.image.id
    network_id       = openstack_networking_network_v2.network.id
    subnet_id        = openstack_networking_subnet_v2.subnet.id
    key_name         = var.key_name
    security_groups  = join(",",var.security_groups)
    volume_size      = var.volume_size
    protocol_port    = 80
    ip_address        = openstack_networking_floatingip_v2.ip.id
    # TODO:
    # Add a health check to this
    #volume_type      = var.volume_type
  }
  template_opts = {
    Bin = file("${path.module}/yaml/software_config.yaml")
  }
  environment_opts ={ 
    Bin = ""
  }
}