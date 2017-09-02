from __future__ import unicode_literals

import subprocess
import re
import os
from os.path import exists
from argparse import ArgumentParser
from distutils.version import StrictVersion
from .internet import internet_content, absolute_url, clean_html, check_url, extract_urls
from . import license
from datetime import datetime
from setuptools import find_packages
import rstcheck
from glob import glob
from .setupcfg import Setupcfg
from .prj import Prj
from .printf import printe, printg


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
        prj = Prj()

        prj.check_package_exists()
        prj.check_manifest()
        prj.check_setupcfg()
        prj.check_init()
        prj.check_pep8()
        prj.check_readme_source()
        prj.check_urls()
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




