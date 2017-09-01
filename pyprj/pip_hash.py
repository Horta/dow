import hashlib

def pip_hash(c):
    return hashlib.sha256(c).hexdigest()
