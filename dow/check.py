from os.path import exists, abspath, isdir
from os import chdir, curdir
from .prj import Prj

def do_check(args):
    path = args.path

    if not exists(path):
        printe("Path %s does not exist." % path)

    if not isdir(path):
        printe("%s is not a folder." % path)

    opath = abspath(curdir)
    try:
        chdir(path)
        prj = Prj(ignore_urls=not args.check_urls)

        prj.check_package_exists()
        prj.check_manifest()
        prj.check_setupcfg()
        prj.check_init()
        prj.check_pep8()
        prj.check_readme_source()
        prj.check_version()
        prj.check_setuppy()
        if args.check_urls:
            prj.check_urls()
    finally:
        chdir(opath)


