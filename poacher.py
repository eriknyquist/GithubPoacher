from sys import path as sys_path
from sys import exit as sys_exit

from os import path as os_path
from os import chmod as os_chmod
from os import remove as os_remove
from os import mkdir as os_mkdir

from stat import S_IWRITE
from shutil import (rmtree, copytree)
from time import (time, sleep)
from json import load as json_load
from argparse import ArgumentParser
from getpass import getpass

from git import Repo
from git import GitCommandError
from optparse import OptionParser
from github import Github

banner = """
::::::::::.     ...       :::.       .,-:::::    ::   .:  .,::::::  :::::::..
 `;;;```.;;; .;;;;;;;.    ;;`;;    ,;;;'````'   ,;;   ;;, ;;;;''''  ;;;;``;;;;
  `]]nnn]]' ,[[     \[[, ,[[ '[[,  [[[         ,[[[,,,[[[  [[cccc    [[[,/[[['
   $$$''    $$$,     $$$c$$$cc$$$c $$$         '$$$'''$$$  $$''''    $$$$$$c
   888o     '888,_ _,88P 888   888,`88bo,__,o,  888   '88o 888oo,__  888b '88bo,
   YMMMb      'YMMMMMP'  YMM   ''`   'YUMMMMMP' MMM    YMM '''YUMMM MMMM   'W'
"""

sys_path.append('utils')
import marker
import tlog

parser = ArgumentParser()
parser.add_argument('-v', '--verbose', action='store_true', dest='verbose')
args = parser.parse_args()

MAIN_CONF = 'conf/poacher.json'

CONF_SKIP_EMPTY = "skip_empty_repos"
CONF_MAX_SIZE   = "max_repo_size_kb"
CONF_CLONE      = "clone"
CONF_MONITOR    = "monitor_only"
CONF_POLL_DELAY = "poll_delay_seconds"
CONF_UNAME      = "github_username"
CONF_PWD        = "github_password"
CONF_HANDLER    = "repo_handler"
CONF_WORKDIR    = "working_directory"
CONF_ARCHDIR    = "archive_directory"

conf = {
    CONF_SKIP_EMPTY : True,
    CONF_MAX_SIZE   : 20000,
    CONF_CLONE      : False,
    CONF_MONITOR    : True,
    CONF_POLL_DELAY : 0.0
}

DEFAULT_STEP =          16
UPPER_INIT =            64

CONF_REQUIRED = [
    CONF_ARCHDIR, CONF_WORKDIR
]

def get_conf_from_user(conf, conf_item, prompt, echo=True):
    ret = False
    if conf_item not in conf or conf[conf_item].strip() == "":
        ret = True
        while conf[conf_item].strip() == "":
            if echo:
                conf[conf_item] = raw_input(prompt.encode())
            else:
                conf[conf_item] = getpass(prompt.encode())

    return ret

def check_main_conf(conf):
    ret = True
    for item in CONF_REQUIRED:
        if item not in conf or conf[item].strip() == "":
            tlog.write('Error: please set %s in file %s' % (item, MAIN_CONF))
            ret = False

    not_in_conf = get_conf_from_user(conf, CONF_UNAME, "Github username: ")
    if not_in_conf:
        msg = "Github password: "
    else:
        msg = "Github password for %s: " % (conf[CONF_UNAME])

    get_conf_from_user(conf, CONF_PWD, msg, echo=False)

    return ret

def parse_user_handler(abspath):
    mod_dir, mod = os_path.split(abspath)
    return mod_dir, os_path.splitext(mod)[0]

def import_user_handler(conf):
    if conf[CONF_MONITOR]:
        conf[CONF_CLONE] = False
        return None, None

    # Import handler module from main conf, if defined...
    repo_handler = None
    module_name = None

    module_dir, module_name = parse_user_handler(conf[CONF_HANDLER])
    repo_handler_logger = lambda msg: tlog.log(msg, desc=module_name)

    sys_path.append(module_dir)

    try:
        repo_handler = __import__(module_name)
    except Exception as e:
        tlog.write("Error importing handler %s: %s" % (module_name, e))

    return module_name, repo_handler

