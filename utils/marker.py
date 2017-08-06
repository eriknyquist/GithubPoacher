import json
import time
import tlog
import os

DEFAULT_LASTID =        10947291
DEFAULT_AVG =           42
MARKERFILE =            'conf/marker.json'
REPOCOUNT_REPOS =       0
REPOCOUNT_TIMESTAMP =   1

class Marker():

    def __init__(self):
        self.average = 0
        self.numrepos = 0
        self.current_timestamp = 0
        self.current_id = 0
        self.starting_id = 0
        self.newest_id = 0
        self.starttime = 0
        self.repo_id = DEFAULT_LASTID
        self.timestamp = time.time()
        self.averages_sum = 0
        self.numsessions = 0

        if not os.path.exists(MARKERFILE):
            tlog.log("Marker file %s doesn't exist, using defaults" %
                MARKERFILE)
            return

        self.__from_json(MARKERFILE)

    def __from_json(self, json_file):
        try:
            with open(json_file, 'r') as fh:
                data = json.load(fh)
        except Exception as e:
            tlog.log('Error reading file %s: %s' % (json_file, e))
            return

        try:
            self.repo_id = data['repo_id']
            self.timestamp = data['timestamp']
            self.averages_sum = data['averages_sum']
            self.numsessions = data['num_sessions']
        except Exception as e:
            tlog.log('Error parsing file %s: %s' % (json_file, e))
    
    def __to_json(self, json_file, avg):
        data = {}
        data['repo_id'] = self.current_id
        data['timestamp'] = time.time()
        data['averages_sum'] = self.averages_sum + avg
        data['num_sessions'] = self.numsessions + 1

        try:
            with open(json_file, 'w') as fh:
                data = json.dump(data, fh, indent=4)
        except Exception as e:
            tlog.log('Error writing file %s: %s' % (json_file, e))
            return

        
    def save(self, avg):
        self.__to_json(MARKERFILE, avg)
