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
from .internet import (absolute_url, check_url, clean_html, extract_urls,
                       internet_content)
from .printf import printe, printg
from .prj import Prj
from .setupcfg import Setupcfg
from .version import version_sort
from .check import do_check
from .see import do_see
from .create import do_create


def dow():
    p = ArgumentParser()
    sp = p.add_subparsers(title='commands', dest='command')

    see = sp.add_parser('see')
    see.add_argument('dist', help='distribution name')

    check = sp.add_parser('check')
    check.add_argument('path', help='project path')
    check.add_argument(
        '--check-urls',
        help='do not check urls',
        action='store_true',
        default=False)

    create = sp.add_parser('create')
    create.add_argument('what', help='what')
    create.add_argument('--author', help='author')
    create.add_argument(
        '--force', help='force', action='store_true', default=False)

    args = p.parse_args()

    if args.command == 'see':
        do_see(args)
    elif args.command == 'check':
        do_check(args)
    elif args.command == 'create':
        do_create(args)

