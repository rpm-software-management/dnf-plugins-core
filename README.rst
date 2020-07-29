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
#. If the change fixes a bug at `Red Hat bugzilla <https://bugzilla.redhat.com/>`_, or if it is important to the end user, add the following block to the commit message::

    = changelog =
    msg:           message to be included in the changelog
    type:          one of: bugfix/enhancement/security (this field is required when message is present)
    resolves:      URLs to bugs or issues resolved by this commit (can be specified multiple times)
    related:       URLs to any related bugs or issues (can be specified multiple times)

   * For example::

       = changelog =
       msg: [download] Respect repo priority
       type: bugfix
       resolves: https://bugzilla.redhat.com/show_bug.cgi?id=1800342

   * For your convenience, you can also use git commit template by running the following command in the top-level directory of this project::

       git config commit.template ./.git-commit-template

#. In a separate commit, add your name and email under ``DNF-PLUGINS-CORE CONTRIBUTORS`` section in the `authors file <https://github.com/rpm-software-management/dnf-plugins-core/blob/master/AUTHORS>`_ as a reward for your generosity
#. Push the branch up to your fork
#. Send a pull request for your branch

Please do not create pull requests with translation (.po) file improvements. Fix the translation on `Fedora Weblate <https://translate.fedoraproject.org/projects/dnf/>`_ instead.

===============
 Documentation
===============

The DNF-PLUGINS-CORE package distribution contains man pages ``dnf.plugin.*(8)``. It is also possible to read the `DNF-PLUGINS-CORE documentation <http://dnf-plugins-core.readthedocs.org>`_ online.

====================
 Bug reporting etc.
====================

Please report discovered bugs to the `Red Hat bugzilla <https://bugzilla.redhat.com/>`_ following this `guide <https://github.com/rpm-software-management/dnf/wiki/Bug-Reporting>`_. If you planed to propose the patch in the report, consider `contribution`_ instead.

Freenode's irc channel ``#yum`` is meant for discussions related to both Yum and DNF. Questions should be asked there, issues discussed. Remember: ``#yum`` is not a support channel and prior research is expected from the questioner.
