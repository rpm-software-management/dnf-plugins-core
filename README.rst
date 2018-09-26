##################
 Core DNF Plugins
##################

Core plugins to use with `DNF package manager <https://github.com/rpm-software-management/dnf>`_.

==============
 Installation
==============

RPM packages are available in official Fedora repositories::

   dnf install dnf-plugins-core

Nigthly builds can be installed from `copr repository <https://copr.fedorainfracloud.org/coprs/rpmsoftwaremanagement/dnf-nightly/>`_.


======================
 Building from source
======================

From the DNF git checkout directory::

    mkdir build;
    pushd build;
    cmake .. && make;
    popd;

Then to run DNF::

    PYTHONPATH=`readlink -f .` bin/dnf <arguments>

===============
 Running tests
===============

From the DNF git checkout directory::

    mkdir build;
    pushd build;
    cmake .. && make ARGS="-V" test;
    popd;

==============
 Contribution
==============

Here's the most direct way to get your work merged into the project.

1. Fork the project
#. Clone down your fork
#. Implement your feature or bug fix and commit changes
#. If you reported a bug or you know it fixes existing bug at `Red Hat bugzilla <https://bugzilla.redhat.com/>`_, append ``(RhBug:<bug_id>)`` to your commit message
#. In special commit add your name and email under ``DNF-PLUGINS-CORE CONTRIBUTORS`` section in `authors file <https://github.com/rpm-software-management/dnf-plugins-core/blob/master/AUTHORS>`_ as a reward for your generosity
#. Push the branch up to your fork
#. Send a pull request for your branch

Please, do not create the pull requests with translation (.po) files improvements. Fix the translation on `Zanata <https://fedora.zanata.org/iteration/view/dnf-plugins-core/master>`_ instead.

===============
 Documentation
===============

The DNF-PLUGINS-CORE package distribution contains man pages ``dnf.plugin.*(8)``. It is also possible to read the `DNF-PLUGINS-CORE documentation <http://dnf-plugins-core.readthedocs.org>`_ online.

====================
 Bug reporting etc.
====================

Please report discovered bugs to the `Red Hat bugzilla <https://bugzilla.redhat.com/>`_ following this `guide <https://github.com/rpm-software-management/dnf/wiki/Bug-Reporting>`_. If you planed to propose the patch in the report, consider `contribution`_ instead.

Freenode's irc channel ``#yum`` is meant for discussions related to both Yum and DNF. Questions should be asked there, issues discussed. Remember: ``#yum`` is not a support channel and prior research is expected from the questioner.
