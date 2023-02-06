variable "name" {
  type = string
  description = "name"
  default = "test"
}

variable "public_network" {
  type = string
  description = "Public network for IP allocations and stuff"
}

variable "network_id" {
  type = string
}

variable "subnet_id" {
  type = string
  description = "Subnet ID"
}

variable "flavor" {
  type = string
  description = "Instance flavor"
}

variable "volume_size" {
  type = number
  description = "volume size"
  default = 10
}

variable "image_id" {
  type = string
}

variable "key_name" {
  type = string
}
variable "security_groups" {
  type = list(string)
  description = "security groups"
}