import sys
import os
import stat
import shutil
import json
import time
import argparse
from git import Repo
from git import GitCommandError
from optparse import OptionParser
from github import Github

sys.path.append('utils')
import marker
import tlog

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', action='store_true', dest='verbose')
args = parser.parse_args()

MAIN_CONF = 'conf/poacher.json'
conf = {
    'skip_empty_repos' : True,
    'max_repo_size_kb' : 20000
}

DEFAULT_STEP =          16
DUMP =                  'vulns.txt'
UPPER_INIT =            64
IGNORE_DIRS =           ['.git']

CONF_REQUIRED = [
    'archive_directory', 'working_directory', 'github_username',
    'github_password', 'repo_handler'
]

def check_main_conf(conf):
    ret = True
    for item in CONF_REQUIRED:
        if item not in conf or conf[item].strip() == '':
            tlog.log('Error: please set %s in file %s' % (item, MAIN_CONF))
            ret = False

    return ret

def parse_user_handler(abspath):
    mod_dir, mod = os.path.split(abspath)
    return mod_dir, os.path.splitext(mod)[0]

try:
    with open(MAIN_CONF, 'r') as fh:
        conf.update(json.load(fh))
except Exception as e:
    tlog.log('Error reading file %s: %s' % (MAIN_CONF, e))
    sys.exit(1)

if not check_main_conf(conf):
    sys.exit(1)

# Import handler module specified in main conf. file
module_dir, module_name = parse_user_handler(conf['repo_handler'])
sys.path.append(module_dir)
repo_handler = __import__(module_name)

repo_handler_logger = lambda msg: tlog.log(msg, desc=module_name)
marker = marker.Marker()

def authenticate():
    return Github(conf['github_username'], conf['github_password'])

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
    delta_s = time.time() - ts
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
    if os.path.exists(name):
        os.chmod(name, stat.S_IWRITE)

        desc = 'file or directory'
        try:
            if os.path.isdir(name):
                desc = 'directory'
                shutil.rmtree(name)
            else:
                desc = 'file'
                os.remove(name)
        except:
            tlog.log("Failed to remove %s %s, abandoning..." %
                     (desc, name))

def archive(archive_dir, repo, handler_logs):
    if not os.path.isdir(conf['archive_directory']):
        os.mkdir(conf['archive_directory'])

    path = os.path.join(conf['archive_directory'],
        os.path.basename(archive_dir) +  '_' + str(repo.id))

    os.mkdir(path)
    infofile = os.path.join(path, 'info.txt')
    with open(infofile, 'w') as fh:
        fh.write('URL : %s\n' % repo.html_url)
        fh.write('created at : %s\n' %
            repo.created_at.strftime('%m/%d/%Y %H:%M:%S'))
        if len(handler_logs) > 0:
            fh.write('\nlogs:\n\n')
            for log in handler_logs:
                fh.write('%s\n' % log)

    try:
        shutil.copytree(archive_dir, path + '/' + os.path.basename(archive_dir))
    except:
        tlog.log(("Failed to copy repo files while archiving: leaving "
                 "in %s") % conf['working_directory'])
        return

    shutil.rmtree(archive_dir, onerror=del_rw)

def main_loop():
    tlog.init(args.verbose)
    G = authenticate()

    guess = 0
    if marker.averages_sum > 0 and marker.numsessions > 0:
        guess = predict_growth(marker.timestamp, marker.averages_sum,
                marker.numsessions)

    newest = bsearch(G, marker.repo_id, guess)
    marker.current_id = newest
    marker.starting_id = newest
    marker.starttime = time.time()

    num = newest - marker.repo_id
    tlog.log('\n%d new repos since last check' % num)

    if not os.path.isdir(conf['working_directory']):
        os.mkdir(conf['working_directory'])

    while True:
        try:
            new = get_new(G, newest)
        except Exception as e:
            tlog.log(str(e))
            sys.exit(1)

        numnew = len(new)
        if numnew == 0:
            continue

        newest = marker.newest_id = new[-1].id
        #tlog.log('%d new repos found.' % numnew)
        marker.numrepos += numnew
        marker.current_timestamp = time.time()

        for repo in new:
            marker.current_id = repo.id

            tlog.log('%s' % repo.html_url)

            try:
                size = repo.size
            except:
                tlog.log('size unknown, skipping...')
                continue
            
            try:
                mbsize = float(size) / 1000.0
            except:
                tlog.log('size unknown, skipping...')
                continue

            if size > conf['max_repo_size_kb']:
                tlog.log('%.f2MB: Repo is too big, skipping...'
                         % mbsize)
                continue

            elif float(size) == 0.0000 and conf['skip_empty_repos']:
                tlog.log("Repo %s is empty, skipping..." % repo.name)
                continue

            tlog.log('size: %.2fMB' % mbsize)
            current = conf['working_directory'] + '/' + repo.name

            tlog.log('Cloning %s' % repo.name)
            try:
                Repo.clone_from(repo.html_url, current)
            except GitCommandError as e:
                tlog.log('Unable to clone: %s: skipping...' % e)
                continue

            handler_logs = []

            def handler_log(msg):
                handler_logs.append(msg)
                tlog.log(msg, desc=module_name)

            tlog.log('Running %s' % module_name)
            if repo_handler.run(current, handler_log):
                archive(current, repo, handler_logs)
            else:
                shutil.rmtree(current, onerror=del_rw)

def get_avg_per_min(delta, num):
    per_sec = float(num) / float(delta)
    return int(per_sec * 60)

def finish():
    npub = marker.numrepos
    nall = marker.newest_id - marker.starting_id

    delta = marker.current_timestamp - marker.starttime
    deltastr = tlog.secs_to_walltime(delta, compact=False)

    avg = get_avg_per_min(delta, nall)
    marker.save(avg)

    r_avg = float(marker.averages_sum + avg) / float(marker.numsessions + 1)
    tlog.log('%d new repos (%d public) in %s.' % (nall, npub, deltastr))
    tlog.log('Session average: %d new repos per minute' % avg)
    tlog.log('Running average: %d new repos per minute.' % r_avg)
    sys.exit(0)


def main():
    try:
        main_loop()
    except KeyboardInterrupt:
        tlog.log('Finishing...')
        time.sleep(2)
        finish()

if __name__ == "__main__":
    main()
