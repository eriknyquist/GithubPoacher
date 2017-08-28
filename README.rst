Github Repository Poacher
=========================

What is this?
-------------

This is a tool for Windows and Linux PCs, which polls github.com for newly
created repostories, clones them, and allows you to do something with the cloned
files. Effectively, this allows you to write a handler/script to be executed on
any newly-created Github repositories, as soon as they appear on github.com.

Why?
----

For fun. Apparently (so I've heard), some people push sensitive information to
public Github repositories by accident (some IDEs even have an integrated
'Push to new Github repo' button). Poacher is a useful tool if you want to
find out for yourself whether there's any truth in that.

|

Unfortunately, writing a program that can detect 'sensitive information' is
pretty damn tricky, so I've left that for you and just pulled together the easy
parts :)

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
* `Git <https://git-scm.com>`_ (to clone Github repositories)

  * **Linux installation**: From a terminal, type ``apt-get install git``
    (Debian/Ubuntu) or ``yum install git`` (Fedora/RedHat)
  * **Windows installation**: download and install
    `Git for windows <https://git-scm.com/download/win>`_

* `PyGithub <https://github.com/PyGithub/PyGithub>`_ (to interact with Github
  through your Github account)

  * **Linux installation**: From a terminal, type ``pip install PyGithub``
  * **Windows installation**: From the command prompt, type
    ``C:\Python27\Scripts\pip.exe install PyGithub``

* `GitPython <https://github.com/gitpython-developers/GitPython>`_ (to interact
  with the git installation on your local machine)

  * **Linux installation**: From a terminal, type ``pip install GitPython``
  * **Windows installation**: From the command prompt, type
    ``C:\Python27\Scripts\pip.exe pip install GitPython``

Once you have installed the 4 items above, you can clone Poacher and test it.

::

   git clone https://github.com/eriknyquist/GithubPoacher
   cd GithubPoacher

Now, you can run poacher by executing the ``poacher.py`` script:

 .. code-block::

    $> python poacher.py -v

                                   ./+syddmmmmdhys+:.
                               -odNMMMMMMMMMMMMMMMMMMNh+.
                            -sNMMMMMMMMMMMMMMMMMMMMMMMMMMmo`
                          :dMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMy.
                        -dMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMs`
                       +MMMMMMd..:ohMMMMMMMMMMMMMMMNy+-.-NMMMMMN:
                      yMMMMMMM/     `::-.`    `.-/-      yMMMMMMM+
                     sMMMMMMMM/                          yMMMMMMMM/
                    /MMMMMMMMM+                          yMMMMMMMMN.
                    mMMMMMMMM:                            sMMMMMMMMs
                   -MMMMMMMMs                              dMMMMMMMN
                   +MMMMMMMM:                              sMMMMMMMM-
                   oMMMMMMMM/                              yMMMMMMMM:
                   /MMMMMMMMy                              NMMMMMMMM.
                   .MMMMMMMMM:                            oMMMMMMMMm
                    yMMMMMMMMN/                         `sMMMMMMMMM/
                    .NMMMMMMMMMm+.                    :sNMMMMMMMMMh
                     -NMMM+.-sNMMMNhs+/`        .+oydNMMMMMMMMMMMm`
                      -mMMMN+ .hMMMMMM:          sMMMMMMMMMMMMMMh`
                       `yMMMMo  -osso/           `MMMMMMMMMMMMMo
                         :dMMMd:`                `MMMMMMMMMMMh.
                           :hMMMMNNNNh           `MMMMMMMMNy-
                             .+dMMMMMd           `MMMMMNh/`
                                `:ohms            hmyo-
    ::::::::::.     ...       :::.       .,-:::::    ::   .:  .,::::::  :::::::..
     `;;;```.;;; .;;;;;;;.    ;;`;;    ,;;;'````'   ,;;   ;;, ;;;;''''  ;;;;``;;;;
      `]]nnn]]' ,[[     \[[, ,[[ '[[,  [[[         ,[[[,,,[[[  [[cccc    [[[,/[[['
       $$$''    $$$,     $$$c$$$cc$$$c $$$         '$$$'''$$$  $$''''    $$$$$$c
       888o     '888,_ _,88P 888   888,`88bo,__,o,  888   '88o 888oo,__  888b '88bo,
       YMMMb      'YMMMMMP'  YMM   ''`   'YUMMMMMP' MMM    YMM '''YUMMM MMMM   'W'

    [08-27-2017 19:44:53.862] [0:00:10] poacher:> Monitor Mode (no active handler. keeping track of repository creation rate, nothing more)
    [08-27-2017 19:44:53.864] [0:00:10] poacher:> last session ended at 08-27-2017 19:44:07.000, latest repo ID was 101597215
    [08-27-2017 19:44:53.864] [0:00:10] poacher:> at 78 repos per minute, predicted current latest repo ID is at least 101597274
    [08-27-2017 19:44:53.865] [0:00:10] poacher:> Starting binary search for latest repo ID, last ID was 101597215
    [08-27-2017 19:44:53.865] [0:00:10] poacher:> trying ID 101597274
    [08-27-2017 19:44:54.189] [0:00:11] poacher:> ID 101597274 not yet used
    [08-27-2017 19:44:54.190] [0:00:11] poacher:> Beginning search between 101597215 and 101597274
    [08-27-2017 19:44:54.191] [0:00:11] poacher:> search area size: 59
    [08-27-2017 19:44:54.665] [0:00:11] poacher:> search area size: 30
    [08-27-2017 19:44:58.430] [0:00:15] poacher:> search area size: 15
    [08-27-2017 19:44:58.805] [0:00:15] poacher:> search area size: 8
    [08-27-2017 19:44:59.435] [0:00:16] poacher:> search area size: 4
    [08-27-2017 19:45:00.077] [0:00:17] poacher:> search area size: 2
    [08-27-2017 19:45:00.568] [0:00:17] poacher:> Latest repo ID is 101597269
    ...

