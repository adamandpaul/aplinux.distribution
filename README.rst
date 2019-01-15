===========================
AP Linux Distribution Tools
===========================

aplinx.distribution is part of the aplinux suite. It focuses on the building and
distribution of aplinux into any given environment.

Getting Started
===============

Follow the steps below to run a local copy of the application stack. You will need
Python 3.6 installed on your system as well as the standard set of build tools.

1. Using a Linux or Mac OS terminal clone the source code from the repository using git::

       git clone git@example.org:adamandpaul/aplinux.distribution.git

2. Change directory to be inside the source::

       cd aplinx.distribution

3. Run the bootstrapping script substituting the location of the bin directory of your python installation::

       PATH=/path/to/python3.6/bin:$PATH bin/bootstrap

4. Run the build script::

       bin/build

   This may take some time.

Subsequent builds can be achieved by running ``bin/build`` or ``bin/build -N`` if you want to use buildout's
non-newest mode (this is faster for minor buildout or dependency changes because it uses cached buildout information)


Development tools
=================

Test runner:

    Run ``bin/test``

    Tests will be auto discovered from files ending in ``_test.py``

    To run the more expensive integration tests which end in ``_inttest.py``
    specify the integration test suite by running ``bin/test --test-suite integration_test_suite``

Code quality tests:
    Run ``bin/code-analysis``. Be aware that this is also run as a git pre-commit
    hook and code which does not conform will prevent git commits.

Test coverage reporting:
    Run ``bin/createcoverage``


The Application Environment/Stack
=================================

The built environment uses the ``zc.buildout`` package to:

1. Check out source dependencies

2. Develop and install this repository as a python package

3. Build applications that are required in the environment, for example PostgreSQL or Redis

4. Build ConfigParser style python configuration files, for logging configuration and application
   configuration.

5. Build stack running and monitoring tools and their configuration. Currently supervisord is used.

Various deployments/builds should be somewhat identical - only varying by confidential keys
which may be injected into a production environment but each build has two modes of operating. The
``develop`` mode and the ``production`` mode. Mode specific scripts are built in the ``bin`` directory
and are prefixed by ``develop-`` or ``production-`` respectively. For python configuration there are also
two ``.ini`` scripts which are built in the root directory  ``develop.ini`` and ``production.ini``. These
scripts should not be edited directly but modified using the buildout configuration by extending the sections
``[configuration]``, ``[develop.ini]`` or ``[production.ini]``.

Generally speaking the develop environment uses self contained applications and is heavier to run, whilst
the production environment will be dependent on other systems external to the buildout environment
specified here. For example, the develop environment may use the postgresql built as part of the buildout,
whilst the production environment may use the postgresql distributed with the operating system or provided
by an external service. The reason behind this is that in a production environment externally managed services
are often far better supported than applications built individually in an environment, whilst in a development
environment security patches and uptime monitoring aren't needed but having multiple development
environments co-exist together is often required.


Folder Contents
===============

``docs/``
  The documentation source. After building this will be compiled``
  to in the directory ``buildout/parts/docs``

``buildout/``
  The buildout environment and configuration.

``aplinux.distribution``
  The package source code as a python module

``var/``
  Created during buildout. Variable application data such as databases etc.
