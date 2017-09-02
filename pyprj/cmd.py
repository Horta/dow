from __future__ import unicode_literals

import os
import re
import subprocess
from argparse import ArgumentParser
from datetime import datetime
from glob import glob
from os.path import exists

import rstcheck
from setuptools import find_packages

from . import license
from .dist import Dist
from .internet import (
    absolute_url, check_url, clean_html, extract_urls, internet_content
)
from .printf import printe, printg
from .prj import Prj
from .setupcfg import Setupcfg
from .version import version_sort


def pyprj():
    p = ArgumentParser()
    sp = p.add_subparsers(title='commands', dest='command')

    see = sp.add_parser('see')
    see.add_argument('dist', help='distribution name')

    check = sp.add_parser('check')
    check.add_argument('path', help='project path')
    check.add_argument(
        '--ignore-urls',
        help='do not check urls',
        action='store_true',
        default=False)

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
        prj = Prj(ignore_urls=args.ignore_urls)

        prj.check_package_exists()
        prj.check_manifest()
        prj.check_setupcfg()
        prj.check_init()
        prj.check_pep8()
        prj.check_readme_source()
        prj.check_version()
        if not args.ignore_urls:
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
        version_sort(fnvers[t], lambda x: x[0])

    return fnvers
