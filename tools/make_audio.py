"""用 Kokoro（開源神經語音，Apache-2.0）把金句裡的英文預先唸成 MP3，放在 audio/ 給 App 播放。

用法：python tools/make_audio.py            # 只產生還沒有的檔
      python tools/make_audio.py --force    # 全部重做
      python tools/make_audio.py --sample   # 只做幾句試聽
      python tools/make_audio.py --budget 540   # 最多跑 540 秒就存檔停下，再跑一次會接著做

需要：pip install kokoro-onnx soundfile
模型（約 330MB，不放進 repo）：放在 ~/.cache/kokoro/
  model.onnx    ← https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/onnx/model.onnx
  voices/*.bin  ← 同一個 repo 的 voices/（af_heart 等），第一次執行會自動打包成 voices.npz

產出：
  audio/s/<id>.mp3   每句英文（id = 英文句子的 SHA-1 前 12 碼，句子改了就會換新檔）
  audio/w/<字>.mp3   每個英文單字（原形）
  audio/index.json   { "s": {id: 秒數}, "w": [單字…] }，App 用來判斷有沒有音檔
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path.home() / '.cache' / 'kokoro'
OUT = ROOT / 'audio'
VOICE = 'af_heart'        # 美式英語女聲，自然度最高的一個
SENT_SPEED = 0.92         # 句子稍慢一點，方便學習
WORD_SPEED = 0.85
SR = 24000


def load_texts():
    js = "global.window={}; require('./quotes.js'); const Q=[...window.QUOTES,...window.QUOTES_PM]; console.log(JSON.stringify(Q.map(q=>q[0]==='en'?q[1]:q[2])))"
    return json.loads(subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, encoding='utf-8').stdout)


def sid(text):
    return hashlib.sha1(text.strip().encode('utf-8')).hexdigest()[:12]


def main():
    force = '--force' in sys.argv
    sample = '--sample' in sys.argv
    budget = float(sys.argv[sys.argv.index('--budget') + 1]) if '--budget' in sys.argv else 1e9
    t_end = time.time() + budget
    from kokoro_onnx import Kokoro  # 只借用它的英文音素轉換
    if not (CACHE / 'voices.npz').exists():
        vs = {Path(p).stem: np.fromfile(p, dtype=np.float32).reshape(-1, 1, 256) for p in glob.glob(str(CACHE / 'voices' / '*.bin'))}
        np.savez(CACHE / 'voices.npz', **vs)
    kk = Kokoro(str(CACHE / 'model.onnx'), str(CACHE / 'voices.npz'))
    sess = ort.InferenceSession(str(CACHE / 'model.onnx'))
    voice = np.load(CACHE / 'voices.npz')[VOICE]

    def speak(text, speed):
        ph = kk.tokenizer.phonemize(text, 'en-us')
        chunks, audio = [], []
        # 太長就依標點切開（模型一次最多約 510 個音素）
        for part in re.split(r'(?<=[.;:!?])\s+', text) if len(ph) > 480 else [text]:
            p = kk.tokenizer.phonemize(part, 'en-us')
            toks = np.array(kk.tokenizer.tokenize(p), dtype=np.int64)[:510]
            out = sess.run(None, {'input_ids': [[0, *toks, 0]], 'style': np.array(voice[len(toks)], dtype=np.float32), 'speed': np.array([speed], dtype=np.float32)})[0]
            audio.append(np.asarray(out).reshape(-1))
            audio.append(np.zeros(int(SR * 0.18), dtype=np.float32))
        a = np.concatenate(audio[:-1]) if audio else np.zeros(1, dtype=np.float32)
        # 頭尾留一點點空白，淡入淡出避免爆音
        a = np.concatenate([np.zeros(int(SR * 0.05), np.float32), a, np.zeros(int(SR * 0.12), np.float32)])
        f = min(240, len(a) // 4); a[:f] *= np.linspace(0, 1, f); a[-f:] *= np.linspace(1, 0, f)
        return a

    texts = load_texts()
    if sample:
        texts = texts[:4]
    (OUT / 's').mkdir(parents=True, exist_ok=True)
    (OUT / 'w').mkdir(parents=True, exist_ok=True)
    idx_path = OUT / 'index.json'
    idx = json.loads(idx_path.read_text(encoding='utf-8')) if idx_path.exists() and not force else {'s': {}, 'w': []}

    want = {sid(t): t for t in texts}
    done = 0
    save = lambda: idx_path.write_text(json.dumps({**idx, 'voice': VOICE}, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    for i, (k, t) in enumerate(want.items()):
        f = OUT / 's' / f'{k}.mp3'
        if f.exists() and not force:
            if k not in idx['s']:
                idx['s'][k] = round(sf.info(str(f)).duration, 2)
            continue
        if time.time() > t_end:
            save(); print(f'time budget reached at sentence {i}/{len(want)} — run again to continue'); return
        a = speak(t, SENT_SPEED)
        sf.write(f, a, SR, format='MP3', bitrate_mode='VARIABLE', compression_level=0.6)
        idx['s'][k] = round(len(a) / SR, 2)
        done += 1
        if done % 25 == 0:
            save(); print(f'sentences {i + 1}/{len(want)}', flush=True)
    if not sample:  # 句子改掉後留下的舊檔清掉
        for k in list(idx['s']):
            if k not in want:
                idx['s'].pop(k)
                (OUT / 's' / f'{k}.mp3').unlink(missing_ok=True)

    # 單字：金句裡實際出現的每個字（小寫，保留 seeks、studied 這類變化形），加上 glossary 的原形
    gloss = json.loads(re.search(r'window\.GLOSS=(\{.*\});', (ROOT / 'glossary.js').read_text(encoding='utf-8')).group(1))
    surface = set(re.findall(r"[a-z]+(?:'[a-z]+)?", ' '.join(texts).lower().replace('’', "'")))
    words = sorted(w for w in surface | set(gloss) if re.fullmatch(r"[a-z']+", w))
    if sample:
        words = words[:10]
    have = set(idx['w'])
    for n, w in enumerate(words):
        f = OUT / 'w' / f"{w.replace(chr(39), '_')}.mp3"
        if f.exists() and not force:
            have.add(w)
            continue
        if time.time() > t_end:
            idx['w'] = sorted(have); save(); print(f'time budget reached at word {n}/{len(words)} — run again to continue'); return
        sf.write(f, speak(w, WORD_SPEED), SR, format='MP3', bitrate_mode='VARIABLE', compression_level=0.7)
        have.add(w)
        if n % 200 == 0:
            print(f'words {n}/{len(words)}', flush=True)
    idx['w'] = sorted(have & set(words)) if not sample else sorted(have)
    idx['voice'] = VOICE
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    size = sum(p.stat().st_size for p in OUT.rglob('*.mp3'))
    print(f'done: {len(idx["s"])} sentences, {len(idx["w"])} words, {size / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
