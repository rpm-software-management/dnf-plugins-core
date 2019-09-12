..
  Copyright (C) 2015  Red Hat, Inc.

  This copyrighted material is made available to anyone wishing to use,
  modify, copy, or redistribute it subject to the terms and conditions of
  the GNU General Public License v.2, or (at your option) any later version.
  This program is distributed in the hope that it will be useful, but WITHOUT
  ANY WARRANTY expressed or implied, including the implied warranties of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
  Public License for more details.  You should have received a copy of the
  GNU General Public License along with this program; if not, write to the
  Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
  02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
  source code or documentation are not subject to the GNU General Public
  License and may only be used or replicated with the express permission of
  Red Hat, Inc.

==========================
 DNF config-manager Plugin
==========================

Manage main and repository DNF configuration options, toggle which
repositories are enabled or disabled, and add new repositories.

--------
Synopsis
--------

``dnf config-manager [options] <section>...``

---------
Arguments
---------

``<section>``
    This argument can be used to explicitly select the configuration sections to manage.
    A section can either be ``main`` or a repoid.
    If not specified, the program will select the ``main`` section and each repoid
    used within any ``--setopt`` options.
    A repoid can be specified using globs.

-------
Options
-------

All general DNF options are accepted, see `Options` in :manpage:`dnf(8)` for details.

``--help-cmd``
    Show this help.

``--add-repo=URL``
    Add (and enable) the repo from the specified file or url. If it has to be added into installroot, combine it with
    ``--setopt=reposdir=/<installroot>/etc/yum.repos.d`` command-line option.

``--dump``
    Print dump of current configuration values to stdout.

``--set-disabled``, ``--disable``
    Disable the specified repos (implies ``--save``).

``--set-enabled``, ``--enable``
    Enable the specified repos (implies ``--save``).

``--save``
    Save the current options (useful with ``--setopt``).

``--setopt=<option>=<value>``
    Set a configuration option. To set configuration options for repositories, use
    ``repoid.option`` for the ``<option>``. Globs are supported in repoid.

--------
Examples
--------
``dnf config-manager --add-repo http://example.com/some/additional.repo``
    Download additional.repo and store it in repodir.

``dnf config-manager --add-repo http://example.com/different/repo``
    Create new repo file with http://example.com/different/repo as baseurl and enable it.

``dnf config-manager --dump``
    Display main DNF configuration.

``dnf config-manager --dump <section>``
    Display configuration of a repository identified by <section>.

``dnf config-manager --set-enabled <repoid>``
    Enable repository identified by <repoid> and make the change permanent.

``dnf config-manager --save --setopt=*.proxy=http://proxy.example.com:3128/ <repo1> <repo2>``
    Update proxy setting in repositories with repoid <repo1> and <repo2> and make the change
    permanent.

``dnf config-manager --save --setopt=*-debuginfo.gpgcheck=0``
    Update gpgcheck setting in all repositories whose id ends with -debuginfo and make the change permanent.
