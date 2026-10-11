"""把 tools/gloss_*.txt（英文單字|中文）合併成 glossary.js，並檢查金句裡的英文字是否都有解釋。

用法：python tools/build_glossary.py
新增或修改金句後執行一次；有缺的字會列出來，補進 gloss_*.txt 再跑一次。
App 端查字時會先查原字，再試著去掉 's / s / es / ies / ed / ing / ly / er / est 找原形（規則與這裡的 base() 相同）。
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

gloss = {}
for f in sorted((ROOT / 'tools').glob('gloss_*.txt')):
    for line in f.read_text(encoding='utf-8').splitlines():
        if '|' in line:
            w, g = line.split('|', 1)
            gloss[w.strip().lower()] = g.strip()

# 取出所有金句中的英文（英文原文，或其他語言的英譯）
js = "global.window={}; require('./quotes.js'); const Q=[...window.QUOTES,...window.QUOTES_PM]; console.log(JSON.stringify(Q.map(q=>q[0]==='en'?q[1]:q[2])))"
texts = json.loads(subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, encoding='utf-8').stdout)
words = set(re.findall(r"[a-z]+(?:'[a-z]+)?", ' '.join(texts).lower().replace('’', "'")))


def base(w, known):
    if w in known:
        return w
    if w.endswith("'s") and w[:-2] in known:
        return w[:-2]
    for suf, rep in [('ies', 'y'), ('es', ''), ('s', ''), ('ied', 'y'), ('ed', ''), ('ed', 'e'), ('ing', ''), ('ing', 'e'), ('ly', ''), ('er', ''), ('est', '')]:
        if w.endswith(suf) and len(w) - len(suf) >= 3 and (w[:-len(suf)] + rep) in known:
            return w[:-len(suf)] + rep
    return None


missing = sorted(w for w in words if base(w, gloss) is None)
out = ROOT / 'glossary.js'
out.write_text('/* 金句英文單字的中文解釋（由 tools/build_glossary.py 產生，不要直接改） */\nwindow.GLOSS=' + json.dumps(gloss, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
print(f'{len(gloss)} entries, {len(words)} words in quotes, missing {len(missing)}')
if missing:
    print(' '.join(missing))
