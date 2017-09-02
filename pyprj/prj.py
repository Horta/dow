from os.path import exists, join
from setuptools import find_packages
import subprocess
from .internet import extract_urls, check_url
from .setupcfg import Setupcfg
import rstcheck
from .printf import printe, printg
from glob import glob

class Prj(object):
    def __init__(self):
        data = dict()
        data['license'] = check_get_files(['LICENSE.txt', 'LICENSE'])
        data['readme'] = check_get_files(['README.rst', 'README.md'])
        data['manifest'] = check_get_files(['MANIFEST.in'])
        data['setup.py'] = check_get_files(['setup.py'])
        data['setup.cfg'] = check_get_files(['setup.cfg'])
        self._data = data

    def check_urls(self):
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
        pkgs = find_packages()
        if len(pkgs) == 0:
            return
    
        pkg = pkgs[0]
        with open(join(pkg, '__init__.py'), 'r') as f:
            rows = [r.strip() for r in f.read().split('\n')]
    
        look_for = ['__name__', '__version__', '__author__', '__author_email__']
        found = {lf:False for lf in look_for}
        for r in rows:
            for lf in look_for:
                if r.startswith(lf):
                    found[lf] = True
    
        if not all(found.values()):
            printe("Could not find " + ', '.join(lk for lk in look_for if not found[lk]))

    def check_setupcfg(self):
        if self._data['setup.cfg'] is None:
            return

        data = self._data
        s = Setupcfg(data['setup.cfg'])
    
        if data['readme'] and s.exists('description_file'):
            fn = s.get('description_file')
            if fn != data['readme']:
                printe('setup.cfg description_file is pointing to %s instead of %s.' % (fn, data['readme']))
    
    def check_manifest(self):
        if self._data['manifest'] is None:
            return
    
        data = self._data
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
    
    def check_package_exists(self):
        pkgs = find_packages()
        if len(pkgs) == 0:
            printe("No Python package could be found at %s." % here())

def check_get_files(filenames):
    if not any(exists(f) for f in filenames):
        printe("Could not find " + ' nor '.join(filenames) + " file(s).")
    else:
        return next(f for f in filenames if exists(f))
