from __future__ import unicode_literals

import re
from argparse import ArgumentParser
from distutils.version import StrictVersion
from .internet import internet_content, absolute_url
from .pip_hash import pip_hash


def pipv():
    p = ArgumentParser()
    p.add_argument('dist', help='distribution name')
    args = p.parse_args()

    d = Dist(args.dist)
    d.fetch_pip_simple_html()
    d.pip_simple_clean_html()

    fnvers = d.filename_versions()
    fnvers = sort_filename_versions(fnvers)
    
    ftypes = ['source', 'wheel']

    latest = {t: fnvers[t][-1][0] for t in ftypes}

    source_filename = fnvers['source'][-1][1]
    
    print("Source:", latest['source'], d.pip_hash(source_filename))
    print(" Wheel:", latest['wheel'])


def sort_filename_versions(fnvers):
    types = ['wheel', 'source']
    for t in types:
        fnvers[t].sort(key=lambda x: StrictVersion(x[0]))

    return fnvers

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
        self._html = self._html

    def fetch_pip_simple_html(self):
        html = internet_content(self.pip_url)
        self._html = re.sub(r".*h1>", "", html).strip()

    def filename_versions(self):
        wheel = []
        source = []

        for fn in self.clean_html.split("\n"):
            if fn.endswith('whl'):
                wheel.append((parse_wheel_filename(fn)['version'], fn))
            elif fn.endswith('tar.gz'):
                source.append((parse_source_filename(fn)['version'], fn))
            else:
                raise ValueError("Unknown filetype")

        return dict(wheel=wheel, source=source)
    
    @property
    def html(self):
        return self._html

    @property
    def clean_html(self):
        return re.sub(r"<[^>]*>", "", self._html).strip()
    
    def filename_url(self, filename):
        expr = r"<a href=\"(.*)#md5=.*\" [^>]*>%s</a>" % filename
        suf = re.search(expr, self.html).group(1)
        return absolute_url("https://pypi.python.org/simple/{}/{}".format(self.dist_name, suf))

    def file_content(self, filename):
        return internet_content(self.filename_url(filename), 'content')

    def pip_hash(self, filename):
        return pip_hash(self.file_content(filename))