def authenticate(conf):
    return Github(conf[CONF_UNAME], conf[CONF_PWD])

def get_new(githubObj, last):
    ret = []

    for repo in githubObj.get_repos(since=last):
            ret.append(repo)

    return ret

def repo_exists(githubObj, id):
    try:
        githubObj.get_repos(since=id)[0]
    except:
        return False
    else:
        return True

def predict_growth(ts, sumavg, numsessions):
    avg = float(sumavg) / float(numsessions)
    delta_s = time() - ts
    delta_m = float(delta_s) / 60.0
    return int(delta_m * avg)

def bsearch(githubObj, lower, growth_prediction):
    upper = lower + growth_prediction
    set = None

    tlog.log('Starting binary search for latest repo ID, last ID was %s'
             % lower)

    step = DEFAULT_STEP
    while not set:
        tlog.log('trying ID %s' % upper)

        if repo_exists(githubObj, upper):
            upper += step
            step *= 2
        else:
            tlog.log('ID %s not yet used\n' % upper)
            set = 1

    tlog.log('Beginning search between %s and %s'
             % (lower, upper))

    while (lower + 1) < upper:
        tlog.log('search area size: %s' % (upper - lower))
        middle = lower + (upper - lower) / 2

        if repo_exists(githubObj, middle):
            lower = middle
        else:
            upper = middle

    return lower

def del_rw(action, name, exc):
    if os_path.exists(name):
        os_chmod(name, S_IWRITE)

        desc = 'file or directory'
        try:
            if os_path.isdir(name):
                desc = 'directory'
                rmtree(name)
            else:
                desc = 'file'
                os_remove(name)
        except:
            tlog.log("Failed to remove %s %s, abandoning..." %
                     (desc, name))

def archive(archive_dir, repo, handler_logs):
    if not os_path.isdir(conf[CONF_ARCHDIR]):
        os_mkdir(conf[CONF_ARCHDIR])

    path = os_path.join(conf[CONF_ARCHDIR],
        os_path.basename(archive_dir) +  '_' + str(repo.id))

    os_mkdir(path)
    infofile = os_path.join(path, 'info.txt')
    with open(infofile, 'w') as fh:
        fh.write('URL : %s\n' % repo.html_url.encode('utf-8'))
        fh.write('created at : %s\n' %
            repo.created_at.strftime('%m/%d/%Y %H:%M:%S'))
        if len(handler_logs) > 0:
            fh.write('\nlogs:\n\n')
            for log in handler_logs:
                fh.write('%s\n' % log.encode('utf-8'))

    try:
        copytree(archive_dir, path + '/' + os_path.basename(archive_dir))
    except:
        tlog.write(("Failed to copy repo files while archiving: leaving "
                 "in %s") % conf[CONF_WORKDIR])
        return

    rmtree(archive_dir, onerror=del_rw)

def run_handler(current, repo, repo_handler, handler_log):
    max_retries = 2
    retries = 0

    while retries < max_retries:
        try:
            ret = repo_handler.run(current, repo, handler_log)
        except Exception as e:
            tlog.write("Error in handler: %s" % e)
            retries = retries + 1
            sleep(1)
        else:
            return ret

    tlog.write("Max. retries reach. Unable to process repo " + repo.full_name)
    return False

def get_repo_size(repo):
    try:
        size = repo.size
    except:
        tlog.log("Repo %s has unknown size" % repo.name)
        return 0, 0

    mbsize = size
    try:
        mbsize = float(size) / 1000.0
    except:
        tlog.log("Repo %s has unknown size" % repo.name)
        return 0, 0

    return size, mbsize

def clone_repo(repo, size, mbsize, conf):
    if not conf[CONF_CLONE]:
        return None

    if size > conf[CONF_MAX_SIZE]:
        tlog.log('%.2fMB: Repo is too big, will not clone' % mbsize)
        return None

    current = conf[CONF_WORKDIR] + '/' + repo.name
    clone_path = current.decode()

    tlog.log('Cloning %s' % repo.name)
    try:
        Repo.clone_from(repo.html_url, current)
    except GitCommandError as e:
        tlog.log('Unable to clone: %s: skipping...' % e)
        return None

    # Sleep for 100ms to ensure files have finished downloading
    sleep(0.1)
    return clone_path

