import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from distutils.version import StrictVersion
from glob import glob
from os.path import exists, join, basename
from hashlib import sha256

import rstcheck
from git import Repo
from git.exc import InvalidGitRepositoryError
from setuptools import find_packages

from .internet import check_url, extract_urls, internet_content
from .printf import printe, printg
from .setupcfg import Setupcfg
from .version import is_canonical, version_sort


def _check_setup_file_uptodate(filename):
    url = "https://raw.githubusercontent.com/limix/setup/master/"
    url += basename(filename)
    c = internet_content(url, 'content')
    latest_hash = sha256(c).hexdigest()

    with open(filename, 'rb') as f:
        hash_ = sha256(f.read()).hexdigest()

    if hash_ != latest_hash:
        printe("%s file is not up-to-date." % filename +
               " Please, download it from %s." % url)


def _extract_urls(filename):
    with open(filename, 'r') as f:
        urls = extract_urls(f.read())

    ok = [check_url(url) for url in urls]

    broken_urls = [u for i, u in enumerate(urls) if not ok[i]]
    return (filename, broken_urls)


class Prj(object):
    def __init__(self, ignore_urls):
        data = dict()
        self._pkgname = None
        self._check_package_exists()

        data['license'] = check_get_files(['LICENSE.txt', 'LICENSE'])
        data['readme'] = check_get_files(['README.rst', 'README.md'])
        data['manifest'] = check_get_files(['MANIFEST.in'])
        data['setup.py'] = check_get_files(['setup.py'])
        data['setup.cfg'] = check_get_files(['setup.cfg'])
        data['conftest.py'] = check_get_files(['conftest.py'])

        if self._pkgname is not None:
            data['_test.py'] = check_get_files(
                [join(self._pkgname, '_test.py')])

        data['requirements.txt'] = check_get_files(['requirements.txt'])
        data['test-requirements.txt'] = check_get_files(
            ['test-requirements.txt'])

        self._data = data
        self._broken_urls = None
        self._pool = ThreadPoolExecutor()
        if not ignore_urls:
            self._find_urls()

        try:
            self._repo = Repo('.')
        except InvalidGitRepositoryError:
            self._repo = None

    def _find_urls(self):
        files = []
        for ext in ['py', 'rst', 'md', 'txt', 'cfg']:
            files += glob("./**/*.%s" % ext, recursive=True)

        tasks = ()
        self._broken_urls = self._pool.map(_extract_urls, files, chunksize=10)

    def check_setuppy(self):
        if self._data['setup.py'] is None:
            return

        _check_setup_file_uptodate(self._data['setup.py'])

    def check_conftestpy(self):
        if self._data['conftest.py'] is None:
            return

        _check_setup_file_uptodate(self._data['conftest.py'])
    
    def check_testpy(self):
        if self._data['_test.py'] is None:
            return

        _check_setup_file_uptodate(self._data['_test.py'])

    def check_urls(self):
        for urls in self._broken_urls:
            if len(urls[1]) == 0:
                continue
            printe("The following url(s) in " + urls[0] + " seem broken:")
            print('\n'.join('  ' + u for u in urls[1]))

    def check_pep8(self):
        p = subprocess.run(['pep8', '.'], stdout=subprocess.PIPE)
        if p.returncode != 0:
            printe('PEP8 violations:')
            msg = p.stdout.decode().strip()
            print('\n'.join('  ' + i for i in msg.split('\n')))

    def check_readme_source(self):
        if self._data['readme'] is None:
            return

        with open(self._data['readme'], 'r') as f:
            r = list(rstcheck.check(f.read()))

        if len(r) > 0:
            printe("There were some problems with %s:" % self._data['readme'])
            print('\n'.join(['  Line %d: %s' % i for i in r]))

    def check_init(self):
        if self._pkgname is None:
            return

        with open(join(self._pkgname, '__init__.py'), 'r') as f:
            rows = [r.strip() for r in f.read().split('\n')]

        look_for = [
            '__name__', '__version__', '__author__', '__author_email__'
        ]
        found = {lf: False for lf in look_for}
        for r in rows:
            for lf in look_for:
                if r.startswith(lf):
                    found[lf] = True

        if not all(found.values()):
            printe("Could not find " + ', '.join(lk for lk in look_for
                                                 if not found[lk]))

    @property
    def version(self):
        if self._pkgname is None:
            return None

        return _get_init_variable(self._pkgname, 'version')

    def check_version(self):

        if self._repo is None:
            return

        branch = self._repo.active_branch

        if branch.name == 'master':
            tags = [t.name for t in self._repo.tags if is_canonical(t.name)]
            if len(tags) == 0:
                return
            version_sort(tags)
            tag_version = tags[-1]

            if StrictVersion(tag_version) > StrictVersion(self.version):
                msg = "Tag version (%s) is more recent " % tag_version
                msg += "than the project one (%s)." % self.version
                printe(msg)
            elif StrictVersion(tag_version) < StrictVersion(self.version):
                msg = "Tag version (%s) is not " % tag_version
                msg += "up-to-date to the project one (%s)." % self.version
                printe(msg)

    def check_setupcfg(self):
        if self._data['setup.cfg'] is None:
            return

        data = self._data
        s = Setupcfg(data['setup.cfg'])

        if data['readme'] and s.exists('description_file'):
            fn = s.get('description_file')
            if fn != data['readme']:
                msg = 'setup.cfg description_file is pointing to'
                printe(msg + ' %s instead of %s.' % (fn, data['readme']))

    def check_manifest(self):
        if self._data['manifest'] is None:
            return

        data = self._data
        look_for = [
            'readme', 'license', 'requirements.txt', 'test-requirements.txt'
        ]
        look_for = [f for f in look_for if data[f] is not None]
        found = {lf: False for lf in look_for}

        with open(data['manifest'], 'r') as f:
            rows = f.read().split('\n')

        for r in rows:
            r = r.strip()
            for lf in found.keys():
                if r == 'include %s' % data[lf]:
                    found[lf] = True

        if not all(found.values()):
            v = [f for f in found.keys() if not found[f]]
            if len(v) == 1:
                sep = 'is'
            else:
                sep = 'are'
            whi = ', '.join(data[vi] for vi in v)
            printe(whi + " %s missing in %s." % (sep, data['manifest']))

    def _check_package_exists(self):
        pkgs = find_packages()
        if len(pkgs) == 0:
            printe("No Python package could be found at %s." % here())

        self._pkgname = pkgs[0]


def check_get_files(filenames):
    if not any(exists(f) for f in filenames):
        printe("Could not find " + ' nor '.join(filenames) + " file(s).")
    else:
        return next(f for f in filenames if exists(f))


def _get_init_variable(prjname, name):
    expr = re.compile(r"__%s__ *=[^\"]*\"([^\"]*)\"" % name)
    data = open(join(prjname, "__init__.py")).read()
    return re.search(expr, data).group(1)
