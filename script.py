#!/bin/env/python3

import sys
sys.path.append('/app')

from autoreplyer import AutoReplyer
from multiprocessing import Process
from repliers import *


def start_autoreplier(v):
    autoreplier= AutoReplyer(v)

def startup():
    processes = []
    for replier in v:
        processes.append(Process(target=start_autoreplier, args=(replier,)))
    
    for p in processes:
        p.start()

    for p in processes:
        p.join()


startup()