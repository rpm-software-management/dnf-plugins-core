from dnfpluginscore import _, logger
from dnf.cli.option_parser import OptionParser

import binascii
import itertools
import libpkgmanifest
import os

import dnf.cli
import hawkey


DEFAULT_MANIFEST_FILENAME = 'packages.manifest.yaml'
ALL_ARCHES = ['noarch', 'aarch64', 'i686', 'ppc64le', 's390x', 'x86_64']


@dnf.plugin.register_command
class ManifestCommand(dnf.cli.Command):
    aliases = ("manifest",)
    summary = _("Operations for working with RPM package manifest files")

    def __init__(self, cli):
        super(ManifestCommand, self).__init__(cli)
        self.cmd = None
        self.file = None
        self.download_dir = None

    @staticmethod
    def set_argparser(parser):
        parser.add_argument("subcommand", nargs=1, choices=['new', 'download', 'install'])
        parser.add_argument('specs', nargs='*', help=_('package specs to be processed'))
        parser.add_argument('--file', help=_('manifest file path to use'))
        parser.add_argument("--source", action='store_true', help=_('include also source packages'))
        parser.add_argument("--arch", '--archlist', dest='arches', default=[],
                            action=OptionParser._SplitCallback, metavar='[arch]',
                            help=_('include only packages of given architectures'))

    def configure(self):
        self.cmd = self.opts.subcommand[0]

        demands = self.cli.demands
        demands.sack_activation = True
        demands.available_repos = True

        self.base.conf.strict = True

        if self.cmd == 'install':
            demands.resolving = True

        if self.opts.source:
            self.base.repos.enable_source_repos()

        if self.opts.file:
            self.file = self.opts.file
        else:
            self.file = DEFAULT_MANIFEST_FILENAME

        if self.opts.destdir:
            self.download_dir = self.opts.destdir
        else:
            self.download_dir, _ = os.path.splitext(os.path.join(dnf.i18n.ucd(os.getcwd()), self.file))

        if self.cmd in ['install', 'download']:
            self.base.conf.destdir = self.download_dir

    def run(self):
        match self.cmd:
            case 'new':
                self._new()
            case 'download':
                self._download()
            case 'install':
                self._install()

    def _new(self):
        if not self.opts.specs:
            raise dnf.exceptions.Error(_("No package specs provided for the 'new' command"))

        self._generate(self.opts.specs)

    def _download(self):
        specs = self._manifest_to_pkg_specs()
        dnf_pkgs = self._get_packages(specs)

        pkg_dict = {}
        for pkg in dnf_pkgs:
            pkg_dict.setdefault(str(pkg), []).append(pkg)

        to_download = []
        for pkg_list in pkg_dict.values():
            pkg_list.sort(key=lambda x: (x.repo.priority, x.repo.cost))
            to_download.append(pkg_list[0])
        if to_download:
            self.base.download_packages(to_download, self.base.output.progress)

    def _install(self):
        for spec in self._manifest_to_pkg_specs():
            self.base.install(spec)

    def _generate(self, specs):
        manifest = libpkgmanifest.Manifest()

        for dnf_pkg in self._get_packages_with_deps(specs):
            pkg = libpkgmanifest.Package()
            pkg.arch = dnf_pkg.arch
            pkg.repo_id = dnf_pkg.repoid
            pkg.nevra = self._get_package_nevra(dnf_pkg)
            pkg.size = dnf_pkg.size
            pkg.url = dnf_pkg.remote_location()
            pkg.srpm = dnf_pkg.sourcerpm if dnf_pkg.arch != 'src' else pkg.nevra

            dnf_chksum_type, dnf_chksum_digest = dnf_pkg.chksum
            pkg.checksum.method = self._checksum_type_to_manifest_conversion(dnf_chksum_type)
            pkg.checksum.digest = binascii.hexlify(dnf_chksum_digest).decode()

            manifest.packages.add(pkg)

        serializer = libpkgmanifest.Serializer()
        serializer.serialize(manifest, self.file)
    
    def _manifest_to_pkg_specs(self):
        if not os.path.isfile(self.file):
            raise dnf.exceptions.Error(_("Input manifest file '%s' does not exist") % self.file)

        parser = libpkgmanifest.Parser()
        manifest = parser.parse(self.file)
        pkgs = [pkg for pkgs in manifest.packages.get().values() for pkg in pkgs]
        if self.cmd == 'install' or not self.opts.source:
            pkgs = [pkg for pkg in pkgs if pkg.arch != 'src']
        return [pkg.nevra for pkg in pkgs]

    def _get_packages_with_deps(self, pkg_specs):
        pkgs = set(self._get_packages(pkg_specs))
        if self.cmd == 'generate' and self.opts.source:
            pkgs |= set(self._get_packages(pkg_specs, True))

        pkg_set = set(pkgs)
        for pkg in pkgs:
            goal = hawkey.Goal(self.base.sack)
            goal.install(pkg)
            rc = goal.run(ignore_weak_deps=(not self.base.conf.install_weak_deps))
            if rc:
                pkg_set.update(goal.list_installs())
                pkg_set.update(goal.list_upgrades())
            else:
                msg = [_('Error in resolve of packages:')]
                logger.error("\n    ".join(msg + [str(pkg) for pkg in pkgs]))
                logger.error(dnf.util._format_resolve_problems(goal.problem_rules()))
                raise dnf.exceptions.Error()
        return pkg_set

    def _get_packages(self, pkg_specs, source=False):
        func = self._get_query_source if source else self._get_query
        queries = []
        for pkg_spec in pkg_specs:
            try:
                queries.append(func(pkg_spec))
            except dnf.exceptions.PackageNotFoundError as e:
                logger.error(dnf.i18n.ucd(e))
                raise dnf.exceptions.Error(e)

        pkgs = list(itertools.chain(*queries))
        return pkgs

    def _get_query(self, pkg_spec):
        subj = dnf.subject.Subject(pkg_spec)
        q = subj.get_best_query(self.base.sack, with_src=self.opts.source)
        q = q.available()
        q = q.filterm(latest_per_arch_by_priority=True)
        if len(q.run()) == 0:
            msg = _("No package %s available.") % (pkg_spec)
            raise dnf.exceptions.PackageNotFoundError(msg)
        return q

    def _get_query_source(self, pkg_spec):
        subj = dnf.subject.Subject(pkg_spec)
        for nevra_obj in subj.get_nevra_possibilities():
            tmp_query = nevra_obj.to_query(self.base.sack).available()
            if tmp_query:
                return tmp_query.latest()

        msg = _("No package %s available.") % (pkg_spec)
        raise dnf.exceptions.PackageNotFoundError(msg)

    def _checksum_type_to_manifest_conversion(self, checksum_type):
        match checksum_type:
            case hawkey.CHKSUM_MD5:
                return libpkgmanifest.ChecksumMethod_MD5
            case hawkey.CHKSUM_SHA1:
                return libpkgmanifest.ChecksumMethod_SHA1
            case hawkey.CHKSUM_SHA256:
                return libpkgmanifest.ChecksumMethod_SHA256
            case hawkey.CHKSUM_SHA384:
                return libpkgmanifest.ChecksumMethod_SHA384
            case hawkey.CHKSUM_SHA512:
                return libpkgmanifest.ChecksumMethod_SHA512
            case _:
                raise dnf.exceptions.Error(_("Unknown package checksum type: %s") % checksum_type)

    def _get_package_nevra(self, pkg):
        name = pkg.name
        epoch = pkg.epoch if pkg.epoch is not None else "0"
        version = pkg.version
        release = pkg.release
        arch = pkg.arch

        return f"{name}-{epoch}:{version}-{release}.{arch}"
