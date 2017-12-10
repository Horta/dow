from __future__ import unicode_literals

from argparse import ArgumentParser

from .check import do_check
from .see import do_see
from .create import do_create
from .update import do_update


def dow():
    p = ArgumentParser()
    sp = p.add_subparsers(title='commands', dest='command')

    see = sp.add_parser('see')
    see.add_argument('dist_or_path', help='distribution name or path to a project')

    update = sp.add_parser('update')
    update.add_argument('file', help='file with requirements')

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
    elif args.command == 'update':
        do_update(args)
