
import os.path

_dirname = os.path.dirname(__file__)

def version_readout():
    fn = os.path.join(_dirname, '../package/dnf-plugins-core.spec')
    with open(fn) as f:
        lines = f.readlines()
    for line in lines:
        if line.startswith('Version:'):
            return line.split(':')[1].strip()


print("[%s]" % version_readout())
