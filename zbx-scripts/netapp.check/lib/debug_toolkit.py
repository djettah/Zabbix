#!/usr/bin/env python3

import json
from functools import wraps
from time import time
import os
import fcntl
from datetime import datetime

TRACE=False
DRYRUN=False
DEBUG=False

delays={}

START_TIME = datetime.now()

def first(iter):
    return iter[0]

def deflogger(func):
    @wraps(func)    
    def wrapper(*args, **kwargs):
        #if TRACE: print ("[@deflogger] {} (args: {}, kwargs:{})".format (func.__name__, args, kwargs))
        #TRACE = kwargs['TRACE'] if kwargs['TRACE'] else False
        #print (kwargs)
        if TRACE: print ("[@deflogger] {}".format (func.__name__))
        return func(*args, **kwargs)
    return wrapper


def prettyprint_request(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in 
    this function because it is programmed to be pretty 
    printed and may differ from the actual request.
    """
    print('{}\n{}\n{}\n\n{}\n{}\n'.format(
        '-----------<prettyprint_request>-----------',
        req.method + ' ' + req.url,
        '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
        '-----------</prettyprint_request>-----------',

    ))

def dry_request(url, headers, method=None, payload=None):
    print ('[dryrun] would send request:\n', json.dumps({'url':url, 'method': method, 'headers':headers, 'payload':payload}, indent=4, sort_keys=False))

def debugtest01():
    print("test ok")

def measure(operation=sum):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            t = time()
            result = func(*args, **kwargs)
            ttr = time() - t
            #delays.append( {'func':func.__name__, 'args': args, 'kwargs':kwargs, 'ttr':ttr})
            key = func.__module__ + "." + func.__name__
            delays[key] = operation((ttr, delays.get(key, 0)))
            if TRACE: print("[@measure({0})] {1} took: {2:.2f} s".format(operation.__name__,key,ttr))
            return result
        return wrapper
    return decorator


fh=0
def run_once(main):
    global fh
    #fh=open(os.path.realpath(__file__),'r')
    fh=open(main,'r')
    try:
        fcntl.flock(fh,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return True
    except:
        #if DEBUG: print(main + " already running, exiting.")
        #os._exit(0)
        return False

def get_uptime():
    return (datetime.now() - START_TIME).total_seconds()

def handle_exception(exc_type, exc_value, exc_traceback, logger):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
