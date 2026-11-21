"""リンク用バナー（446×180、2倍の 892×360 も）。SOMEC のサイドバーで KMRI のバナーの下に置く想定（2026-11-21）。
KMRI と同じ組み方：白地・灰色の枠、上に分野の一行、中央に印と名前、下に説明の一行。意匠は og.png と同じ（重なる二つの矩形、字間を空けた明朝）。"""
from PIL import Image, ImageDraw, ImageFont
import os
INK, SUB, BG, ACC, FRAME = '#1f2328', '#5d646b', '#ffffff', '#2f4f6f', '#c4c4c4'
MIN = '/System/Library/Fonts/ヒラギノ明朝 ProN.ttc'
def ctext(d, y, t, f, fill, W, s):
    d.text(((W * s - d.textlength(t, font=f)) / 2, y * s), t, font=f, fill=fill)
def draw(W=446, H=180, S=4):
    im = Image.new('RGB', (W * S, H * S), BG); d = ImageDraw.Draw(im); s = lambda v: round(v * S)
    d.rectangle([0, 0, W * S - 1, H * S - 1], outline=FRAME, width=s(2))
    ctext(d, 16, '公的な統計と資料の検証・記録', ImageFont.truetype(MIN, s(16), index=0), INK, W, S)
    # 中央：印＋URAZUKE を一塊で中央に
    f1 = ImageFont.truetype(MIN, s(46), index=0); gap = s(9)
    tw = sum(d.textlength(c, font=f1) for c in 'URAZUKE') + gap * 6
    mh = 66; k = mh / 230; mw = s(198 * k); sp = s(22)
    x0 = (W * S - (mw + sp + tw)) / 2; y0 = s(48)
    X = lambda v: x0 + s(v * k); Y = lambda v: y0 + s(v * k)
    d.rectangle([X(58), Y(58), X(198), Y(230)], fill=ACC)
    d.rectangle([X(0), Y(0), X(157), Y(190)], fill=BG, outline=INK, width=s(15 * k))
    x = x0 + mw + sp; ty = y0 + s(mh / 2) - s(46 * 0.62)
    for c in 'URAZUKE':
        d.text((x, ty), c, font=f1, fill=INK); x += d.textlength(c, font=f1) + gap
    ctext(d, 128, '犯罪・司法・精神医療・福祉の公開データを、', ImageFont.truetype(MIN, s(13.5), index=0), SUB, W, S)
    ctext(d, 149, '再現できる方法で検証し、記録する　urazuke.org', ImageFont.truetype(MIN, s(13.5), index=0), SUB, W, S)
    return im
im = draw(); here = os.path.dirname(os.path.abspath(__file__))
im.resize((446, 180), Image.LANCZOS).save(os.path.join(here, 'urazuke_banner_446x180.png'), optimize=True)
im.resize((892, 360), Image.LANCZOS).save(os.path.join(here, 'urazuke_banner_892x360@2x.png'), optimize=True)
print('ok')
