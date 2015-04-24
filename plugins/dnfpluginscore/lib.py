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

import dnf
import iniparse
import librepo
import tempfile


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
                         cfgoptions, items, optionobj,
                         modify=None):
    """
    # :api
    Code adopted from yum-config-manager writeRawRepoFile().
    filename   - name of config file (.conf or .repo)
    section_id - id of modified section (e.g. main, fedora, updates)
    substitutions - instance of base.conf.substitutions
    cfgoptions - options parsed from conf file (e.g. base.conf.cfg.options)
    items      - current global or repo settings (e.g. base.conf.iteritems)
    optionobj  - option parse object (e.g. base.conf.optionobj)
    modify     - list of modified options
    """
    ini = iniparse.INIConfig(open(filename))

    osection_id = section_id
    # b/c repoids can have $values in them we need to map both ways to figure
    # out which one is which
    if section_id not in ini:
        for sect in ini:
            if dnf.conf.parser.substitute(sect, substitutions) == section_id:
                section_id = sect

    # Updated the ConfigParser with the changed values
    cfgopts = cfgoptions(osection_id)
    for name, value in items():
        if value is None: # Proxy
            continue

        if modify is not None and name not in modify:
            continue

        option = optionobj(name)
        ovalue = option.tostring(value)
        #  If the value is the same, but just interpreted ... when we don't want
        # to keep the interpreted values.
        if (name in ini[section_id] and
                ovalue == dnf.conf.parser.substitute(ini[section_id][name],
                                                     substitutions)):
            ovalue = ini[section_id][name]

        if name not in cfgopts and option.default == value:
            continue

        ini[section_id][name] = ovalue
    fp = open(filename, "w")
    fp.write(str(ini))
    fp.close()

def _enable_sub_repos(repos, sub_name_fn):
    for repo in repos.iter_enabled():
        repos.get_matching(sub_name_fn(repo.id)).enable()

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
