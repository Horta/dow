class Setupcfg(object):
    def __init__(self, filename):
        with open(filename, 'r') as f:
            rows = f.read().split('\n')
            rows = [r.strip() for r in rows]
        self._rows = rows

    def exists(self, what):
        for r in self._rows:
            if '=' not in r:
                continue
            if r.split('=')[0].strip() == what:
                return True
        return False

    def get(self, what):
        for r in self._rows:
            if '=' not in r:
                continue
            if r.split('=')[0].strip() == what:
                return r.split('=')[1].strip()
        return None
