..
  Copyright (C) 2015 Emil Renner Berthing

  This copyrighted material is made available to anyone wishing to use,
  modify, copy, or redistribute it subject to the terms and conditions of
  the GNU General Public License v.2, or (at your option) any later version.
  This program is distributed in the hope that it will be useful, but WITHOUT
  ANY WARRANTY expressed or implied, including the implied warranties of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
  Public License for more details.

==================
DNF leaves Plugin
==================

List installed packages not required by any other installed package.

--------
Synopsis
--------

``dnf leaves``

-----------
Description
-----------

`leaves` lists all the packages installed on your system which are not required as a dependency of another installed package. However two or more packages might depend on eachother in a dependency cycle. Packages in such cycles, which are not required by any other package, are also listed.

-------------------
Why is this useful?
-------------------

The list gives you a nice overview of what is installed on your system without flooding you with anything required by the packages already shown.
The following list of arguments basically says the same thing in different ways:

* All the packages on this list is either needed by you, other users of the system or not needed at all -- if it was required by another installed package it would not be on the list.
* If you want to uninstall anything from your system (without breaking dependencies) it must involve at least one package on this list.
* If there is anything installed on the system which is not needed it must be on this list -- otherwise it would be required as a dependency by another package.

