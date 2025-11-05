#!/usr/bin/env python3
"""
A small msgfmt implementation in Python to compile .po to .mo
Usage: python tools/msgfmt.py locale/es/LC_MESSAGES/django.po
"""
import sys
import os
import struct
import ast


def read_po(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    entries = []
    msgid = None
    msgstr = None
    in_msgid = False
    in_msgstr = False

    def flush_entry():
        nonlocal msgid, msgstr, in_msgid, in_msgstr
        if msgid is not None and msgstr is not None:
            entries.append((msgid, msgstr))
        msgid = None
        msgstr = None
        in_msgid = False
        in_msgstr = False

    for raw_line in lines:
        line = raw_line.rstrip('\n')
        stripped = line.strip()
        if stripped.startswith('#') or stripped == '':
            if stripped == '' and msgid is not None and msgstr is not None:
                flush_entry()
            continue
        if line.startswith('msgid '):
            flush_entry()
            in_msgid = True
            in_msgstr = False
            msgid = ast.literal_eval(line[5:].strip())
            continue
        if line.startswith('msgstr '):
            in_msgid = False
            in_msgstr = True
            msgstr = ast.literal_eval(line[6:].strip())
            continue
        if line.startswith('"') and line.endswith('"'):
            text = ast.literal_eval(line.strip())
            if in_msgid and msgid is not None:
                msgid += text
            elif in_msgstr and msgstr is not None:
                msgstr += text
            continue
        # Any other directive (msgctxt, plurals) not supported; flush to avoid corruption
        flush_entry()

    if msgid is not None and msgstr is not None:
        flush_entry()
    return entries


def make_mo(pofile, mofile):
    messages = read_po(pofile)
    catalog = {}
    for msgid, msgstr in messages:
        if msgid is None or msgstr is None:
            continue
        catalog[msgid] = msgstr
    # sort by msgid (header entry with empty msgid stays first)
    items = sorted(catalog.items(), key=lambda item: item[0])
    ids = []
    strs = []
    for k, v in items:
        ids.append(k.encode('utf-8'))
        strs.append(v.encode('utf-8'))
    header_size = 7 * 4
    orig_table_offset = header_size
    trans_table_offset = orig_table_offset + len(ids) * 8
    string_data_offset = trans_table_offset + len(ids) * 8

    offsets = []
    cur = string_data_offset
    for k in ids:
        offsets.append((len(k), cur))
        cur += len(k) + 1

    valoffsets = []
    for v in strs:
        valoffsets.append((len(v), cur))
        cur += len(v) + 1

    with open(mofile, 'wb') as of:
        # magic
        of.write(struct.pack('<I', 0x950412de))
        # version
        of.write(struct.pack('<I', 0))
        # number of strings
        of.write(struct.pack('<I', len(ids)))
        # offset of table with original strings
        of.write(struct.pack('<I', orig_table_offset))
        # offset of table with translation strings
        of.write(struct.pack('<I', trans_table_offset))
        # size/offset of hash table (unused)
        of.write(struct.pack('<I', 0))
        of.write(struct.pack('<I', 0))
        # tables (each entry: length, offset) little-endian
        for l, o in offsets:
            of.write(struct.pack('<II', l, o))
        for l, o in valoffsets:
            of.write(struct.pack('<II', l, o))
        # blobs (null-terminated)
        for k in ids:
            of.write(k + b'\0')
        for v in strs:
            of.write(v + b'\0')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: msgfmt.py POFILE [MOFILE]')
        sys.exit(1)
    pofile = sys.argv[1]
    mofile = sys.argv[2] if len(sys.argv) > 2 else pofile[:-3] + '.mo'
    os.makedirs(os.path.dirname(mofile), exist_ok=True)
    make_mo(pofile, mofile)
    print('Wrote', mofile)
