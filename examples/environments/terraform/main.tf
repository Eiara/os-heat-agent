terraform {
required_version = "~> 1.1"
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = ">= 1.49.0"
    }
  }
}

resource "openstack_networking_floatingip_v2" "ip" {
  # This is Catalyst Cloud specific; maybe should be a variable
  pool = var.public_network
}

### Create the loadbalancer

resource "openstack_lb_loadbalancer_v2" "loadbalancer" {
  name          = "lb"
  vip_subnet_id = var.subnet_id
}

### HTTP listener, for redirecting to https

resource "openstack_lb_listener_v2" "http" {
  name            = "http-listener"
  protocol        = "HTTP"
  protocol_port   = 80
  loadbalancer_id = openstack_lb_loadbalancer_v2.loadbalancer.id
}

resource "openstack_lb_pool_v2" "http" {
  name = "http"
  # Speaks HTTP to the backends
  #
  protocol    = "HTTP"
  lb_method   = "ROUND_ROBIN"
  listener_id = openstack_lb_listener_v2.http.id
  persistence {
    type = "SOURCE_IP"
  }
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
    image_id         = var.image_id
    network_id       = var.network_id
    subnet_id        = var.subnet_id
    key_name         = var.key_name
    security_groups  = join(",",var.security_groups)
    volume_size      = var.volume_size
    lb_pool_id       = openstack_lb_pool_v2.http.id
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