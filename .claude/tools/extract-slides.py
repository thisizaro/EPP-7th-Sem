#!/usr/bin/env python3
"""Extract text from .pptx/.docx (OOXML zip) and legacy .ppt (OLE CFB) using only stdlib."""
import sys, os, re, struct, zipfile
import xml.etree.ElementTree as ET

A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

# ---------------- OOXML ----------------
def para_text(p, tag_t):
    return ''.join(t.text or '' for t in p.iter(tag_t))

def extract_pptx(path):
    out = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        def num(n):
            m = re.search(r'(\d+)\.xml$', n)
            return int(m.group(1)) if m else 0
        slides = sorted([n for n in names if re.match(r'ppt/slides/slide\d+\.xml$', n)], key=num)
        for sn in slides:
            idx = num(sn)
            root = ET.fromstring(z.read(sn))
            lines = []
            # walk shapes in document order
            for sp in root.iter(P + 'sp'):
                txt = []
                for p in sp.iter(A + 'p'):
                    t = para_text(p, A + 't').strip()
                    if t:
                        txt.append(t)
                if txt:
                    lines.append(txt)
            # tables
            for tbl in root.iter(A + 'tbl'):
                for tr in tbl.iter(A + 'tr'):
                    cells = []
                    for tc in tr.iter(A + 'tc'):
                        cells.append(' '.join(
                            para_text(p, A + 't').strip() for p in tc.iter(A + 'p')).strip())
                    row = ' | '.join(c for c in cells)
                    if row.strip(' |'):
                        lines.append(['[table] ' + row])
            notes = ''
            nn = 'ppt/notesSlides/notesSlide%d.xml' % idx
            if nn in names:
                nroot = ET.fromstring(z.read(nn))
                ntxt = [para_text(p, A + 't').strip() for p in nroot.iter(A + 'p')]
                ntxt = [t for t in ntxt if t and not re.fullmatch(r'\d+', t)]
                notes = '\n'.join(ntxt)
            out.append((idx, lines, notes))
    return out

def extract_docx(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read('word/document.xml'))
    lines = []
    body = root.find(W + 'body')
    for el in body.iter():
        if el.tag == W + 'p':
            t = para_text(el, W + 't').strip()
            if t:
                lines.append(t)
        elif el.tag == W + 'tbl':
            for tr in el.iter(W + 'tr'):
                cells = [' '.join(para_text(p, W + 't').strip() for p in tc.iter(W + 'p')).strip()
                         for tc in tr.iter(W + 'tc')]
                row = ' | '.join(cells)
                if row.strip(' |'):
                    lines.append('[table] ' + row)
    # dedupe consecutive repeats caused by nested iteration
    res = []
    for l in lines:
        if not res or res[-1] != l:
            res.append(l)
    return res

