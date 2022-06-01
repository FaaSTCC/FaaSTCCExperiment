# FaaSTCC Experiment

This repository includes all the files necessary to run the experiments regarding [FaaSTCC](https://dl.acm.org/doi/10.1145/3464298.3493392). 

## Deployment
FaaSTCC deployment relies on Kubernetes, requiring specific resources for some pods. 
More information about the kubernetes deployment can be found in the [ClusterTCC respository](https://github.com/FaaSTCC/clusterTCC).

FaaSTCC was deployed and tested on the [GRID'5000](https://www.grid5000.fr/w/Grid5000:Home) datacenter, in the Nancy site.
We include the necessary config files for the cluster in [the terraform directory](terraform-provider-grid5000-faastcc), 
along with a [script to start the deployment](terraformSetup.sh).

### Deploying Locally

FaaSTCC can also be deployed in local environments like [Minikube](https://minikube.sigs.k8s.io/docs/). Some considerations when running on Minikube:
* In [runExperiment.py](runExperiment.py), in the `setupKubernetes` function, the last flag `-l` must be set to `True`. 
* The current deployment requires both __hardware requirements__ and __node selectors__ ([example](https://github.com/FaaSTCC/clusterTCC/blob/master/hydro/cluster/yaml/ds/function-ds.yml)). You may remove these limitations for local testing.

## Experimental configuration
Experimental configuration is defined in [runExperiment.py](runExperiment.py), inside the experiment function in the `setup` dictionary.
Some general configuration information:
* `num_requests`: Number of DAGs executed by each client;
* `db_size`: Number of keys in the key-set;
* `tx_size`: Number of keys read by each function in the DAG;
* `dag_size`: Number of functions per DAG;
* `zipf`: Zipfian distribution access of data.

You may also change the number of pods of the system, present in the `setupKubernetes` function:
* `-m`: Number of memory pods. Each pod includes 4 threads of [Anna](https://github.com/FaaSTCC/annaTCC/tree/master/src/kvs).
* `-r`: Number of routing pods. Each pod includes 4 threads of [Anna Routers](https://github.com/FaaSTCC/annaTCC/tree/master/src/route).
* `-f`: Number of function pods. Each pod includes 3 threads of [Cloudburst Executors](https://github.com/FaaSTCC/cloudburstTCC/tree/master/cloudburst/server/executor) and 1 thread of [Anna Cache](https://github.com/FaaSTCC/cacheTCC).
* `-s`: Number of scheduler pods. Each pod includes 1 [Cloudburst Scheduler](https://github.com/FaaSTCC/cloudburstTCC/tree/master/cloudburst/server/scheduler).
* `-b`: Number of benchmark pods. Each pod includes 4 [Cloudburst Benchmarks/Clients](https://github.com/FaaSTCC/cloudburstTCC/tree/master/cloudburst/server/benchmarks) (__Note:__ If changing the number of benchmark clients, the `sent_msgs` variable in `run_experiment` must be changed to the new number of pods, in the form of 4*`benchmark_nodes`).

__Note:__ You may see a rather large `sleep` (currently of 15 minutes) in the `experiment` function of [runExperiment.py](runExperiment.py). 
This is due to delays on the Cloudburst environment to stabilize. This sleep may have to be adjusted depending on the deployment environment.

## Running the experiments

First, you must deploy your Kubernetes cluster, either using Minikube, the provided [GRID'5000 script](terraformSetup.sh) or any other kubernetes deployment.
Then we provide the [setup script](setup), where you may define the experiment to be run:
* `-t` defines the varying variable, representing the `setup` dictionary variable that will vary through experiments.
* `-e` defines the experimental values to run.

An example is provided in the [setup](setup) file, testing with multiple zipfians through `1` and `1.5`.

__Note__: Due to the high amount of Docker images that the Kubernetes cluster pulls, we require a docker account, which username and password must be provided in the `setup` script.