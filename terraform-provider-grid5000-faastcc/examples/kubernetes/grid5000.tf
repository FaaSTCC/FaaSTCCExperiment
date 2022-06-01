locals {
  site        = "nancy"
  nodes_count = 18
  types = ["C","M","M","M","M","F","F","F","F","F","F","F","F","F","F","B","B","S"]
}

resource "grid5000_job" "my_job1" {
  name      = "Terraform RKE"
  site      = local.site
  command   = "sleep 72h"
  resources = "/nodes=${local.nodes_count},walltime=1:0:0"
  properties = "cluster='gros'"
  types     = ["deploy"]
}

resource "grid5000_deployment" "my_deployment" {
  site        = local.site
  environment = "debian10-x64-base"
  nodes       = grid5000_job.my_job1.assigned_nodes
  key         = file("~/.ssh/id_rsa.pub")
}
