from __future__ import unicode_literals as _
from hashlib import sha256
import re

from .internet import absolute_url, clean_html, internet_content
from .version import is_canonical


class Dist(object):
    def __init__(self, name):
        self._name = name
        self._html = None

        self._fetch_pip_simple_html()

    @property
    def pypi_exists(self):
        return self._html is not None

    def conda_versions(self):
        url = "https://anaconda.org/conda-forge/%s" % self.dist_name

        c = internet_content(url)
        c = c.replace('\n', '')

        m = re.search(r"<ul class=\"list-inline no-bullet\">(.*)</ul>", c)
        if m is None:
            return None

        c = m.group(1)
        i = c.find('</ul>')

        c = clean_html(c[:i]).strip()
        c = " ".join(c.split())

        c = c.split(' ')
        data = dict()
        for i in range(len(c) // 2):
            data[c[2 * i]] = c[2 * i + 1].replace('v', '')

        return data

    @property
    def dist_name(self):
        return self._name.replace('_', '-')

    @property
    def pip_url(self):
        return "https://pypi.python.org/simple/%s/" % self.dist_name

    def _fetch_pip_simple_html(self):
        try:
            html = internet_content(self.pip_url)
        except RuntimeError:
            return
        self._html = re.sub(r".*h1>", "", html).strip()

    def filename_versions(self):
        wheel = []
        source = []

        for fn in self.clean_html.split("\n"):
            if fn.endswith('whl'):
                wheel.append((parse_wheel_filename(fn)['version'], fn))
            elif fn.endswith('tar.gz'):
                source.append((parse_source_filename(fn)['version'], fn))
            elif fn.endswith('egg'):
                pass
            elif fn.endswith('zip'):
                source.append((parse_source_filename(fn)['version'], fn))
            else:
                pass
                #raise ValueError("Unknown filetype:", fn)

        wheel = [v for v in wheel if is_canonical(v[0])]
        source = [v for v in source if is_canonical(v[0])]
        return dict(wheel=wheel, source=source)

    @property
    def html(self):
        return self._html

    @property
    def clean_html(self):
        if self._html is None:
            return ""
        return re.sub(r"<[^>]*>", "", self._html).strip()

    def filename_url(self, filename):
        expr = r"<a .*href=\"(.*)#md5=.*\" [^>]*>%s</a>" % filename
        suf = re.search(expr, self.html).group(1)
        return absolute_url(
            "https://pypi.python.org/simple/{}/{}".format(self.dist_name, suf))

    def file_content(self, filename):
        return internet_content(self.filename_url(filename), 'content')

    def pip_hash(self, filename):
        return sha256(self.file_content(filename)).hexdigest()


def parse_wheel_filename(filename):
    expr = r"^(.*)-(.*)(-\d.*)?-(.*)-(.*)-(.*)\.whl$"
    m = re.match(expr, filename)
    if m is None:
        return None

    fields = ['distribution', 'version', 'build', 'python', 'abi', 'platform']
    return {f: m.group(i + 1) for (i, f) in enumerate(fields)}


def parse_source_filename(filename):
    expr = r"^(.*)-(.*)\.(tar\.gz|zip)$"
    m = re.match(expr, filename)
    if m is None:
        return None

    fields = ['distribution', 'version']
    return {f: m.group(i + 1) for (i, f) in enumerate(fields)}
