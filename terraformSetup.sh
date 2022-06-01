#!/bin/bash

cd ~/FaaSTCCExperiment/terraform-provider-grid5000-faastcc
cd examples/kubernetes
rm terraform.tfstate
terraform init
printf yes | terraform apply
printf yes | terraform apply
export KUBECONFIG=${PWD}/kube_config_cluster.yml
cp kube_config_cluster.yml ~/.kube/config
cd ~/FaaSTCCExperiment
sh ./setup
cd ~/FaaSTCCExperiment/terraform-provider-grid5000-faastcc/examples/kubernetes
printf yes | terraform destroy
cd ~/FaaSTCCExperiment
