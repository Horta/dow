import re
from .pip_hash import pip_hash
from .internet import internet_content, clean_html

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
