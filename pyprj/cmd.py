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
from .dist import Dist


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

    do_pip(d)
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
    if not d.pypi_exists:
        printe("Not found in PyPI.")
        return
    print("PyPI")
    fnvers = d.filename_versions()
    fnvers = sort_filename_versions(fnvers)
    
    ftypes = [v for v in ['source', 'wheel'] if len(fnvers[v]) > 0]

    latest = {t: fnvers[t][-1][0] for t in ftypes}

    source_filename = fnvers['source'][-1][1]
    
    if 'source' in latest:
        print("    Source:", latest['source'], d.pip_hash(source_filename))

    if 'wheel' in latest:
        print("     Wheel:", latest['wheel'])

def do_conda(d):
    data = d.conda_versions()
    if data is None:
        printe("Not found in Conda.")
        return

    print("Conda")
    n = max(len(k) for k in data.keys())
    for k in sorted(data.keys()):
        print('  ' + ' ' * (n - len(k)) + '%s:' % k, data[k])

def sort_filename_versions(fnvers):
    types = ['wheel', 'source']
    for t in types:
        fnvers[t].sort(key=lambda x: StrictVersion(x[0]))

    return fnvers