If you see poacher start to search for the latest repository ID, like in the
log output shown above, then you're good to go.

Using Poacher
#############

You need to do 3 simple things to use your own handler with poacher:

1. Write a handler. Your handler should be a .py file that defines a ``run()``
   method, like this:

   .. code:: python

       def run(repo_path, repo, log):
           #
           # repo_path : absolute path to clone of the current repository
           #             on your system. If the repository is not cloned for any
           #             reason (running in monitor mode, repository is too big
           #             to clone, "clone" set to false in the configuration
           #             file), then repo_path will be set to None.
           #
           # repo      : the Repository object provided by PyGithub. See
           #             http://pygithub.readthedocs.io/en/latest/github_objects/Repository.html
           #
           # log       : logging function. Call this to print any information
           #             that you want associated with this repo
           #
           # return    : bool. If True, the clone of this repository will be copied
           #             to your archive directory before continuing.

           log("latest repository: %s" % repo.full_name)

           if repo_path != None:
               log("cloned at %s" % repo_path)

           return True

   An example handler ``examples/example_handler.py`` is provided, in case
   you want to use it as a template

2. Open ``conf/poacher.json``, and change the value of ``repo_handler`` so it
   contains the path to the file containing your handler.

3. Also in ``conf/poacher.json``, make sure that ``monitor_only`` is set to
   ``false``, otherwise your handler will not run.

That's it. Now you can run poacher, and verify that your handler is loaded by
looking for message like this in the log output:

::

     [08-06-2017 18:43:53.588] [0:00:00] poacher:> Using handler example_handler

Each time a new repository appears on github.com, Poacher will clone it, and
invoke your handler, passing in the path to the cloned repository as
``repo_path``.  ``repo`` is a
`PyGithub Repository object <http://pygithub.readthedocs.io/en/latest/github_objects/Repository.html>`_.
If your handler returns ``True``, then Poacher will make a copy
of the repository in the archive directory specified in ``conf/poacher.json``.

If you go look at some clones that have been archived in your archive directory,
you'll notice that there is an extra file alongside the repository files,
called ``info.txt``. This file contains some extra information about the
repository, specifically:

* The repository's github.com URL
* The date and time the repository was created (UTC)
* Anything that your handler logged using the log() function, when it was
  invoked for this repository

Poacher configuration
---------------------

A description of configurable parameters in ``conf/poacher.json`` follows

  | **Name**: ``working_directory``
  | **Type**: string
  | **Description**: path to the directory where poacher will temporarily clone
  | repositories

|

  | **Name**: ``archive_directory``
  | **Type**: string
  | **Description**: path to the directory where poacher will put archived 
  | repositories

|

  | **Name**: ``skip_empty_repos``
  | **Type**: bool
  | **Description**: if true, poacher will not download repositories with a
  | size of 0

|

  | **Name**: ``max_repo_size_kb``
  | **Type**: integer
  | **Description**: size limit in kilobytes. Poacher will not download repos
  | larger than this, and pass 'None' to your handler in place of the clone path

|

  | **Name**: ``monitor_only``
  | **Type**: bool
  | **Description**: if true, poacher will not download any repositories, or
  | run any handlers, effectively just keeping track of the repo creation rate.
  | This setting overrides the values of ``clone`` and ``repo_handler``: you'll
  | need to make sure the ``monitor_only`` is set to ``false`` if you want to
  | set ``clone`` or ``repo_handler``.

|

  | **Name**: ``poll_delay_seconds``
  | **Type**: float
  | **Description**: time (in seconds) to sleep between Github requests while
  | polling for new repositories

|

  | **Name**: ``github_retries``
  | **Type**: integer
  | **Description**: number of times to retry a failed Github request before
  | quitting poacher (0 means never stop retrying)

|

  | **Name**: ``github_retry_delay_seconds``
  | **Type**: float
  | **Description**: time (in seconds) to sleep between retrying failed Github
  | requests

|

  | **Name**: ``clone``
  | **Type**: bool
  | **Description**: if true, each new repository will be cloned, and the path
  | to the cloned repository will be passed to your handler, if defined.
  | Otherwise (set to false), repositories will not be cloned and your handler
  | will be passed 'None' in place of the clone path.

|

  | **Name**: ``repo_handler``
  | **Type**: string
  | **Description**: path to the .py file containing the handler that should be
  | called when a new repository is created. If ``repo_handler`` is not defined,
  | or if an invalid file is provided, then poacher will automatically switch
  | to monitor mode (``monitor_only = true``)

|

  | **Name**: ``github_username``
  | **Type**: string
  | **Description**: username for the Github account that will be used for
  | authentication. If not set, you will be prompted to type a username at the
  | terminal when poacher starts

|

  | **Name**: ``github_password``
  | **Type**: string
  | **Description**: password for the Github account that will be used for
  | authentication. If not set, you will be prompted to type a password at the
  | terminal when poacher starts
