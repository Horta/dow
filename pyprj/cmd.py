from __future__ import unicode_literals

import subprocess
import re
import os
from os.path import exists
from argparse import ArgumentParser
from distutils.version import StrictVersion
from .internet import internet_content, absolute_url, clean_html, check_url, extract_urls
from .pip_hash import pip_hash
from . import license
from datetime import datetime
from setuptools import find_packages
import rstcheck
from glob import glob

def printe(msg):
    from colorama import Fore, Style
    print(Fore.RED + '\u2717 ' + msg + Style.RESET_ALL)

def printg(msg):
    from colorama import Fore, Style
    print(Fore.GREEN + '\u2713 ' + msg + Style.RESET_ALL)


def pif():
    p = ArgumentParser()
    sp = p.add_subparsers(title='commands', dest='command')

    see = sp.add_parser('see')
    see.add_argument('dist', help='distribution name')

    check = sp.add_parser('check')
    check.add_argument('path', help='project path')

    create = sp.add_parser('create')
    create.add_argument('what', help='what')
    create.add_argument('author', help='author')

    args = p.parse_args()
    
    if args.command == 'see':
        do_see(args)
    elif args.command == 'check':
        do_check(args)
    elif args.command == 'create':
        do_create(args)

def here():
    return os.path.abspath(os.curdir)
    
def do_see(args):
    d = Dist(args.dist)

    print("PyPI")
    do_pip(d)
    print("Conda")
    do_conda(d)

def do_check(args):
    path = args.path

    if not exists(path):
        printe("Path %s does not exist." % path)
    
    if not os.path.isdir(path):
        printe("%s is not a folder." % path)
    
    opath = os.path.abspath(os.curdir)
    try:
        os.chdir(path)
        data = dict()
        data['license'] = check_and_get(['LICENSE.txt', 'LICENSE'])
        data['readme'] = check_and_get(['README.rst', 'README.md'])
        data['manifest'] = check_and_get(['MANIFEST.in'])
        data['setup.py'] = check_and_get(['setup.py'])
        data['setup.cfg'] = check_and_get(['setup.cfg'])

        check_package_exists()

        if data['manifest']:
            check_manifest(data)

        if data['setup.cfg']:
            check_setupcfg(data)

        check_init(data)
        check_pep8()
        if data['readme']:
            check_readme_source(data['readme'])

        check_urls()
    finally:
        os.chdir(opath)

def do_create(args):
    dst = here()
    
    if args.what == 'license':
        dst = os.path.join(dst, 'LICENSE.txt')
        

        if exists(dst):
            printe("%s already exist." % dst)
            return
        
        c = license.mit(datetime.now().year, args.author)

        with open(dst, 'w') as f:
            f.write(c)

        printg("License file %s created." % dst)

def check_urls():
    files = []
    for ext in ['py', 'rst', 'md', 'txt', 'cfg']:
        files += glob("./**/*.%s" % ext, recursive=True)

    urlss = dict()
    for fi in files:
        with open(fi, 'r') as f:
            urlss[fi] = extract_urls(f.read())

    for fi in urlss.keys():
        urls = urlss[fi]
        ok = [check_url(url) for url in urls]
        if not all(ok):
            printe("The following url(s) in " + fi + " seem broken:")
            print('\n'.join('  ' + u for i, u in enumerate(urls) if not ok[i]))

def check_pep8():
    p = subprocess.run(['pep8', '.'], stdout=subprocess.PIPE)
    if p.returncode != 0:
        printe('PEP8 violations:')
        msg = p.stdout.decode().strip()
        print('\n'.join('  ' + i for i in msg.split('\n')))

def check_readme_source(filename):
    with open(filename, 'r') as f:
        r = list(rstcheck.check(f.read()))
    
    if len(r) > 0:
        printe("There were some problems with %s:" % filename)
        print('\n'.join(['  Line %d: %s' % i for i in r]))

def check_init(data):
    pkgs = find_packages()
    if len(pkgs) == 0:
        return

    pkg = pkgs[0]
    with open(os.path.join(pkg, '__init__.py'), 'r') as f:
        rows = [r.strip() for r in f.read().split('\n')]

    look_for = ['__name__', '__version__', '__author__', '__author_email__']
    found = {lf:False for lf in look_for}
    for r in rows:
        for lf in look_for:
            if r.startswith(lf):
                found[lf] = True

    if not all(found.values()):
        printe("Could not find " + ', '.join(lk for lk in look_for if not found[lk]))

class Setupcfg(object):
    def __init__(self, filename):
        with open(filename, 'r') as f:
            rows = f.read().split('\n')
            rows = [r.strip() for r in rows]
        self._rows = rows

    def exists(self, what):
        for r in self._rows:
            if '=' not in r:
                continue
            if r.split('=')[0].strip() == what:
                return True
        return False
    
    def get(self, what):
        for r in self._rows:
            if '=' not in r:
                continue
            if r.split('=')[0].strip() == what:
                return r.split('=')[1].strip()
        return None

def check_setupcfg(data):
    s = Setupcfg(data['setup.cfg'])

    if data['readme'] and s.exists('description_file'):
        fn = s.get('description_file')
        if fn != data['readme']:
            printe('setup.cfg description_file is pointing to %s instead of %s.' % (fn, data['readme']))


def check_manifest(data):

    look_for = [f for f in ['readme', 'license'] if data[f] is not None]
    found = {lf:False for lf in look_for}

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
            sep  = 'is'
        else:
            sep = 'are'
        whi = ', '.join(data[vi] for vi in v)
        printe(whi + " %s missing in %s." % (sep, data['manifest']))

def check_package_exists():
    pkgs = find_packages()
    if len(pkgs) == 0:
        printe("No Python package could be found at %s." % here())

def check_and_get(filenames):
    if not any(exists(f) for f in filenames):
        printe("Could not find " + ' nor '.join(filenames) + " file(s).")
    else:
        return next(f for f in filenames if exists(f))

def do_pip(d):
    fnvers = d.filename_versions()
    fnvers = sort_filename_versions(fnvers)
    
    ftypes = ['source', 'wheel']

    latest = {t: fnvers[t][-1][0] for t in ftypes}

    source_filename = fnvers['source'][-1][1]
    
    print("    Source:", latest['source'], d.pip_hash(source_filename))
    print("     Wheel:", latest['wheel'])

def do_conda(d):
    data = d.conda_versions()
    n = max(len(k) for k in data.keys())
    for k in sorted(data.keys()):
        print('  ' + ' ' * (n - len(k)) + '%s:' % k, data[k])


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

        self._fetch_pip_simple_html()
        self._pip_simple_clean_html()

    def conda_versions(self):
        url = "https://anaconda.org/conda-forge/%s" % self.dist_name
        
        c = internet_content(url)
        c = c.replace('\n', '')
        
        m = re.search(r"<ul class=\"list-inline no-bullet\">(.*)</ul>", c)
        c = m.group(1)
        i = c.find('</ul>')
        
        c = clean_html(c[:i]).strip()
        c = " ".join(c.split())
        
        c = c.split(' ')
        data = dict()
        for i in range(len(c)//2):
            data[c[2 * i]] = c[2 * i + 1].replace('v', '')

        return data

    @property
    def dist_name(self):
        return self._name.replace('_', '-')

    @property
    def pip_url(self):
        return "https://pypi.python.org/simple/%s/" % self.dist_name

    def _pip_simple_clean_html(self):
        self._html = self._html

    def _fetch_pip_simple_html(self):
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
            elif fn.endswith('egg'):
                pass
            else:
                raise ValueError("Unknown filetype:", fn)

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

