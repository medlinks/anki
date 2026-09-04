#!/usr/bin/env python3
"""予備試験 暗記カード — ビルドスクリプト

  cards/*.tsv            … カード原稿（デッキ ⇥ 表 ⇥ 裏 ⇥ メモ ⇥ タグ ⇥ id）
  build/part1_head.html  … HTML の <head> と骨格
  build/part2_script.html… アプリ本体の JavaScript
  static/                … manifest / sw.js / アイコン

  → dist/ に配信用一式を出力する。GitHub Actions がこれを Pages へデプロイする。
"""
import collections, datetime, glob, os, re, shutil, sys

DATE = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
DIST = 'dist'

# ---- 1. カード読み込み＋検証 -------------------------------------------------
files = sorted(glob.glob('cards/*.tsv'))
if not files:
    raise SystemExit('cards/*.tsv が見つかりません')

lines, bad = [], []
for f in files:
    for i, l in enumerate(open(f, encoding='utf-8'), 1):
        l = l.rstrip('\n')
        if not l.strip() or l.lstrip().startswith('#'):
            continue
        if len(l.split('\t')) not in (5, 6):
            bad.append('%s:%d 列数=%d' % (f, i, len(l.split('\t'))))
        lines.append(l)
if bad:
    raise SystemExit('列数が5でも6でもない行があります:\n  ' + '\n  '.join(bad[:15]))

data = '\n'.join(lines)
for ch in ('`', '${', '\\'):
    if ch in data:
        raise SystemExit('テンプレートリテラルを壊す文字が含まれています: %r' % ch)

# カード ID は 6 列目に固定して書いてある（Tools/assign_ids.py が振る）。
# 表の文言を直しても id は変わらないので、記憶曲線は残る。
# 6 列目が無い古い行だけ、以前と同じ「科目＋表」で判定しておく。
def _key(l):
    p = l.split('\t')
    return p[5].strip() if len(p) >= 6 and p[5].strip() else (p[0].split('::')[0], p[1])

dup = [k for k, v in collections.Counter(_key(l) for l in lines).items() if v > 1]
if dup:
    raise SystemExit('ID衝突:\n  ' + '\n  '.join(str(d) for d in dup[:10]))

noid = [l.split('\t')[1][:30] for l in lines
        if len(l.split('\t')) < 6 or not l.split('\t')[5].strip()]
if noid:
    print('⚠️  id 列が空の行が %d 件あります（Tools/assign_ids.py で固定できます）' % len(noid))
    for x in noid[:8]:
        print('     ' + x)

VERSION = '%s (%d枚)' % (DATE, len(lines))

# ---- 2. HTML 組み立て -------------------------------------------------------
head = open('build/part1_head.html', encoding='utf-8').read()
body = open('build/part2_script.html', encoding='utf-8').read().replace('__VERSION__', VERSION)
html = head + '\n<script>\nconst CARD_DATA = `\n' + data + '\n`;\n</script>\n' + body

if os.path.isdir(DIST):
    shutil.rmtree(DIST)
os.makedirs(DIST)
open(os.path.join(DIST, 'index.html'), 'w', encoding='utf-8').write(html)
# オフライン配布用に、同じ中身を単一ファイル名でも置いておく
open(os.path.join(DIST, '予備試験_暗記カード.html'), 'w', encoding='utf-8').write(html)

for f in glob.glob('static/*'):
    name = os.path.basename(f)
    if name == 'sw.js':
        sw = open(f, encoding='utf-8').read()
        sw = re.sub(r"const VERSION = '[^']*';",
                    "const VERSION = '%s';" % VERSION.replace("'", ''), sw)
        open(os.path.join(DIST, name), 'w', encoding='utf-8').write(sw)
    else:
        shutil.copy2(f, os.path.join(DIST, name))

# ---- 3. 文字版（内容チェック用） --------------------------------------------
decks = {}
for l in lines:
    p = l.split('\t')
    decks.setdefault(p[0], []).append(p)
out = ['# 予備試験 暗記カード — 文字版（内容チェック用）', '',
       'バージョン **%s**' % VERSION, '',
       '> アプリに入っているカードと完全に同じ内容です。', '']
for d in sorted(decks):
    out.append('\n## %s　（%d 枚）\n' % (d, len(decks[d])))
    for i, p in enumerate(decks[d], 1):
        out.append('**%d. 表** %s' % (i, p[1]))
        out.append('　　**裏** %s' % p[2])
        if p[3]: out.append('　　💡 %s' % p[3])
        if p[4]: out.append('　　🏷 `%s`' % p[4])
        out.append('')
open(os.path.join(DIST, 'カード一覧.md'), 'w', encoding='utf-8').write('\n'.join(out))

print('✅ build OK   version = %s' % VERSION)
for k in sorted(decks):
    print('   %-26s %3d' % (k, len(decks[k])))
