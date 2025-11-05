#!/usr/bin/env python3
"""
A small msgfmt implementation in Python to compile .po to .mo
Usage: python tools/msgfmt.py locale/es/LC_MESSAGES/django.po
"""
import sys
import os
import struct


def read_po(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    entries = []
    msgid = None
    msgstr = None
    collecting = None
    for line in lines:
        line = line.strip('\n')
        if line.startswith('#') or line.strip() == '':
            if msgid is not None and msgstr is not None:
                entries.append((msgid, msgstr))
                msgid = None
                msgstr = None
                collecting = None
            continue
        if line.startswith('msgid '):
            collecting = 'id'
            msgid = line[6:].strip().strip('"')
            continue
        if line.startswith('msgstr '):
            collecting = 'str'
            msgstr = line[7:].strip().strip('"')
            continue
        if line.startswith('"') and line.endswith('"') and collecting:
            text = line.strip('"')
            if collecting == 'id':
                msgid += text
            elif collecting == 'str':
                msgstr += text
    if msgid is not None and msgstr is not None:
        entries.append((msgid, msgstr))
    return entries


def make_mo(pofile, mofile):
    messages = read_po(pofile)
    # filter out empty msgid
    catalog = {msgid: msgstr for msgid, msgstr in messages if msgid}
    # sort by msgid
    items = sorted(catalog.items())
    ids = []
    strs = []
    for k, v in items:
        ids.append(k.encode('utf-8'))
        strs.append(v.encode('utf-8'))
    # prepare header
    # keys and values must be null-terminated in the blob
    kblob = b"\0".join(ids) + b"\0"
    vblob = b"\0".join(strs) + b"\0"
    keystart = 7 * 4 + 16 * len(ids)
    # offsets in the tables point into the file where blobs start
    # compute per-string lengths and offsets
    offsets = []
    cur = keystart
    for k in ids:
        offsets.append((len(k), cur))
        cur += len(k) + 1  # include null terminator
    valuestart = cur
    valoffsets = []
    for v in strs:
        valoffsets.append((len(v), cur))
        cur += len(v) + 1
    # write header (use little-endian '<' to ensure standard MO format)
    with open(mofile, 'wb') as of:
        # magic
        of.write(struct.pack('<I', 0x950412de))
        # version
        of.write(struct.pack('<I', 0))
        # number of strings
        of.write(struct.pack('<I', len(ids)))
        # offset of table with original strings
        of.write(struct.pack('<I', keystart))
        # offset of table with translation strings
        of.write(struct.pack('<I', valuestart))
        # size/offset of hash table (unused)
        of.write(struct.pack('<I', 0))
        of.write(struct.pack('<I', 0))
        # tables (each entry: length, offset) little-endian
        for l, o in offsets:
            of.write(struct.pack('<II', l, o))
        for l, o in valoffsets:
            of.write(struct.pack('<II', l, o))
        # blobs
        of.write(kblob)
        of.write(vblob)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: msgfmt.py POFILE [MOFILE]')
        sys.exit(1)
    pofile = sys.argv[1]
    mofile = sys.argv[2] if len(sys.argv) > 2 else pofile[:-3] + '.mo'
    os.makedirs(os.path.dirname(mofile), exist_ok=True)
    make_mo(pofile, mofile)
    print('Wrote', mofile)
