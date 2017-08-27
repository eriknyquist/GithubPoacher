import datetime
import time
import os

DESCPAD =             10
DEFAULT_DESC =        'poacher'
TS_TEMPLATE =         "%m-%d-%Y %H:%M:%S.%f"

start =               time.time()
verbose =             True

def timestamp(time=None):
    if time == None:
        timeval = datetime.datetime.now()
    else:
        timeval = datetime.datetime.fromtimestamp(time)

    return timeval.strftime(TS_TEMPLATE)[:-3]

def init(arg_verbose):
    global verbose
    verbose = arg_verbose

def secs_to_walltime(delta, compact=True):
    delta_m, delta_s = divmod(delta, 60)
    delta_h, delta_m = divmod(delta_m, 60)

    if compact:
        return '%d:%02d:%02d' % (delta_h, delta_m, delta_s)

    ret = ''
    if delta_h != 0:
        ret += '%d hours' % delta_h

    if delta_m != 0:
        ret += ((('%d' if ret == '' else ', %d') + ' minutes') % delta_m)

    if delta_s != 0:
        ret += ((('%d' if ret == '' else ', %d') + ' seconds') % delta_s)

    return ret

def write(msg, desc=DEFAULT_DESC):
    splitdesc = os.path.splitext(desc)[0]
    ts = timestamp()
    ut = secs_to_walltime(time.time() - start)

    splitmsg = msg.strip().split('\n')

    for m in splitmsg:
        line = '[%s] [%s] %s:> %s' % (ts, ut, splitdesc, m)
        print line

def log(msg, desc=DEFAULT_DESC):
    if not verbose:
        return

    write(msg, desc)
