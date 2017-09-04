import re
from distutils.version import StrictVersion
from distutils.version import LooseVersion


def is_canonical(version):
    expr = r'^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*'
    expr += '((a|b|rc)(0|[1-9]\d*))?(\.post(0|[1-9]\d*))?(\.dev(0|[1-9]\d*))?$'
    return re.match(expr, version) is not None


def version_sort(versions, key=None):
    if key is None:
        _key = LooseVersion
    else:

        def _key(x):
            return LooseVersion(key(x))

    versions.sort(key=_key)
