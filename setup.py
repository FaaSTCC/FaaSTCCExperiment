from cloudburst.shared.reference import CloudburstReference
import numpy as np
from cloudburst.client.client import CloudburstConnection
from anna.lattices import WrenLattice
import pickle

def funcCopy(cloudburst,tx_size, zipfGenerator, *argv):
    next_read = []
    keys = set()
    zipfGenerator = pickle.loads(zipfGenerator)
    while len(keys) < tx_size:
        keys.add("k" + str(zipfGenerator.next()))

    for key in keys:
        next_read.append(CloudburstReference(key, True))

    return (tx_size, pickle.dumps(zipfGenerator), *argv)





def setup(db_size, dag_size, dag_name, cloudburst):
    def func(cloudburst, tx_size, zipfGenerator, *argv):
        next_read = []
        keys = set()
        return (tx_size, zipfGenerator, *argv)
    for i in range(db_size+1):
        cloudburst.put_object("k" + str(i), 1, WrenLattice)
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

    try:
        success, error = cloudburst.register_dag(dag_name, functions,
                                              connections)
        print(success)
    except:
        pass