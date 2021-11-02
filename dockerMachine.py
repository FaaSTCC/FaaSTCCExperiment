from datetime import datetime

from cloudburst.client.client import CloudburstConnection
from cloudburst.shared.proto.cloudburst_pb2 import (
    Continuation,
    DagTrigger,
    FunctionCall,
    NORMAL, MULTI,  # Cloudburst's consistency modes,
    EXECUTION_ERROR, FUNC_NOT_FOUND,  # Cloudburst's error types
    MULTIEXEC # Cloudburst's execution types
)

from cloudburst.shared.reference import CloudburstReference
import numpy as np

from ZipfGenerator import ZipfGenerator
from setup import setup
import configparser
import pickle
from anna.lattices import WrenLattice
from cloudburst.shared.serializer import Serializer
serializer = Serializer()

def getTime():
    return datetime.now().timestamp() * 1000

def func(cloudburst, futureReads, *argv):
    next_read = []
    keys = futureReads.pop(0)
    for key in keys:
        next_read.append(CloudburstReference(key, True))
    return (futureReads, *next_read)

configParser = configparser.RawConfigParser()
configFilePath = r'./config/10000_5_test'
configParser.read(configFilePath)
print(configParser.sections())
db_size = int(configParser['your-config']['db_size'])
dag_size = int(configParser['your-config']['dag_size'])
dag_name = "test1"
tx_size = int(configParser['your-config']['tx_size'])
zipf = float(configParser['your-config']['zipf'])
num_requests = 100
cloudburst = CloudburstConnection('10.107.78.76', '10.0.2.15')
from anna.client import AnnaTcpClient
kvs = AnnaTcpClient("10.109.46.57", '10.0.2.15', local=False, offset=11)


#cloudburst.kvs_client = kvs
for i in range(db_size + 1):
    #cloudburst.put_object("k" + str(i), 1, WrenLattice)
    lattice = serializer.dump_lattice(1, typ=WrenLattice)
    kvs.put("k" + str(i), lattice)
    pass

functions = []
last = ""
connections = []
for i in range(dag_size):
    functions.append('func' + str(i))
    cloudburst.register(func, 'func' + str(i))
    if(last != ""):
        connections.append((last,'func' + str(i)))
    last = 'func' + str(i)


success, error = cloudburst.register_dag(dag_name, functions,
                                          connections)



zipfGenerator = ZipfGenerator(db_size, zipf)
next_read = []
keys = set()
while len(keys) < tx_size:
    keys.add("k" + str(zipfGenerator.next()))

for key in keys:
    next_read.append(CloudburstReference(key, True))


total_time = []
epoch_req_count = 0
epoch_latencies = []

epoch_start = getTime()
epoch = 0
requests = []
for _ in range(num_requests):
    next_read = []
    keys = set()
    output_key = "k" + str(zipfGenerator.next())
    futureReads = []
    while len(keys) < tx_size:
        keys.add("k" + str(zipfGenerator.next()))
    for key in keys:
        next_read.append(CloudburstReference(key, True))
    for i in range(dag_size):
        f_read = []
        keys = set()
        while len(keys) < tx_size:
            keys.add("k" + str(zipfGenerator.next()))
        futureReads.append(keys)

    arg_map = {'func0': [futureReads, *next_read]}
    requests.append(arg_map)

for request in requests:
    output_key = "k" + str(zipfGenerator.next())
    start = getTime()
    res = cloudburst.call_dag(dag_name, request,consistency=MULTI, output_key=output_key, direct_response= True)
    end = getTime()

    if res is not None:
        epoch_req_count += 1
        total_time += [end - start]
        epoch_latencies += [end - start]

    epoch_end = getTime()
    if epoch_end - epoch_start > 10000:
        print(epoch_req_count, epoch_latencies)

        print('EPOCH %d THROUGHPUT: %.2f' %
                     (epoch, (epoch_req_count / 10)))
        print(epoch_latencies,  'EPOCH %d E2E' % epoch, True)
        epoch += 1

        epoch_req_count = 0
        epoch_latencies.clear()
        epoch_start = getTime()

print(total_time, [], [], 0)

print("Hello")


