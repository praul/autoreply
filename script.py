#!/bin/env/python3

import sys
sys.path.append('/app')

from autoreplyer import AutoReplyer
import threading
from repliers import *
import time

def start_autoreplier(v):
    autoreplier= AutoReplyer(v)

def startup():
    processes = []
    for replier in v:
        processes.append( threading.Thread( target=start_autoreplier, args=(replier,) ) )
          
    for p in processes:
        p.start()

    for p in processes:
        p.join()

startup()