..
  Copyright (C) 2019 Red Hat, Inc.

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

===================================
DNF post-transaction-actions Plugin
===================================

-----------
Description
-----------

The plugin allows to define actions to be executed upon completing an RPM transaction. Each action
may define a (glob-like) filtering rule on the package NEVRA or package files, as well as whether
the package was installed or removed. Actions are defined in action files.

-------------
Configuration
-------------

The plugin configuration is in ``/etc/dnf/plugins/post-transaction-actions.conf``. All configuration
options are in the ``[main]`` section.

``enabled``
    Whether the plugin is enabled. Default value is ``True``.

``actiondir``
    Path to the directory with action files. Action files must have the ".action" extension.
    Default value is "/etc/dnf/plugins/post-transaction-actions.d/".

------------------
Action file format
------------------

Empty lines and lines that start with a '#' character are ignored.
Each non-comment line defines an action and consists of three items separated by colons:
``package_filter:transaction_state:command``.

``package_filter``
   A (glob-like) filtering rule applied on the package NEVRA (also in the shortened forms) or
   package files.

``transaction_state``
   Filters packages according to their state in the transaction.

   * ``in`` - packages that appeared on the system (downgrade, install, obsolete, reinstall, upgrade)
   * ``out`` - packages that disappeared from the system (downgraded, obsoleted, remove, upgraded)
   * ``any`` - all packages

``command``
   Any shell command.
   The following variables in the command will be substituted:
      * ``${name}``, ``$name`` - package name
      * ``${arch}``, ``$arch`` - package arch
      * ``${ver}``, ``$ver`` - package version
      * ``${rel}``, ``$rel`` - package release
      * ``${epoch}``, ``$epoch`` - package epoch
      * ``${repoid}``, ``$repoid`` - package repository id
      * ``${state}``, ``$state`` - the change of package state in the transaction:
         "downgrade", "downgraded", "install", "obsolete", "obsoleted", "reinstall",
         "reinstalled", "remove", "upgrade", "upgraded"

   The shell command will be evaluated for each package that matched the ``package_filter`` and
   the ``transaction_state``. However, after variable substitution, any duplicate commands will be
   removed and each command will only be executed once per transaction. The order of execution
   of the commands follows the order in the action files, but may differ from the order of
   packages in the transaction.  In other words, when you define several action lines for the
   same ``package_filter`` these lines will be executed in the order they were defined in the
   action file when the ``package_filter`` matches a package during the ``trasaction_state`` state.
   However, the order of when a particular ``package_filter`` is invoked depends on the position
   of the corresponding package in the transaction.

An example action file:
^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: none

   # log all packages (state, nevra, repo) in transaction into a file.
   *:any:echo '${state} ${name}-${epoch}:${ver}-${rel}.${arch} repo ${repoid}' >>/tmp/post-trans-actions-trans.log

   # The same shell command (after variables substitution) is executed only once per transaction.
   *:any:echo '${repoid}' >>/tmp/post-trans-actions-repos
   # will write each repo only once to /tmp/post-trans-actions-repos, even if multiple packages from
   # the same repo were matched
