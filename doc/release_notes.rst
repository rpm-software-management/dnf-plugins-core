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


====================
0.1.21 Release Notes
====================

Set --alldeps as defaults in Repoquery plugin and added --exactdeps option.

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

Documented :doc:`repoquery` options ``--unneeded`` and ``--recent``.

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

:doc:`repoquery` was extended by newly added select options ``--srpm``, ``--alldeps``
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

Three new options were added to :doc:`repoquery`: `latest-limit`, `unsatisfied` and `resolve`.

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

:doc:`repoquery` now accepts `<pkg-spec>`.

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

:doc:`repoquery` adds `--list` switch to show files the package contains.

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

Added info switch to :ref:`repoquery <info_repoquery-label>`

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

This release provides the :doc:`repoquery` and a bugfix for the :doc:`builddep`.

Bugs fixed for 0.1.0:

* :rhbug:`1045078`
* :rhbug:`1103906`


.. _dnf plugins extras: http://dnf-plugins-extras.readthedocs.org/
