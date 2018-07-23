..
  Copyright (C) 2014  Red Hat, Inc.

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

##############################
Core DNF Plugins Release Notes
##############################

.. contents::

===================
3.0.2 Release Notes
===================

Bugs fixed in 3.0.2:

* :rhbug:`1603805`
* :rhbug:`1571251`

===================
3.0.1 Release Notes
===================

* Enhanced documentation

Bugs fixed in 3.0.1:

* :rhbug:`1576594`
* :rhbug:`1530081`
* :rhbug:`1547897`
* :rhbug:`1550006`
* :rhbug:`1431491`
* :rhbug:`1516857`
* :rhbug:`1499623`
* :rhbug:`1489724`

===================
2.1.5 Release Notes
===================

Bugs fixed in 2.1.5:

* :rhbug:`1498426`

===================
2.1.4 Release Notes
===================

* Added four new options for ``list`` subcommand of ``copr`` plugin

Bugs fixed in 2.1.4:

* :rhbug:`1476834`

===================
2.1.3 Release Notes
===================

Bugs fixed in 2.1.3:

* :rhbug:`1470843`
* :rhbug:`1279001`
* :rhbug:`1439514`

===================
2.1.2 Release Notes
===================

* :doc:`copr` doesn't crash anymore in some circumstances.
* :doc:`debuginfo-install` doesn't install any additional subpackages anymore,
  previously it was trying to get all dependent packages recursively and install
  debuginfo packages for them.

Bugs fixed in 2.1.2:

* :rhbug:`1322599`

===================
2.1.1 Release Notes
===================

It introduces new behavior of Versionlock plugin where it doesn't apply any excludes in non-transactional operations like `repoquery`, `list`, `info`, etc.

Bugs fixed in 2.1.1:

* :rhbug:`1458446`

===================
2.1.0 Release Notes
===================

Additional subpackage in 2.1.0:

* Added new subpackage ``dnf-utils`` that provides binaries originaly provided by ``yum-utils``.

Bugs fixed in 2.1.0:

* :rhbug:`1381917`

===================
2.0.0 Release Notes
===================

* Added ``DEBUG`` plugin from dnf-plugins-extras
* Added ``LEAVES`` plugin from dnf-plugins-extras
* Added ``LOCAL`` plugin from dnf-plugins-extras
* Added ``MIGRATE`` plugin from dnf-plugins-extras
* Added ``NEEDS RESTARTING`` plugin from dnf-plugins-extras
* Added ``REPOCLOSURE`` plugin from dnf-plugins-extras
* Added ``REPOGRAPH`` plugin from dnf-plugins-extras
* Added ``REPOMANAGE`` plugin from dnf-plugins-extras
* Added ``SHOW LEAVES`` plugin from dnf-plugins-extras
* Added ``VERSIONLOCK`` plugin from dnf-plugins-extras

===================
1.1.0 Release Notes
===================

* Updated translations
* :doc:`builddep` doesn't check GPG key of src.rpm anymore
* :doc:`builddep` installs dependencies by provides
* :doc:`download` with ``--resolve`` now downloads all needed packages for transaction

Bugs fixed in 1.1.0:

* :rhbug:`1429087`
* :rhbug:`1431486`
* :rhbug:`1332830`
* :rhbug:`1276611`

===================
1.0.2 Release Notes
===================

Newly implemented :doc:`download` options ``--url`` and ``--urlprotocol``.

Bugs fixed in 1.0.2:

* :rhbug:`1250115`

===================
1.0.1 Release Notes
===================

Minor changes in builddep: print errors from RPM SPEC parser

===================
1.0.0 Release Notes
===================

`Repoquery  <https://dnf.readthedocs.org/en/latest/command_ref.html#repoquery_command-label>`_ and
`protected_packages <dnf.readthedocs.io/en/latest/conf_ref.html>`_ plugins were integrated into DNF.

Bugs fixed in 1.0.0:

* :rhbug:`1361003`
* :rhbug:`1360752`
* :rhbug:`1350604`
* :rhbug:`1325350`
* :rhbug:`1303117`
* :rhbug:`1193823`
* :rhbug:`1260986`

====================
0.1.21 Release Notes
====================

Bugfixes, internal improvements.

Bugs fixed in 0.1.21:

* :rhbug:`1335959`
* :rhbug:`1279538`
* :rhbug:`1303311`

====================
0.1.20 Release Notes
====================

Small fixes in COPR plugin, added ``get_reposdir`` function to dnfpluginscore lib.

====================
0.1.18 Release Notes
====================

Changed COPR server adress to the new one.

====================
0.1.17 Release Notes
====================

Added configuration file for :doc:`debuginfo-install`.


Bugs fixed in 0.1.17:

* :rhbug:`1024701`
* :rhbug:`1302214`

====================
0.1.16 Release Notes
====================

Documented `DNF repoquery <https://dnf.readthedocs.org/en/latest/command_ref.html#repoquery_command-label>`_ options ``--unneeded`` and ``--recent``.

Bugs fixed in 0.1.16:

* :rhbug:`1297511`
* :rhbug:`1292475`

====================
0.1.15 Release Notes
====================

Newly implemented :doc:`download` options ``--resolve`` and ``--debuginfo``.

Improved the start-up time of bash completion.

Reviewed documentation.

Bugs fixed in 0.1.15:

* :rhbug:`1283448`
* :rhbug:`1253237`

