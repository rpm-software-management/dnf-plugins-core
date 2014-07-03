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

===============================
 DNF protected_packages Plugin
===============================

-----------
Description
-----------

Prevents any DNF operation that would result in a removal of one of the protected packages from the system. These are typically packages essential for proper system boot and basic operation.

-------------
Configuration
-------------

Deciding whether a package is protected is based on the package name. The set of packages names considered protected is loaded from configuration files under::

  /etc/dnf/protected.d
  /etc/yum/protected.d

Every line in all ``*.conf`` files there is taken as a protected package name. Moreover, the currently booted kernel package is always protected.

Complete disabling of the protected packages feature is done by disabling the plugin::

  dnf --disableplugin=protected_packages erase dnf
