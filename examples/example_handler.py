# This is sample handler for poacher. It searches all files in the cloned
# repo for text matching a regex. If it finds a match, it will log the
# matching text using the provided log() function, and return 'True', to
# ensure the cloned repo gets archived.
#
# This is not really a useful handler, beyond demonstration purposes. In reality
# this handler will turn up many false positives (try it and see!)

import re
import os

regex = (
    '(password|passwd|accesskey|access_key|accesstok|access_tok|accesstoken|'
    'access_token)\s*(=|:=)\s*(\"|\')?[A-Za-z0-9+/\-&@!]+(\"|\')?'
)

pattern = re.compile(regex)

# Search a given file for the regex, and
# print anything we find to log function
def search_file_for_pattern(filename, log):
    ret = False
    with open(filename, 'r') as fh:
        lines = fh.readlines()

    for line in lines:
        for match in pattern.finditer(line):
            log("Found match in file %s: %s" % (filename, match.group(0)))
            ret = True

    return ret

def run(repo_path, repo, log):
    # repo_path will be set to None if there is no local clone available (i.e.
    # if 'clone' is set to false in poacher.json). Return value doesn't matter
    # in this case, since poacher ignores the return value of a handler when
    # 'clone' is set to false
    if repo_path == None:
        return False

    ret = False
    log("Searching files in repo %s" % repo.full_name)

    # Walk through all files in the repo directory and subdirectories,
    # reading each file we find and searching it for the regex
    for root, subdirs, files in os.walk(repo_path):
        for f in files:
            if search_file_for_pattern(os.path.join(root, f), log):
                # Found something! make sure to return True, so
                # that a copy of this repo gets copied to your archive directory
                ret = True

    return ret
