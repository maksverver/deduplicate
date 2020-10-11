#!/usr/bin/env python

import codecs
import hashlib
import json
import os
import sys

READ_BLOCK_SIZE = 65536

digests = {}  # path -> digest


def CalculateFileDigest(f):
    h = hashlib.sha256()
    while True:
        chunk = f.read(READ_BLOCK_SIZE)
        if chunk:
            h.update(chunk)
        else:
            break # EOF reached
    return h.digest()


def CalculateDirDigest(content_digests):
    h = hashlib.sha256()
    for chunk in sorted(content_digests):
        h.update(chunk)
    return h.digest()


def Main(top_dirs, output=sys.stdout):
    for top_dir in top_dirs:
        for (dirpath, dirnames, filenames) in os.walk(top_dir.rstrip('/'), topdown=False, followlinks=False):
            content_digests = []
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                assert filepath not in digests
                try:
                    f = open(filepath, 'rb')
                except OSError:
                    # Happens if we don't have permission to read the file.
                    print('Cannot open', filepath, file=sys.stderr)
                else:
                    with f:
                        digest = CalculateFileDigest(f)
                    digests[filepath] = digest
                    content_digests.append(digest)
            for dirname in dirnames:
                subdirpath = os.path.join(dirpath, dirname) + '/'
                try:
                    content_digests.append(digests[subdirpath])
                except KeyError:
                    # Happens if the we didn't have permission to read the directory.
                    print('Missing digest for directory', subdirpath, file=sys.stderr)
            assert not dirpath.endswith('/')
            assert dirpath not in digests  # can't be both a file and directory
            assert dirpath + '/' not in digests
            digests[dirpath + '/'] = CalculateDirDigest(content_digests)

    for path in sorted(digests):
        obj = {'path': path, 'sha256': digests[path].hex()}
        json.dump(obj, output)
        output.write('\n')

if len(sys.argv) <= 1:
    print('Usage: index.py <directory>+')
    sys.exit(1)

Main(sys.argv[1:])

