import re

def is_canonical(version):
    expr = r'^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*'
    expr += '((a|b|rc)(0|[1-9]\d*))?(\.post(0|[1-9]\d*))?(\.dev(0|[1-9]\d*))?$'
    return re.match(expr, version) is not None
