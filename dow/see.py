def do_see(args):
    d = Dist(args.dist)

    do_pip(d)
    do_conda(d)

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
