###################
 Core DNF Plugins
###################

Experimental plugins to use with `DNF <https://github.com/akozumpl/dnf>`_.


Install
========

To install the plugins, run the followings as **root**

::

    make install


Build RPM
==========
to build RPM's use the following command

::
    make rpms

You need to have all rpmbuild & all build requirments installed.


Run Unit Tests
==============
Do run unit tests using a dnf git checkout

::
    make DNF_LIBPATH=<path to dnf checkout> run-tests


Example:

if you have a dnf git checkout in ~/udv/tmp/dnf

use this command to run the unit tests

::
    make DNF_LIBPATH=~/udv/tmp/dnf run-tests


Check the DNF build from source  
`instructions <https://github.com/akozumpl/dnf>`_
for how to build a DNF checkout



