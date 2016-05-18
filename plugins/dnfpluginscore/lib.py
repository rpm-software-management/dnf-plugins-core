#
# Copyright (C) 2015  Red Hat, Inc.
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

from dnf.pycomp import PY3
from dnfpluginscore import _, logger

import dnf
import iniparse
import librepo
import tempfile
import os

def get_reposdir(plugin):
    """
    # :api
    Returns the value of reposdir
    """
    myrepodir = None
    # put repo file into first reposdir which exists or create it
    for rdir in plugin.base.conf.reposdir:
        if os.path.exists(rdir):
            myrepodir = rdir

    if not myrepodir:
        myrepodir = plugin.base.conf.reposdir[0]
        dnf.util.ensure_dir(myrepodir)
    return myrepodir

def current_value(plugin, repo, option):
    """
    # :api
    Returns current value of the option
    (set in .repo or dnf.conf or on commandline).
    """
    if (repo is not None and
            hasattr(repo, option) and getattr(repo, option) is not None):
        return getattr(repo, option)
    conf = plugin.base.conf
    if (hasattr(conf, option) and getattr(conf, option) is not None):
        return getattr(conf, option)
    return None


def urlopen(plugin, repo, url, mode='w+b', **kwargs):
    """
    # :api
    modified dnf.util.urlopen() which respects proxy setting
    even for non-repo downloads
    """
    conf = plugin.base.conf

    def non_repo_handle():
        handle = librepo.Handle()
        handle.useragent = dnf.const.USER_AGENT
        # see dnf.repo.Repo._handle_new_remote() how to pass
        handle.maxspeed = conf.throttle if type(conf.throttle) is int \
                     else int(conf.bandwidth * conf.throttle)
        handle.proxy = conf.proxy
        handle.proxyuserpwd = dnf.repo._user_pass_str(conf.proxy_username,
                                                      conf.proxy_password)
        handle.sslverifypeer = handle.sslverifyhost = conf.sslverify
        return handle

    if PY3 and 'b' not in mode:
        kwargs.setdefault('encoding', 'utf-8')
    fo = tempfile.NamedTemporaryFile(mode, **kwargs)
    if repo:
        handle = repo.get_handle()
    else:
        handle = non_repo_handle()
    try:
        librepo.download_url(url, fo.fileno(), handle)
    except librepo.LibrepoException as e:
        raise IOError(e.args[1])
    fo.seek(0)
    return fo


def write_raw_configfile(filename, section_id, substitutions,
                         modify):
    """
    # :api
    filename   - name of config file (.conf or .repo)
    section_id - id of modified section (e.g. main, fedora, updates)
    substitutions - instance of base.conf.substitutions
    modify     - dict of modified options
    """
    ini = iniparse.INIConfig(open(filename))

    # b/c repoids can have $values in them we need to map both ways to figure
    # out which one is which
    if section_id not in ini:
        for sect in ini:
            if dnf.conf.parser.substitute(sect, substitutions) == section_id:
                section_id = sect

    for name, value in modify.items():
        if isinstance(value, list):
            value = ' '.join(value)
        ini[section_id][name] = value

    fp = open(filename, "w")
    fp.write(str(ini))
    fp.close()

def _enable_sub_repos(repos, sub_name_fn):
    for repo in repos.iter_enabled():
        for found in repos.get_matching(sub_name_fn(repo.id)):
            if not found.enabled:
                logger.info(_('enabling %s repository'), found.id)
                found.enable()

def enable_source_repos(repos):
    """
    # :api
    enable source repos corresponding to already enabled binary repos
    """
    def source_name(name):
        return ("{}-source-rpms".format(name[:-5]) if name.endswith("-rpms")
                else "{}-source".format(name))
    _enable_sub_repos(repos, source_name)

def enable_debug_repos(repos):
    """
    # :api
    enable debug repos corresponding to already enabled binary repos
    """
    def debug_name(name):
        return ("{}-debug-rpms".format(name[:-5]) if name.endswith("-rpms")
                else "{}-debuginfo".format(name))
    _enable_sub_repos(repos, debug_name)

def package_debug_name(package):
    """
    # :api
    returns name of debuginfo package for given package
    e.g. kernel-PAE -> kernel-PAE-debuginfo
    """
    return "{}-debuginfo".format(package.name)

def package_source_name(package):
    """"
    # :api
    returns name of source package for given pkgname
    e.g. krb5-libs -> krb5
    """
    if package.sourcerpm is not None:
        # trim suffix first
        srcname = rtrim(package.sourcerpm, ".src.rpm")
        # source package filenames may not contain epoch, handle both cases
        srcname = rtrim(srcname, "-{}".format(package.evr))
        srcname = rtrim(srcname, "-{0.version}-{0.release}".format(package))
    else:
        srcname = None
    return srcname

def package_source_debug_name(package):
    """
    # :api
    returns name of debuginfo package for source package of given package
    e.g. krb5-libs -> krb5-debuginfo
    """
    srcname = package_source_name(package)
    return "{}-debuginfo".format(srcname)

def rtrim(s, r):
    while s.endswith(r):
        s = s[:-len(r)]
    return s
