import pymongo
import redis
#backendapi.default.svc.cluster.local:8080
import logging
import sys
import time
import zmq

import cloudpickle as cp

from cloudburst.server.benchmarks import utils

r = redis.Redis(host='127.0.0.1', port=61292, db=0)

logging.basicConfig(filename='log_trigger.txt', level=logging.INFO,
                    format='%(asctime)s %(message)s')

bname = 'tcc'
num_requests = 100

dag_name = 'test'
db_size = 1000
tx_size = 2
dag_size = 3
zipf = 1

create = True


msg = "%s:%s:%s:%s:%s:%s:%s:%s" % (bname,num_requests,dag_name,db_size,tx_size,dag_size,zipf,create)

p = r.pubsub()
p.psubscribe('result')



sent_msgs = 0

if create:
    r.publish('benchmark0', msg)

    for msg in p.listen():
        if "subscribe" in msg["type"]:
            continue
        msg = msg['data']
        if msg:
            break
msg = "%s:%s:%s:%s:%s:%s:%s:%s" % (bname,num_requests,dag_name,db_size,tx_size,dag_size,zipf,False)
r.publish('benchmarkt', msg)



epoch_total = []
total = []
end_recv = 0

epoch_recv = 0
epoch = 1
epoch_thruput = 0
epoch_start = time.time()
sent_msgs = 4

for msg in p.listen():
    if "subscribe" in msg["type"]:
        continue
    msg = msg['data']

    if b'END' in msg:
        end_recv += 1
        if end_recv >= sent_msgs:
            break
    else:
        msg = cp.loads(msg)

        if type(msg) == tuple:
            epoch_thruput += msg[0]
            new_tot = msg[1]
        else:
            new_tot = msg

        epoch_total += new_tot
        total += new_tot
        epoch_recv += 1

        if epoch_recv == sent_msgs:
            epoch_end = time.time()
            elapsed = epoch_end - epoch_start
            thruput = epoch_thruput / elapsed

            logging.info('\n\n*** EPOCH %d ***' % (epoch))
            logging.info('\tTHROUGHPUT: %.2f' % (thruput))
            utils.print_latency_stats(epoch_total, 'E2E', True)

            epoch_recv = 0
            epoch_thruput = 0
            epoch_total.clear()
            epoch_start = time.time()
            epoch += 1

logging.info('*** END ***')

if len(total) > 0:
    utils.print_latency_stats(total, 'E2E', True)