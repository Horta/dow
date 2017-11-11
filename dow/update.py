import os
from .here import here
from os.path import exists, join
from datetime import datetime
from .internet import internet_content
from .printf import printe, printg
from . import license
from .dist import Dist
from .version import version_sort, is_canonical, is_final
from requirements import parse
from tqdm import tqdm
from colorama import Fore, Style


def do_update(args):
    dst = here()

    out = dict()
    with open(args.file, "r") as f:
        for r in tqdm(list(parse(f))):

            if r.name in out:
                continue

            change = False
            if len(r.specs) > 1:
                text = _implode(r)

            elif len(r.specs) == 1 and r.specs[0][0] not in ['>', '>=']:
                text = _implode(r)
            else:
                d = Dist(r.name)
                versions = _extract_versions(d.filename_versions().values())
                if len(versions) > 0:
                    v = version_sort(versions)[0]
                    row = r.name + '>=' + v
                    text = row
                    change = _implode(r) != row
                else:
                    text = _implode(r)

            out[r.name] = (text, change)

    names = sorted(out.keys())
    for n in names:
        if out[n][1]:
            print(Fore.RED + out[n][0] + Style.RESET_ALL)
        else:
            print(out[n][0])

    reqs = [out[n][0] for n in names]
    _write_down(args.file, '\n'.join(reqs) + '\n')


def _extract_versions(versions):
    r = []
    for vers in versions:
        vers = [v[0] for v in vers if is_canonical(v[0])]
        v = [v for v in vers if is_final(v)]
        v = version_sort(v)
        if len(v) > 0:
            r.append(v[-1])
    return r


def _implode(r):
    specs = [''.join(s) for s in r.specs]
    if len(r.extras) == 0:
        return r.name + ','.join(specs)
    extras = '[{}]'.format(','.join(r.extras))
    return r.name + extras + ','.join(specs)


def _write_down(filepath, text):
    tmpfp = filepath + '.tempko2kj22x78'
    f = open(tmpfp, 'w')
    f.write(text)
    f.flush()
    os.fsync(f.fileno())
    f.close()
    os.rename(tmpfp, filepath)
