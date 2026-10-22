"""畫出時屜的 App 圖示（與 index.html 裡的 LOGO SVG 同一個圖形），輸出各種尺寸。

用法：python tools/make_icons.py

產生（覆蓋）：
  icons/source-1024.png                    滿版原圖
  icons/icon-192.png、icons/icon-512.png   圓角版（manifest purpose: any、網頁 favicon）
  icons/maskable-512.png                   滿版、主體縮到 80%（Android 自適應圖示會再裁成圓形）
  icons/apple-touch-icon.png               180x180 滿版（iOS 會自己加圓角）

圖形：三個抽屜，抽屜之間留白；中間那格被拉出來（＝此刻打開的抽屜），把手是橘色。
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / 'icons'
SS = 4  # 超取樣倍數，邊緣比較乾淨


def hexrgb(h, a=255):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def draw(size=1024, inset=1.0):
    S = size * SS
    k = S / 1024 * inset
    off = S * (1 - inset) / 2
    R = lambda x0, y0, x1, y1: [off + x0 * k, off + y0 * k, off + x1 * k, off + y1 * k]

    # 底色：長流橘（與長流、細水同一個橘），上淺下深
    top, bot = hexrgb('#FB9042'), hexrgb('#EC6512')
    img = Image.new('RGBA', (S, S))
    px = ImageDraw.Draw(img)
    for y in range(S):
        t = y / (S - 1)
        px.line([(0, y), (S, y)], fill=tuple(round(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,))

    def layer(fn, blur=0):
        lay = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        fn(ImageDraw.Draw(lay))
        if blur:
            lay = lay.filter(ImageFilter.GaussianBlur(blur * k))
        img.alpha_composite(lay)

    # 上下兩格：收著的抽屜
    for y0 in (232, 642):
        layer(lambda d, y0=y0: d.rounded_rectangle(R(236, y0, 788, y0 + 150), radius=44 * k, fill=hexrgb('#FFF4EA', 128)))
        layer(lambda d, y0=y0: d.rounded_rectangle(R(452, y0 + 64, 572, y0 + 86), radius=11 * k, fill=hexrgb('#C85A0E', 140)))
    # 中間：拉出來的抽屜（陰影＋面板＋金色把手）
    layer(lambda d: d.rounded_rectangle(R(200, 440, 824, 620), radius=50 * k, fill=hexrgb('#7A2E05', 90)), blur=26)
    layer(lambda d: d.rounded_rectangle(R(190, 414, 834, 600), radius=50 * k, fill=hexrgb('#FFF4EA')))
    layer(lambda d: d.rounded_rectangle(R(427, 492, 597, 522), radius=15 * k, fill=hexrgb('#F2711C')))
    return img.resize((size, size), Image.LANCZOS)


def rounded(img, radius=0.23):
    big = img.resize((img.size[0] * 4, img.size[1] * 4), Image.LANCZOS)
    mask = Image.new('L', big.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, big.size[0] - 1, big.size[1] - 1], radius=int(big.size[0] * radius), fill=255)
    big.putalpha(mask)
    return big.resize(img.size, Image.LANCZOS)


def main():
    ICONS.mkdir(exist_ok=True)
    src = draw(1024)
    src.convert('RGB').save(ICONS / 'source-1024.png')
    rounded(draw(192)).save(ICONS / 'icon-192.png')
    rounded(draw(512)).save(ICONS / 'icon-512.png')
    draw(512, inset=0.8).convert('RGB').save(ICONS / 'maskable-512.png')
    draw(180).convert('RGB').save(ICONS / 'apple-touch-icon.png')
    print('icons written to', ICONS)


if __name__ == '__main__':
    main()
