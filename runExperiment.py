//  Copyright 2021 Taras Lykhenko, Rafael Soares
//
//  Licensed under the Apache License, Version 2.0 (the "License");
//  you may not use this file except in compliance with the License.
//  You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.

import argparse

import pymongo
import redis
import logging
import sys
import time

import cloudpickle as cp

import os
from datetime import datetime
logging.basicConfig(filename='log_trigger.txt', level=logging.INFO,
                    format='%(asctime)s %(message)s')

import numpy as np



def print_latency_stats(data, ident, log=False, epoch=0, result_logger=False):
    npdata = np.array(data)
    tput = 0

    if epoch > 0:
        tput = len(data) / epoch

    mean = np.mean(npdata)
    median = np.percentile(npdata, 50)
    p75 = np.percentile(npdata, 75)
    p95 = np.percentile(npdata, 95)
    p99 = np.percentile(npdata, 99)
    mx = np.max(npdata)

    p25 = np.percentile(npdata, 25)
    p05 = np.percentile(npdata, 5)
    p01 = np.percentile(npdata, 1)
    mn = np.min(npdata)

    output = ('%s LATENCY:\n\tsample size: %d\n' +
              '\tTHROUGHPUT: %.4f\n'
              '\tmean: %.6f, median: %.6f\n' +
              '\tmin/max: (%.6f, %.6f)\n' +
              '\tp25/p75: (%.6f, %.6f)\n' +
              '\tp5/p95: (%.6f, %.6f)\n' +
              '\tp1/p99: (%.6f, %.6f)') % (ident, len(data), tput, mean,
                                           median, mn, mx, p25, p75, p05, p95,
                                           p01, p99)

    if result_logger:
        result_logger.info(output)
    if log:
        logging.info(output)
    else:
        print(output)

def setupKubernetes(hydroHome):
    path = os.path.join(hydroHome, "cluster")
    os.chdir(path)
    os.environ["HYDRO_HOME"] = hydroHome
    os.system("kubectl create namespace hydro")
    os.system("kubectl config set-context --current --namespace=hydro")

    os.system("python3 -m hydro.cluster.create_cluster -m 4 -r 1 -f 40 -s 1 -b 4 -l False")

def populate(r,p, bname,num_requests,dag_name,db_size,tx_size,dag_size,zipf,create = True):
    msg = "%s:%s:%s:%s:%s:%s:%s:%s" % (bname,num_requests,dag_name,db_size,tx_size,dag_size,zipf,create)

    if create:
        r.publish('benchmark0', msg)

        for msg in p.listen():
            if "subscribe" in msg["type"]:
                continue
            msg = msg['data']
            if msg:
                break


def run_expermiment(r,p, bname,num_requests,dag_name,db_size,tx_size,dag_size,zipf, has_logging = True):
    msg = "%s:%s:%s:%s:%s:%s:%s:%s" % (bname, num_requests, dag_name, db_size, tx_size, dag_size, zipf, False)
    r.publish('benchmarkt', msg)
    epoch_total = []
    total = []
    end_recv = 0

    epoch_recv = 0
    epoch = 1
    epoch_thruput = 0
    epoch_start = time.time()
    sent_msgs = 4*4

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
                if has_logging:
                    logging.info('\n\n*** EPOCH %d ***' % (epoch))
                    logging.info('\tTHROUGHPUT: %.2f' % (thruput))
                    print_latency_stats(epoch_total, 'E2E', logging)

                epoch_recv = 0
                epoch_thruput = 0
                epoch_total.clear()
                epoch_start = time.time()
                epoch += 1

    return total

def cleanUpKubernetes():
    os.system("kubectl config set-context --current --namespace=default")

    os.system("kubectl delete namespaces hydro")

def experiment(test, experiments,redisService, redisPort, hydro, faasTCC):

    setup = {
        "bname" : 'tcc',
        "num_requests" : 1000,
        "dag_name" : test,
        "db_size" : 100000,
        "tx_size" : 2,
        "dag_size" : 6,
        "zipf" : 1,
    }
    systems = {
        #"hydro" : hydro,
        "faastTCC" : faasTCC
    }
    flag = True
    while flag:
        try:
            r = redis.Redis(host=redisService, port=redisPort, db=0)
            p = r.pubsub()
            p.psubscribe('result')
            print("Subbed to redis")
            flag = False
        except:
            continue
    # Gets or creates a logger
    logger = logging.getLogger("result")

    # set log level
    logger.setLevel(logging.INFO)

    # define file handler and set formatter
    file_handler = logging.FileHandler('results_%s.log' % test)
    formatter = logging.Formatter('%(asctime)s %(message)s')
    file_handler.setFormatter(formatter)

    # add file handler to logger
    logger.addHandler(file_handler)
    for system in systems.keys():
        for experiment in experiments:
            total = []
            logging.info('*** Experiment system %s %s = %s ***' % (system, test, str(experiment)))
            logger.info('*** Experiment system %s %s = %s ***' % (system, test, str(experiment)))
            setup[test] = experiment
            setupKubernetes(systems[system])
            time.sleep(600)
            logging.info('*** Being Populate ***')
            populate(r,p, setup["bname"],setup["num_requests"],setup["dag_name"],setup["db_size"],setup["tx_size"],setup["dag_size"],setup["zipf"], create = True)
            time.sleep(90)
            logging.info('*** Warm Up ***')
            run_expermiment(r,p, setup["bname"],setup["num_requests"]*2,setup["dag_name"],setup["db_size"],setup["tx_size"],setup["dag_size"],setup["zipf"], has_logging = False)
            logging.info('*** Warm End ***')
            logging.info('*** Experiment ***')
            start = datetime.now().timestamp()
            total = run_expermiment(r,p, setup["bname"],setup["num_requests"],setup["dag_name"],setup["db_size"],setup["tx_size"],setup["dag_size"],setup["zipf"], has_logging = True)
            exp_time = datetime.now().timestamp() - start
            logging.info('*** Experiment Result***')
            if len(total) > 0:
                print_latency_stats(total, 'E2E', True, exp_time, result_logger=logger)
            logging.info('*** Experiment End***')

            cleanUpKubernetes()


    logging.info('*** END ***')

def str2bool(v):
    try:
        return int(v)
    except ValueError:
        return float(v)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''Runs experiments''')

    parser.add_argument('-t', '--test', nargs=1, type=str, metavar='T',
                        help='Experiemnt field' +
                             '(required)', dest='test', required=True)

    parser.add_argument('-e', '--experiments', nargs="+", type=str2bool, metavar='E',
                        help='Experiemnt ' +
                             '(required)', dest='experiments', required=True)

    parser.add_argument('-r', '--redish', nargs=1, type=str, metavar='R',
                        help='redis host ' +
                             '(required)', dest='redish', required=True)

    parser.add_argument('-p', '--redisp', nargs=1, type=int, metavar='P',
                        help='redis port ' +
                             '(required)', dest='redisp', required=True)

    parser.add_argument('-hh', '--hydro', nargs=1, type=str, metavar='H',
                        help='hydro home ' +
                             '(required)', dest='hydro', required=True)

    parser.add_argument('-f', '--faastccs', nargs=1, type=str, metavar='F',
                        help='faastccs home ' +
                             '(required)', dest='faastccs', required=True)




    args = parser.parse_args()
    print(args.test[0])
    print(args.experiments)
    print(args.redish[0])
    print(args.redisp[0])
    print(args.hydro[0])
    print(args.faastccs[0])
    experiment(args.test[0], args.experiments, args.redish[0], args.redisp[0],
                  args.hydro[0], args.faastccs[0])
