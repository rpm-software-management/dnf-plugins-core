# repomanage.py
# DNF plugin adding a command to manage rpm packages from given directory.
#
# Copyright (C) 2015 Igor Gnatenko
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#

from __future__ import absolute_import
from __future__ import unicode_literals

import dnf
import dnf.cli
import dnfpluginscore
import os
import rpm

_ = dnfpluginscore._
logger = dnfpluginscore.logger

class RepoManage(dnf.Plugin):

    name = "repomanage"

    def __init__(self, base, cli):
        super(RepoManage, self).__init__(base, cli)
        if cli is None:
            return
        cli.register_command(RepoManageCommand)


class RepoManageCommand(dnf.cli.Command):
    aliases = ("repomanage",)
    summary = _("""
    manage a directory of rpm packages. returns lists of newest
    or oldest packages in a directory for easy piping to xargs
    or similar programs""")
    usage = "[--old] [--new] path"

    def __init__(self, args):
        super(RepoManageCommand, self).__init__(args)
        self.opts = None

    def configure(self, args):
        self.opts = self._parse_args(args)

    def run(self, _):
        if self.opts.new and self.opts.old:
            raise dnf.exceptions.Errror(_("Pass either --old or --new, not both!"))

        rpm_list = []
        rpm_list = self._get_file_list(self.opts.path, ".rpm")
        verfile = {}
        # hold all of them - put them in (n, a) = [(e, v, r),(e1, v1, r1)]
        pkgdict = {}

        keepnum = int(self.opts.keep)*(-1) # the number of items to keep

        if len(rpm_list) == 0:
            raise dnf.exceptions.Error(_("No files to process"))

        ts = rpm.TransactionSet()
        if self.opts.nocheck:
            ts.setVSFlags(~(rpm._RPMVSF_NOPAYLOAD))
        else:
            ts.setVSFlags(~(rpm.RPMVSF_NOMD5|rpm.RPMVSF_NEEDPAYLOAD))
        for pkg in rpm_list:
            try:
                hdr = self.hdrFromPackage(ts, pkg)
            except dnf.exceptions.Error as e:
                logger.warning("Error opening pkg {}: {}".format(pkg, str(e)))
                continue

            pkgtuple = self.pkgTupleFromHeader(hdr)
            (n, a, e, v, r) = pkgtuple
            del hdr

            if (n, a) not in pkgdict:
                pkgdict[(n, a)] = []
            pkgdict[(n, a)].append((e, v, r))

            if pkgtuple not in verfile:
                verfile[pkgtuple] = []
            verfile[pkgtuple].append(pkg)

        for natup in pkgdict.keys():
            evrlist = pkgdict[natup]
            if len(evrlist) > 1:
                evrlist = self.unique(evrlist)
                evrlist.sort(self.compareEVR)
                pkgdict[natup] = evrlist

        del ts

        # now we have our dicts - we can return whatever by iterating over them

        outputpackages = []

        #if new
        if not self.opts.old:
            for (n, a) in pkgdict.keys():
                evrlist = pkgdict[(n, a)]

                if len(evrlist) < abs(keepnum):
                    newevrs = evrlist
                else:
                    newevrs = evrlist[keepnum:]

                for (e, v, r) in newevrs:
                    for pkg in verfile[(n, a, e, v, r)]:
                        outputpackages.append(pkg)

        if self.opts.old:
            for (n, a) in pkgdict.keys():
                evrlist = pkgdict[(n, a)]

                if len(evrlist) < abs(keepnum):
                    continue

                oldevrs = evrlist[:keepnum]
                for (e, v, r) in oldevrs:
                    for pkg in verfile[(n, a, e, v, r)]:
                        outputpackages.append(pkg)

        outputpackages.sort()
        for pkg in outputpackages:
            if self.opts.space:
                print("{} ".format(pkg))
            else:
                print(pkg)

    @staticmethod
    def _parse_args(args):
        alias = RepoManageCommand.aliases[0]
        parser = dnfpluginscore.ArgumentParser(alias)
        parser.add_argument("-o", "--old", action="store_true",
                            help=_("Print the older packages"))
        parser.add_argument("-n", "--new", action="store_true",
                            help=_("Print the newest packages"))
        parser.add_argument("-s", "--space", action="store_true",
                            help=_("Space separated output, not newline"))
        parser.add_argument("-k", "--keep", action="store", metavar="KEEP",
                            help=_("Newest N packages to keep - defaults to 1"),
                            default=1)
        parser.add_argument("-c", "--nocheck", action="store_true", 
                            help=_("do not check package payload signatures/digests"))
        parser.add_argument("path", action="store",
                            help=_("Path to directory"))

        return parser.parse_args(args)

    @staticmethod
    def _get_file_list(path, ext):
        """Return all files in path matching ext

        return list object
        """
        filelist = []
        for root, dirs, files in os.walk(path):
            for f in files:
                if os.path.splitext(f)[1].lower() == str(ext):
                    filelist.append(os.path.join(root, f))

        return filelist

    @staticmethod
    def hdrFromPackage(ts, package):
        """hand back the rpm header or raise an Error if the pkg is fubar"""
        try:
            fdno = os.open(package, os.O_RDONLY)
        except OSError as e:
            raise dnf.exceptions.Error(_("Unable to open file"))

        # XXX: We should start a readonly ts here, so we don't get the options
        # from the other one (sig checking, etc)
        try:
            hdr = ts.hdrFromFdno(fdno)
        except rpm.error as e:
            os.close(fdno)
            raise dnf.exceptions.Error(_("RPM Error opening Package"))
        if type(hdr) != rpm.hdr:
            os.close(fdno)
            raise dnf.exceptions.Error(_("RPM Error opening Package (type)"))

        os.close(fdno)
        return hdr

    ###########
    # Title: Remove duplicates from a sequence
    # Submitter: Tim Peters
    # From: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52560
    @staticmethod
    def unique(s):
        """Return a list of the elements in s, but without duplicates.
    
        For example, unique([1,2,3,1,2,3]) is some permutation of [1,2,3],
        unique("abcabc") some permutation of ["a", "b", "c"], and
        unique(([1, 2], [2, 3], [1, 2])) some permutation of
        [[2, 3], [1, 2]].
    
        For best speed, all sequence elements should be hashable.  Then
        unique() will usually work in linear time.
    
        If not possible, the sequence elements should enjoy a total
        ordering, and if list(s).sort() doesn't raise TypeError it's
        assumed that they do enjoy a total ordering.  Then unique() will
        usually work in O(N*log2(N)) time.
    
        If that's not possible either, the sequence elements must support
        equality-testing.  Then unique() will usually work in quadratic
        time.
        """
    
        n = len(s)
        if n == 0:
            return []
    
        # Try using a dict first, as that's the fastest and will usually
        # work.  If it doesn't work, it will usually fail quickly, so it
        # usually doesn't cost much to *try* it.  It requires that all the
        # sequence elements be hashable, and support equality comparison.
        u = {}
        try:
            for x in s:
                u[x] = 1
        except TypeError:
            del u  # move on to the next method
        else:
            return u.keys()
    
        # We can't hash all the elements.  Second fastest is to sort,
        # which brings the equal elements together; then duplicates are
        # easy to weed out in a single pass.
        # NOTE:  Python's list.sort() was designed to be efficient in the
        # presence of many duplicate elements.  This isn't true of all
        # sort functions in all languages or libraries, so this approach
        # is more effective in Python than it may be elsewhere.
        try:
            t = list(s)
            t.sort()
        except TypeError:
            del t  # move on to the next method
        else:
            assert n > 0
            last = t[0]
            lasti = i = 1
            while i < n:
                if t[i] != last:
                    t[lasti] = last = t[i]
                    lasti += 1
                i += 1
            return t[:lasti]
    
        # Brute force is all that's left.
        u = []
        for x in s:
            if x not in u:
                u.append(x)
        return u

    @staticmethod
    def compareEVR(evr1, evr2):
        # return 1: a is newer than b
        # 0: a and b are the same version
        # -1: b is newer than a
        (e1, v1, r1) = evr1
        (e2, v2, r2) = evr2
        if e1 is None:
            e1 = "0"
        else:
            e1 = str(e1)
        v1 = str(v1)
        r1 = str(r1)
        if e2 is None:
            e2 = "0"
        else:
            e2 = str(e2)
        v2 = str(v2)
        r2 = str(r2)
        rc = rpm.labelCompare((e1, v1, r1), (e2, v2, r2))
        return rc

    @staticmethod
    def pkgTupleFromHeader(hdr):
        """return a pkgtuple (n, a, e, v, r) from a hdr object, converts
           None epoch to 0, as well."""
       
        name = hdr["name"]
    
        # RPMTAG_SOURCEPACKAGE: RPMTAG_SOURCERPM is not necessarily there for
        # e.g. gpg-pubkeys imported with older rpm versions
        # http://lists.baseurl.org/pipermail/yum/2009-January/022275.html
        if hdr[rpm.RPMTAG_SOURCERPM] or hdr[rpm.RPMTAG_SOURCEPACKAGE] != 1:
            arch = hdr["arch"]
        else:
            arch = "src"
            
        ver = hdr["version"]
        rel = hdr["release"]
        epoch = hdr["epoch"]
        if epoch is None:
            epoch = "0"
        pkgtuple = (name, arch, epoch, ver, rel)
        return pkgtuple
