Poacher
=======

Poacher polls github.com for newly created repositories, allowing you to obtain
the URLs (or any other information provided by the Github API) for all new
public repositories as they are created.

Installation
------------

Install using pip:

::

    pip install poacher

Documentation
-------------

Full documentation for poacher Python API is here `<https://poacher.readthedocs.io>`_

Why?
----

For fun. It's not something the Github API explicitly provides, and it's a bit
of a hack.

How does it work?
-----------------

The Github API only allows you to fetch information about a specific repository
by passing the repository ID, or of course the repository URL, however we're
interested in the ID in this case. There's nothing really special about the
repo ID, it's just a number that gets incremented each time a repo is created.
So the first ever repo has the ID "1", and the 4,000th repo has the ID "4000",
etc.

|

This means we can determine the latest repo ID with a little brute force.
Requests for a non-existent ID (or a private repo that your account cannot
access) will fail, so with a simple binary search we can determine the highest
repo ID currently in use, with a fairly small number of steps. Once we have this
reference point, we can poll continuously for the next repo ID to be in use, and
in this way "watch" the stream of new repos as they are being created.

Casual command-line usage
-------------------------

An example command-line program using poacher, ``poacher-monitor`` is provided
with this package. ``poacher-monitor`` will print the clone URLs of new public
repositories on github.com as they are created. Basic usage looks like this;

::

    $> poacher-monitor

    Github username: eriknyquist
    Github password:

    https://github.com/chungbinkley/ch09-builderimage.git
    https://github.com/zhonghuihuo/JavaCardAppletBasics.git
    https://github.com/hlp2002/BaiduyunSpider.git
    https://github.com/Alex-X-W/Misc-Projects.git
    https://github.com/haimli/javacsv.git
    https://github.com/NazarMykhailechko/crm_corporate.git
    https://github.com/DEVHARAM/blockchain.git
    https://github.com/meitesi/get-docker.git
    https://github.com/criverso/Resumeportfolio.git
    https://github.com/macman178/binance-api-node.git

Or, pass your username and password as arguments instead:

::

    $> poacher-monitor -u github-username -p github-password

``poacher-monitor`` has several command-line options. To see a full
description of all options, run ``poacher-monitor -h``
