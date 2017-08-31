from __future__ import unicode_literals

import re
from argparse import ArgumentParser
from distutils.version import StrictVersion

import requests


def pipv():
    p = ArgumentParser()
    p.add_argument('dist', help='distribution name')
    args = p.parse_args()

    d = Dist(args.dist)
    d.fetch_pip_simple_html()
    d.pip_simple_clean_html()

    versions = d.versions()

    types = ['wheel', 'source']
    for t in types:
        versions[t].sort(key=StrictVersion)

    latest = {t: versions[t][-1] for t in types}
    print(latest)


def parse_wheel_filename(filename):
    expr = r"^(.*)-(.*)(-\d.*)?-(.*)-(.*)-(.*)\.whl$"
    m = re.match(expr, filename)
    if m is None:
        return None

    fields = ['distribution', 'version', 'build', 'python', 'abi', 'platform']
    return {f: m.group(i + 1) for (i, f) in enumerate(fields)}


def parse_source_filename(filename):
    expr = r"^(.*)-(.*)\.tar\.gz$"
    m = re.match(expr, filename)
    if m is None:
        return None

    fields = ['distribution', 'version']
    return {f: m.group(i + 1) for (i, f) in enumerate(fields)}


class Dist(object):
    def __init__(self, name):
        self._name = name

    @property
    def dist_name(self):
        return self._name.replace('_', '-')

    @property
    def pip_url(self):
        return "https://pypi.python.org/simple/%s/" % self.dist_name

    def pip_simple_clean_html(self):
        self._html = re.sub(r".*h1>", "", self._html)
        self._html = re.sub(r"<[^>]*>", "", self._html)
        self._html = self._html.strip()

    def fetch_pip_simple_html(self):
        resp = requests.get(self.pip_url)
        if resp.ok:
            self._html = resp.text
        else:
            msg = "Failure while requesting %s: " % self.pip_url
            raise RuntimeError(msg + str(resp.status_code))

    def versions(self):
        wheel = []
        source = []

        for fn in self.html.split("\n"):
            if fn.endswith('whl'):
                wheel.append(parse_wheel_filename(fn)['version'])
            elif fn.endswith('tar.gz'):
                source.append(parse_source_filename(fn)['version'])
            else:
                raise ValueError("Unknown filetype")

        return dict(wheel=wheel, source=source)

    @property
    def html(self):
        return self._html