# ---------------- OLE compound file ----------------
class OLE:
    def __init__(self, data):
        self.d = data
        assert data[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', 'not an OLE file'
        self.ssz = 1 << struct.unpack_from('<H', data, 30)[0]
        self.mssz = 1 << struct.unpack_from('<H', data, 32)[0]
        n_fat = struct.unpack_from('<I', data, 44)[0]
        dir_start = struct.unpack_from('<I', data, 48)[0]
        self.mini_cutoff = struct.unpack_from('<I', data, 56)[0]
        mfat_start = struct.unpack_from('<I', data, 60)[0]
        n_mfat = struct.unpack_from('<I', data, 64)[0]
        difat_start = struct.unpack_from('<I', data, 68)[0]
        n_difat = struct.unpack_from('<I', data, 72)[0]

        difat = list(struct.unpack_from('<109I', data, 76))
        sec = difat_start
        for _ in range(n_difat):
            if sec >= 0xFFFFFFFA:
                break
            blk = self.sector(sec)
            vals = struct.unpack_from('<%dI' % (self.ssz // 4), blk, 0)
            difat.extend(vals[:-1])
            sec = vals[-1]

        self.fat = []
        for s in difat[:n_fat]:
            if s >= 0xFFFFFFFA:
                continue
            blk = self.sector(s)
            self.fat.extend(struct.unpack_from('<%dI' % (self.ssz // 4), blk, 0))

        self.minifat = []
        sec = mfat_start
        for _ in range(n_mfat):
            if sec >= 0xFFFFFFFA:
                break
            blk = self.sector(sec)
            self.minifat.extend(struct.unpack_from('<%dI' % (self.ssz // 4), blk, 0))
            sec = self.fat[sec] if sec < len(self.fat) else 0xFFFFFFFE

        self.dirents = []
        raw = self.chain_data(dir_start)
        for off in range(0, len(raw) - 127, 128):
            e = raw[off:off + 128]
            nlen = struct.unpack_from('<H', e, 64)[0]
            name = e[:max(0, nlen - 2)].decode('utf-16-le', 'ignore')
            typ = e[66]
            start = struct.unpack_from('<I', e, 116)[0]
            size = struct.unpack_from('<Q', e, 120)[0]
            self.dirents.append((name, typ, start, size))
        root = next((d for d in self.dirents if d[1] == 5), None)
        self.ministream = self.chain_data(root[2]) if root else b''

    def sector(self, n):
        off = 512 + n * self.ssz
        return self.d[off:off + self.ssz]

    def chain_data(self, start, fat=None, ssz=None, src=None):
        fat = self.fat if fat is None else fat
        ssz = self.ssz if ssz is None else ssz
        out = bytearray()
        s = start
        seen = set()
        while s < 0xFFFFFFFA and s not in seen:
            seen.add(s)
            if src is None:
                out += self.sector(s)
            else:
                out += src[s * ssz:(s + 1) * ssz]
            s = fat[s] if s < len(fat) else 0xFFFFFFFE
        return bytes(out)

    def stream(self, name):
        for n, typ, start, size in self.dirents:
            if typ == 2 and n == name:
                if size < self.mini_cutoff:
                    return self.chain_data(start, self.minifat, self.mssz, self.ministream)[:size]
                return self.chain_data(start)[:size]
        return None

# ---------------- PowerPoint binary records ----------------
RT_SLIDE, RT_NOTES, RT_MAINMASTER = 0x03EE, 0x03F0, 0x03F8
RT_TEXTHEADER, RT_TEXTCHARS, RT_TEXTBYTES = 0x0F9F, 0x0FA0, 0x0FA8
HTYPE = {0: 'title', 1: 'body', 2: 'notes', 3: 'other', 4: 'other',
         5: 'body', 6: 'title', 7: 'body', 8: 'body'}

def clean(s):
    s = s.replace('\x0b', '\n').replace('\r', '\n').replace('\x00', '')
    s = ''.join(ch for ch in s if ch >= ' ' or ch == '\n' or ch == '\t')
    return s.strip()

def walk(buf, ctx, slides, depth=0):
    off, end = 0, len(buf)
    while off + 8 <= end:
        vi, rt, rl = struct.unpack_from('<HHI', buf, off)
        ver = vi & 0x0F
        body_start = off + 8
        body_end = body_start + rl
        if rl > end - body_start or rl < 0:
            break
        if ver == 0x0F:  # container
            nctx = ctx
            if rt == RT_SLIDE:
                nctx = 'slide'
                slides.append({'kind': 'slide', 'runs': []})
            elif rt == RT_NOTES:
                nctx = 'notes'
                slides.append({'kind': 'notes', 'runs': []})
            elif rt == RT_MAINMASTER:
                nctx = 'master'
            walk(buf[body_start:body_end], nctx, slides, depth + 1)
        else:
            if ctx in ('slide', 'notes') and slides:
                if rt == RT_TEXTHEADER and rl >= 4:
                    slides[-1].setdefault('pending',
                        HTYPE.get(struct.unpack_from('<I', buf, body_start)[0], 'other'))
                    slides[-1]['pending'] = HTYPE.get(
                        struct.unpack_from('<I', buf, body_start)[0], 'other')
                elif rt == RT_TEXTCHARS:
                    t = clean(buf[body_start:body_end].decode('utf-16-le', 'ignore'))
                    if t:
                        slides[-1]['runs'].append((slides[-1].pop('pending', 'other'), t))
                elif rt == RT_TEXTBYTES:
                    t = clean(buf[body_start:body_end].decode('latin-1', 'ignore'))
                    if t:
                        slides[-1]['runs'].append((slides[-1].pop('pending', 'other'), t))
        off = body_end

def extract_ppt(path):
    with open(path, 'rb') as f:
        ole = OLE(f.read())
    doc = ole.stream('PowerPoint Document')
    if doc is None:
        raise RuntimeError('no PowerPoint Document stream')
    slides = []
    walk(doc, 'root', slides)
    return [s for s in slides if s['runs']]

# ---------------- main ----------------
def main():
    for path in sys.argv[1:]:
        ext = os.path.splitext(path)[1].lower()
        base = os.path.basename(path)
        print('\n' + '=' * 78)
        print('FILE: ' + base)
        print('=' * 78)
        try:
            if ext == '.pptx':
                for idx, lines, notes in extract_pptx(path):
                    print('\n--- Slide %d ---' % idx)
                    for shape in lines:
                        for i, t in enumerate(shape):
                            print(('# ' if i == 0 and len(shape) > 0 else '  ') + t)
                    if notes:
                        print('  [NOTES] ' + notes.replace('\n', '\n           '))
            elif ext == '.docx':
                for l in extract_docx(path):
                    print(l)
            elif ext == '.ppt':
                n = 0
                for s in extract_ppt(path):
                    n += 1
                    print('\n--- %s %d ---' % (s['kind'], n))
                    for kind, t in s['runs']:
                        pre = '# ' if kind == 'title' else '  '
                        print(pre + t.replace('\n', '\n  '))
            else:
                print('(unsupported: %s)' % ext)
        except Exception as e:
            print('ERROR: %r' % (e,))

main()
