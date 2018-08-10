__version__ = "0.1"

import time
import argparse

from github import Github
from github.GithubException import UnknownObjectException

DEFAULT_STEP =          64

class GithubPoacher(object):
    """
    Base class containing functionality to poll github.com for new repositories.
    Extend this class and override poacher.GithubPoacher.on_repo to get information
    about new repositories as they are created.
    """

    def __init__(self, poll_delay_seconds=2.0, github_retries=10,
            github_retry_delay_seconds=2.0):
        """
        :param float poll_delay_seconds: time to wait between checking for new \
            repos at github.com
        :param int github_retries: number of times to retry a failed github.com\
            request before giving up
        :param float github_retry_delay_seconds: time to wait between retrying \
            a failed github.com request
        """

        self.repo_id = None
        self.github_retries = github_retries
        self.poll_delay_seconds = poll_delay_seconds
        self.github_retry_delay_seconds = github_retry_delay_seconds

    def _get_new(self, last):
        ret = []
        retries = 0

        while True:
            try:
                for repo in self.github.get_repos(since=last):
                    ret.append(repo)
            except Exception as e:
                print("Error getting new repos from Github: " + str(e))

                if self.github_retries > 0:
                    if retries >= (self.github_retries - 1):
                        raise e

                    retries += 1

                time.sleep(self.github_retry_delay_seconds)
            else:
                break

        return ret

    def _repo_exists(self, repoid):
        try:
            _ = self.github.get_repos(since=repoid)[0]
        except IndexError:
            return False

        return True

    def _bsearch(self, startid):
        upper = startid
        lower = startid
        idset = False

        step = DEFAULT_STEP
        while not idset:
            self.on_search_iteration(lower, upper)
            if self._repo_exists(upper):
                upper += step
                step *= 2
            else:
                idset = True

        while (lower + 1) < upper:
            middle = int(lower + ((upper - lower) / 2.0))

            if self._repo_exists(middle):
                lower = middle
            else:
                upper = middle

            self.on_search_iteration(lower, upper)

        return lower

    def on_search_iteration(self, lower, upper):
        """
        Override this method. This method will be called each time
        the search parameters are updated during the initial binary search
        for the latest repository ID in GithubPoacher.main_loop.

        :param int lower: lowest repository ID in search area
        :param int upper: highest repository ID in search area
        """

        pass

    def on_lock(self, repo_id):
        """
        Override this method. This method will be called when the binary search
        for the latest repo ID in GithubPoacher.main_loop is complete

        :param int repo_id: result of binary search (latest repository ID)
        """

        pass 

    def on_repo(self, repo):
        """
        Override this method. This method will be called by
        GithubPoacher.main_loop whenever a new Github repo is created.

        :param PyGithub.Repo repo: Repo object for repository (see PyGithub \
            documentation)
        """

        pass

    def on_repos_processed(self, num):
        """
        Override this method. This method will be called in each iteration of
        GithubPoacher.main_loop, after GithubPoacher.on_repo has been called
        for all new repos returned by a request to github.com

        :param int num: the number of new repositories processed
        """

        pass

    def authenticate(self, username, password):
        """
        Authenticate with Github

        :param str username: Github username
        :param str password: Github password
        """

        self.github = Github(username, password)

    def main_loop(self, start_id=99525181):
        """
        Find the latest repository on github.com and start polling to get
        new repositories as they become available. This method never returns.

        :param int startid: github repository ID for a known existing \
            repository on github.com to start binary search for latest \
            repository
        """

        if not self._repo_exists(start_id):
            raise ValueError("Repo with ID %d doesn't exist yet" % start_id)

        self.repo_id = newest = self._bsearch(start_id)
        self.on_lock(newest)

        while True:
            new = self._get_new(newest)
            if len(new) == 0:
                continue

            for repo in new:
                self.on_repo(repo)

            self.on_repos_processed(len(new))
            self.repo_id = newest = new[-1].id
            time.sleep(self.poll_delay_seconds)