def main_loop(conf, mark, repo_handler, module_name):
    tlog.init(args.verbose)
    G = authenticate(conf)

    if repo_handler != None:
        tlog.log('Using handler %s' % module_name)

    guess = 0
    if mark.averages_sum > 0 and mark.numsessions > 0:
        guess = predict_growth(mark.timestamp, mark.averages_sum,
                mark.numsessions)

    if mark.numsessions > 0:
        tlog.log("last session ended at %s, latest repo ID was %d"
            % (tlog.timestamp(time=int(mark.timestamp)), mark.repo_id))
        tlog.log("at %d repos per minute, predicted current latest repo ID is "
            "at least %d" % (mark.averages_sum / mark.numsessions,
            mark.repo_id + guess))

    newest = bsearch(G, mark.repo_id, guess)
    mark.current_id = newest
    mark.starting_id = newest
    mark.starttime = time()

    tlog.log('Latest repo ID is %d' % newest)

    if not os_path.isdir(conf[CONF_WORKDIR]):
        os_mkdir(conf[CONF_WORKDIR])

    while True:
        sleep(conf[CONF_POLL_DELAY])

        try:
            new = get_new(G, newest)
        except Exception as e:
            tlog.write("Error getting new repos from Github: " + str(e))
            sys_exit(1)

        numnew = len(new)
        if numnew == 0:
            continue

        newest = mark.newest_id = new[-1].id
        mark.numrepos += numnew
        mark.current_timestamp = time()

        for repo in new:
            mark.current_id = repo.id

            size, mbsize = get_repo_size(repo)
            if size == 0.000 and conf[CONF_SKIP_EMPTY]:
                continue

            tlog.log('%s (%.2fMB)' % (repo.html_url, mbsize))

            if repo_handler == None:
                continue

            clone_path = clone_repo(repo, size, mbsize, conf)
            handler_logs = []

            def handler_log(msg):
                handler_logs.append(msg)
                tlog.log(msg, desc=module_name)

            if (run_handler(clone_path, repo, repo_handler, handler_log)
                    and conf[CONF_CLONE]):
                archive(clone_path, repo, handler_logs)
            elif conf[CONF_CLONE] and clone_path != None:
                rmtree(clone_path, onerror=del_rw)

def get_avg_per_min(delta, num):
    per_sec = float(num) / float(delta)
    return int(per_sec * 60)

def finish(mark):
    npub = mark.numrepos
    nall = mark.newest_id - mark.starting_id

    delta = mark.current_timestamp - mark.starttime
    deltastr = tlog.secs_to_walltime(delta, compact=False)

    avg = get_avg_per_min(delta, nall)
    mark.save(avg)

    r_avg = float(mark.averages_sum + avg) / float(mark.numsessions + 1)
    tlog.log('%d new repos (%d public) in %s.' % (nall, npub, deltastr))
    tlog.log('Session average: %d new repos per minute' % avg)
    tlog.log('Running average: %d new repos per minute.' % r_avg)
    sys_exit(0)


def main():
    try:
        with open(MAIN_CONF, 'r') as fh:
            conf.update(json_load(fh))
    except Exception as e:
        tlog.write('Error reading file %s: %s' % (MAIN_CONF, e))
        sys_exit(1)

    if not check_main_conf(conf):
        sys_exit(1)

    if args.verbose:
        print banner

    module_name, repo_handler = import_user_handler(conf)
    mark = marker.Marker()

    if (CONF_HANDLER not in conf or conf[CONF_HANDLER] == ""
            or repo_handler == None):
        tlog.write("Monitor Mode (no active handler. keeping track of repository "
                 "creation rate, nothing more)")

    try:
        main_loop(conf, mark, repo_handler, module_name)
    except KeyboardInterrupt:
        tlog.write('Finishing...')
        sleep(2)
        finish(mark)

if __name__ == "__main__":
    main()