=====================
 0.1.14 Release Notes
=====================

Bugs fixed in 0.1.14:

* :rhbug:`1231572`
* :rhbug:`1265210`
* :rhbug:`1280416`
* :rhbug:`1270091`
* :rhbug:`1272936`

=====================
 0.1.13 Release Notes
=====================

Kickstart plugin has been moved to `dnf plugins extras`_ as a separate ``python-dnf-plugins-extras-kickstart`` package.

Bugs fixed in 0.1.13:

* :rhbug:`1267808`
* :rhbug:`1264125`
* :rhbug:`1265622`
* :rhbug:`1159614`

=====================
 0.1.12 Release Notes
=====================

Added support of globs to ``--whatrequires`` and ``--whatprovides`` options.

Bugs fixed in 0.1.12:

* :rhbug:`1249073`

=====================
 0.1.11 Release Notes
=====================

Option ``--arch`` now accepts more than one architecture.

Introduced select options ``--available``, ``--extras``, ``--installed``, ``--upgrades``.

Added ability to use weak dependencies query options in combination with ``--tree`` switch.

Bugs fixed in 0.1.11:

* :rhbug:`1250114`
* :rhbug:`1186381`
* :rhbug:`1225784`
* :rhbug:`1233728`
* :rhbug:`1199601`
* :rhbug:`1156778`

=====================
 0.1.10 Release Notes
=====================

:doc:`builddep` was extended by newly added options ``--srpm`` and ``--spec`` for specifying the input file.

Implemented ``remove`` command in :doc:`copr` plugin.

Bugs fixed in 0.1.10:

* :rhbug:`1226663`
* :rhbug:`1184930`
* :rhbug:`1234099`
* :rhbug:`1241126`
* :rhbug:`1218299`
* :rhbug:`1241135`
* :rhbug:`1244125`


====================
 0.1.9 Release Notes
====================

`DNF repoquery <https://dnf.readthedocs.org/en/latest/command_ref.html#repoquery_command-label>`_ was extended by newly added select options ``--srpm``, ``--alldeps``
and query option ``--tree``.

Bugs fixed in 0.1.9:

* :rhbug:`1128425`
* :rhbug:`1186382`
* :rhbug:`1228693`
* :rhbug:`1186689`
* :rhbug:`1227190`

====================
 0.1.8 Release Notes
====================

This release fixes only packaging issues.

====================
 0.1.7 Release Notes
====================

All occurrences of `repoid` option were replaced by `repo` to unified repository specification in plugins.

:doc:`builddep` now accepts packages from repositories as arguments and allows users
to define RPM macros used during spec files parsing via `-D` option.

Three new options were added to `DNF repoquery <https://dnf.readthedocs.org/en/latest/command_ref.html#repoquery_command-label>`_: `latest-limit`, `unsatisfied` and `resolve`.

Bugs fixed in 0.1.7:

* :rhbug:`1215154`
* :rhbug:`1074585`
* :rhbug:`1156487`
* :rhbug:`1208773`
* :rhbug:`1186948`

====================
 0.1.6 Release Notes
====================

Newly implemented :doc:`config_manager` plugin.

`DNF repoquery <https://dnf.readthedocs.org/en/latest/command_ref.html#repoquery_command-label>`_ now accepts `<pkg-spec>`.

Bugs fixed in 0.1.6:

* :rhbug:`1208399`
* :rhbug:`1194725`
* :rhbug:`1198442`
* :rhbug:`1193047`
* :rhbug:`1196952`
* :rhbug:`1171046`
* :rhbug:`1179366`

====================
 0.1.5 Release Notes
====================

:doc:`builddep` accepts also `nosrc.rpm` package.

`DNF repoquery <https://dnf.readthedocs.org/en/latest/command_ref.html#repoquery_command-label>`_ adds `--list` switch to show files the package contains.

Bugs fixed in 0.1.5:

* :rhbug:`1187773`
* :rhbug:`1178239`
* :rhbug:`1166126`
* :rhbug:`1155211`

====================
 0.1.4 Release Notes
====================

Provides :doc:`needs_restarting` and :doc:`reposync`.

Bugs fixed in 0.1.4:

* :rhbug:`1139738`
* :rhbug:`1144003`

====================
 0.1.3 Release Notes
====================

Added info switch to `DNF repoquery <https://dnf.readthedocs.org/en/latest/command_ref.html#info_repoquery-label>`_

Bugs fixed in 0.1.3:

* :rhbug:`1135984`
* :rhbug:`1134378`
* :rhbug:`1123886`

====================
 0.1.2 Release Notes
====================

Bugs fixed in 0.1.2:

* :rhbug:`1108321`
* :rhbug:`1116389`
* :rhbug:`1118809`

====================
 0.1.1 Release Notes
====================

Provides :doc:`protected_packages` and a bugfix to the Copr plugin.

Bugs fixed in 0.1.1:

* :rhbug:`1049310`
* :rhbug:`1104088`
* :rhbug:`1111855`

====================
 0.1.0 Release Notes
====================

This release provides the `DNF repoquery <https://dnf.readthedocs.org/en/latest/command_ref.html#repoquery_command-label>`_ and a bugfix for the :doc:`builddep`.

Bugs fixed for 0.1.0:

* :rhbug:`1045078`
* :rhbug:`1103906`


.. _dnf plugins extras: http://dnf-plugins-extras.readthedocs.org/
