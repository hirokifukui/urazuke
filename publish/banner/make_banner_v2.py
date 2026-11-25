"""リンク用バナー 第2版（2026-11-24）。サイトでは 446×180 の半分（223×90）で表示されると HP 作成者から連絡があった。
表示の大きさで読める字だけにする：中央に印と URAZUKE（大きく、太く）、下に短い一行だけ。説明の二行と URL は外した。
446×180 と 2倍の 892×360、確認用に表示の大きさの 223×90 も作る。"""
from PIL import Image, ImageDraw, ImageFont
import os
INK, SUB, BG, ACC, FRAME = '#1f2328', '#3d444b', '#ffffff', '#2f4f6f', '#b8b8b8'
MIN = '/System/Library/Fonts/ヒラギノ明朝 ProN.ttc'
def font(px, bold):
    for idx in ((2, 0) if bold else (0,)):   # 2 = ヒラギノ明朝 ProN W6
        try: return ImageFont.truetype(MIN, px, index=idx)
        except Exception: pass
def ctext(d, y, t, f, fill, W):
    d.text(((W - d.textlength(t, font=f)) / 2, y), t, font=f, fill=fill)
def draw(W=446, H=180, S=4):
    W, H = W * S, H * S; s = lambda v: round(v * S)
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W - 1, H - 1], outline=FRAME, width=s(3))
    # 印＋URAZUKE を一塊で中央に（表示 223×90 で字の高さ約 18px）
    fs = 54; f1 = font(s(fs), True); gap = s(5)
    tw = sum(d.textlength(c, font=f1) for c in 'URAZUKE') + gap * 6
    mh = 70; k = mh / 230; mw = s(198 * k); sp = s(18)
    x0 = (W - (mw + sp + tw)) / 2; y0 = s(30)
    X = lambda v: x0 + s(v * k); Y = lambda v: y0 + s(v * k)
    d.rectangle([X(58), Y(58), X(198), Y(230)], fill=ACC)
    d.rectangle([X(0), Y(0), X(157), Y(190)], fill=BG, outline=INK, width=s(22 * k))
    x = x0 + mw + sp; ty = y0 + s(mh / 2) - s(fs * 0.64)
    for c in 'URAZUKE':
        d.text((x, ty), c, font=f1, fill=INK); x += d.textlength(c, font=f1) + gap
    # 下の一行（表示で約 12px）
    d.line([s(70), s(124), W - s(70), s(124)], fill=FRAME, width=s(1.5))
    ctext(d, s(131), '公的統計の検証と記録', font(s(29), True), SUB, W)
    return im
im = draw(); here = os.path.dirname(os.path.abspath(__file__))
for w, h, n in [(446, 180, 'urazuke_banner_446x180_v2.png'), (892, 360, 'urazuke_banner_892x360@2x_v2.png'), (223, 90, 'urazuke_banner_preview_223x90_v2.png')]:
    im.resize((w, h), Image.LANCZOS).save(os.path.join(here, n), optimize=True)
print('ok')
