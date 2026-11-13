"""LINE・SNSで共有したときに出るプレビュー画像（1200×630）を作る。

使い方（LFF フォルダで）:
    python site/tools/make_ogp.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

SITE = Path(__file__).resolve().parents[1]
OUT = SITE / "img"
FONT_B = r"C:\Windows\Fonts\YuGothB.ttc"
FONT_M = r"C:\Windows\Fonts\YuGothM.ttc"
W, H = 1200, 630


def cover(img: Image.Image, top: float = 0.5, inset: float = 0.0) -> Image.Image:
    img = img.convert("RGB")
    if inset:
        dx, dy = int(img.width * inset), int(img.height * inset)
        img = img.crop((dx, dy, img.width - dx, img.height - dy))
    r = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * r) + 1, int(img.height * r) + 1), Image.LANCZOS)
    x = (img.width - W) // 2
    y = int((img.height - H) * top)
    return img.crop((x, y, x + W, y + H))


def card(bg, kicker: str, title: list[str], sub: str, out: str, top: float = 0.5, inset: float = 0.0, dim: float = 0.42) -> None:
    im = Image.new("RGB", (W, H), (17, 17, 19)) if bg is None else cover(Image.open(bg), top, inset)
    im = ImageEnhance.Brightness(im).enhance(dim)
    d = ImageDraw.Draw(im)
    fk = ImageFont.truetype(FONT_M, 30)
    ft = ImageFont.truetype(FONT_B, 76)
    fs = ImageFont.truetype(FONT_M, 32)
    x = 72
    d.ellipse((x, 92, x + 14, 106), fill=(209, 59, 31))
    d.text((x + 28, 80), kicker, font=fk, fill=(235, 235, 232))
    y = 150
    for line in title:
        d.text((x, y), line, font=ft, fill=(255, 255, 255))
        y += 96
    d.text((x, y + 22), sub, font=fs, fill=(220, 220, 216))
    d.text((x, H - 70), "kitsuneudonjp.github.io/lff", font=ImageFont.truetype(FONT_M, 24), fill=(170, 170, 166))
    im.save(OUT / out, "JPEG", quality=88)
    print(out)


card(SITE / "evidence/line/LI13a_1107_0623_tents_on_ground.jpg",
     "検証ノート｜画像と記録で確かめる",
     ["ローカルフードファイト", "in 鳥取で何が起きたのか"],
     "テントはなぜ届かなかったのか。誰がいつ知っていたのか。",
     "ogp.jpg", 0.55, inset=0.09)
card(None,
     "重要資料の開示",
     ["削除された投稿の記録", "主催側が消したもの"],
     "松林安美氏のX・TOSUのX・公式Xの「9.4万人」・チケットショップ",
     "ogp_deleted.jpg", dim=1.0)
card(SITE / "manga/p01.webp",
     "記録まんが｜約6分",
     ["記録でたどる", "ローカルフードファイト"],
     "セリフはすべて実際の書き込みからの引用です。",
     "ogp_manga.jpg", 0.5)
