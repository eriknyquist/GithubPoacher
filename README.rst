Github Repository Poacher
=========================

What is this?
-------------

This is a tool for Windows and Linux PCs, which polls github.com for newly
created repostories, clones them, and allows you to do something with the cloned
files. Effectively, this allows you to write a handler/script to be executed on
any newly-created Github repositories, as soon as they appear on github.com.

How does it work?
-----------------

The Github API doesn't provide any way to grab the most recently created
repository; you can only get a repository by a repo ID. There's nothing really
special about the repo ID, it's just a number that gets incremented each time
a repo is created. So the first ever repo has the ID "1", and the 4,000th repo
has the ID "4000", etc.

|

This means we can determine the latest repo ID with a little brute force.
Requests for a non-existent ID (or a private repo that your account cannot
access) will fail, so with a simple binary search we can determine the highest
repo ID currently in use, with a fairly small number of steps. Once we have this
reference point, we can poll continuously for the next repo ID to be in use, and
in this way "watch" the stream of new repos as they are being created.

NOTE: This binary search process needs to happen each time you start poacher.
The first time you run poacher, it will take a bit longer to find the
latest repo ID (perhaps 20-30 seconds). Once the latest repo ID is found,
poacher saves it in ``conf/marker.json``, so the next start-up will be faster.

How To Use Poacher
------------------

Installation and quick test
###########################

Installation is easy. Poacher works on Linux and Windows, as long as you have
the following packages installed:

* `Python 2.7.x <https://www.python.org/downloads/release/python-2713>`_
* `Git <https://git-scm.com>`_

  * **Linux installation**: From a terminal, type ``apt-get install git``
    (Debian/Ubuntu) or ``yum install git`` (Fedora/RedHat)
  * **Windows installation**: download and install
    `Git for windows <https://git-scm.com/download/win>`_

* `PyGithub <https://github.com/PyGithub/PyGithub>`_

  * **Linux installation:** From a terminal, type ``pip install PyGithub``
  * **Windows installation:** From a terminal, type
    ``C:\Python27\Scripts\pip.exe install PyGithub``

Once you have installed the 3 items above, you can clone Poacher and test it.

::

   git clone https://github.com/eriknyquist/poacher
   cd poacher

Open the file ``conf/poacher.json`` in a text editor. It should look something
like this:

::

    {
        "working_directory": "work", 
        "archive_directory": "archive",
        "skip_empty_repos": true,
        "max_repo_size_kb": 20000,
        "repo_handler": "examples/example_handler.py",
        "github_username": "", 
        "github_password": ""
    }

Set ``github_username`` and ``github_password`` to your Github
username/password. Save the file and close it.

|

Now, it's a good idea to run poacher with the example handler, to make sure
everything is working:

::

    $> python poacher.py --verbose

    [08-06-2017 15:41:56.609] [0:00:00] poacher:> Starting binary search for latest repo ID, last ID was 99517307
    [08-06-2017 15:41:56.609] [0:00:00] poacher:> trying ID 99517341
    [08-06-2017 15:41:56.908] [0:00:00] poacher:> ID 99517341 not yet used
    [08-06-2017 15:41:56.908] [0:00:00] poacher:> 
    [08-06-2017 15:41:56.908] [0:00:00] poacher:> Beginning search between 99517307 and 99517341
    [08-06-2017 15:41:56.908] [0:00:00] poacher:> search area size: 34
    [08-06-2017 15:41:57.415] [0:00:00] poacher:> search area size: 17
    [08-06-2017 15:41:57.831] [0:00:01] poacher:> search area size: 9
    [08-06-2017 15:41:58.252] [0:00:01] poacher:> search area size: 5
    [08-06-2017 15:41:58.944] [0:00:02] poacher:> search area size: 3
    [08-06-2017 15:41:59.255] [0:00:02] poacher:> search area size: 2
    [08-06-2017 15:41:59.602] [0:00:02] poacher:> 
    [08-06-2017 15:41:59.602] [0:00:02] poacher:> 33 new repos since last check
    ...

Using Poacher
#############

You need to do 2 simple things to use your own handler with poacher:

1. Write a handler. Your handler should be a .py file that defines a ``run()``
   method, like this:

   .. code:: python

       def run(repo_path, log):
           #
           # log       : logging function. Call this to print any information
           #             that you want associated with this repo
           #
           # repo_path : absolute path to clone of the current repository
           #             on your system
           #
           # return    : bool. If True, the clone of this repository will be copied
           #             to your archive directory before continuing.

           log("Latest repository is currently cloned at %s" % repo_path)
           return True

   An example handler ``examples/example_handler.py`` is provided, in case
   you want to use it as a template

2. Open ``conf/poacher.json``, and change the value of ``repo_handler`` so it
   contains the path to the file containing your handler.

Each time a new repository appears on github.com, Poacher will clone it, and
invoke your handler, passing in the path to the cloned repository as
``repo_path``. If your handler returns ``True``, then Poacher will make a copy
of the repository in the archive directory specified in ``conf/poacher.json``.

If you go look at some clones that have been archived in your archive directory,
you'll notice that there is an extra file alongside the repository files,
called ``info.txt``. This file contains some extra information about the
repository, specifically:

* The repository's github.com URL
* The date and time the repository was created (UTC)
* Anything that your handler logged using the log() function, when it was
  invoked for this repository
