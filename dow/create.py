from .here import here
from os.path import exists, join
from datetime import datetime
from .internet import internet_content
from .printf import printe, printg


def do_create(args):
    dst = here()

    if args.what == 'license':
        dst = join(dst, 'LICENSE.txt')

        if not args.force and exists(dst):
            printe("%s already exist." % dst)
            return

        c = license.mit(datetime.now().year, args.author)

        with open(dst, 'w') as f:
            f.write(c)

        printg("License file %s created." % dst)
    elif args.what == 'setup.py':
        dst = join(dst, 'setup.py')

        if not args.force and exists(dst):
            printe("%s already exist." % dst)
            return

        url = "https://raw.githubusercontent.com/limix/setup/master/setup.py"
        c = internet_content(url)

        with open(dst, 'w') as f:
            f.write(c)

        printg("setup.py file %s created." % dst)
