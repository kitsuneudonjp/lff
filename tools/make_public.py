"""非公開の証拠画像から、公開用のコピーを作る。

使い方（LFF フォルダで）:
    python site/tools/make_public.py

やること:
- LINE画像ビューアの上部バー（投稿者名・グループ名が写る）を切り落とす
- EXIF などのメタデータを付けずに保存し直す
- 出力先は site/evidence/line/。ファイル名は台帳の ID にそろえる
公開しない画像（人物が近くに写るもの、出店者名が写るもの）は、ここに載せない。
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "evidence" / "line"
DST = ROOT / "site" / "evidence" / "line"
TOP_CROP = 0.10      # ビューア上部バーの高さ（画像の高さに対する割合）
BOTTOM_CROP = 0.08   # 下部のリアクション（反応した人のアイコン）

# 公開する画像: 元ファイル名の先頭 → 公開名
PUBLIC = {
    "LI02_": "LI02_1103_matsubayashi_to_axis_55man.jpg",
    "LI03a_": "LI03a_prepayment_invoice_2936780yen_due1102.jpg",
    "LI03b_": "LI03b_invoice_items.jpg",
    "LI04_": "LI04_vendor_mail_1102_no_payment.jpg",
    "LI05_": "LI05_axis_status_list_refrigerated_trucks_arranged.jpg",
    "LI07a_": "LI07a_health_center_booth_layout.jpg",
    "LI07b_": "LI07b_required_equipment_layout.jpg",
    "LI12b_": "LI12b_1107_0834_venue_1.jpg",
    "LI12c_": "LI12c_1107_0834_venue_2.jpg",
    "LI12d_": "LI12d_1107_0834_venue_3.jpg",
    "LI12e_": "LI12e_1107_0803_venue.jpg",
    "LI12f_": "LI12f_1107_0745_vip_tent.jpg",
    "LI13a_": "LI13a_1107_0623_tents_on_ground.jpg",
    "LI13b_": "LI13b_1107_0622_venue_early.jpg",
    "LI16_": "LI16_1104_venue_map.jpg",
    "LI17a_": "LI17a_flyer_back_program.jpg",
    "LI17b_": "LI17b_flyer_front.jpg",
}


ARCHIVE = ROOT / "archive"
# SNSのスクショは、閲覧者（このサイトの作成者）のアカウント表示やフォロー状態が
# 左右の列に写るので、投稿本体の中央の列だけを切り出す。(left, right) は 1440px 幅のときの x 座標。
ARCHIVE_PUBLIC = [
    ("x_ms759sk", "*.jpg", (356, 955), "sns/x_ms759sk"),
    ("threads_axis.nao.official", "*.jpg", (385, 1025), "sns/threads_axis"),
    ("threads_sayoto2tyan", "01_timeline_06.jpg", (385, 1025), "sns/threads_sayoto2tyan"),
]
# 公開しないもの：
# - プロフィール画面（「〇〇さんにフォローされています」「フォロー中」が出て、閲覧者のつながりが分かる）
# - 健康・家族・第三者の年齢に触れる部分を含む画面
# - 第三者の返信が並ぶ返信欄
ARCHIVE_SKIP = {
    "00_with_replies_tab_halfsize.jpg", "00_profile_20261111.jpg",
    "01_2120317312121368663_c.jpg", "03_2120329698169569573_b.jpg",
    "06_DfildE2H3rq_b.jpg", "07_Dfi1o6Gn7pG_b.jpg", "07_Dfi1o6Gn7pG_c.jpg",
    "07_Dfi1o6Gn7pG_d.jpg", "07_Dfi1o6Gn7pG_e.jpg",
}
# 黒塗りする範囲（1440px 幅の元画像の座標）：健康状態に触れる文
REDACT = {
    "01_2120317312121368663_a.jpg": [(360, 158, 950, 214)],
    "01_2120317312121368663_b.jpg": [(360, 618, 950, 694)],   # 入院・家族について
}


import re
import shutil

# AXIS の Threads は、本人の投稿本体（_a と、連投の続き）だけを公開する。
# 返信欄（第三者）・引用された他人の画像・オープンチャットのスクショ（11_）は出さない。
AXIS_ALLOW = re.compile(r"^(0[1-9]|10|12)_.*_a\.jpg$|^08_.*_[bc]\.jpg$|^12_.*_[bc]\.jpg$")  # 12_d/e・13 は第三者の返信が写るので出さない


def allowed(folder: str, name: str) -> bool:
    if name in ARCHIVE_SKIP:
        return False
    if folder == "threads_axis.nao.official":
        return bool(AXIS_ALLOW.match(name))
    return True


def export_archive() -> None:
    for folder, pattern, (left, right), out in ARCHIVE_PUBLIC:
        dst = ROOT / "site" / "evidence" / out
        shutil.rmtree(dst, ignore_errors=True)
        dst.mkdir(parents=True, exist_ok=True)
        for p in sorted((ARCHIVE / folder).glob(pattern)):
            if not allowed(folder, p.name):
                continue
            im = Image.open(p).convert("RGB")
            w, h = im.size
            scale = w / 1440
            for (x0, y0, x1, y1) in REDACT.get(p.name, []):
                im.paste((0, 0, 0), (int(x0 * scale), int(y0 * scale), int(x1 * scale), int(y1 * scale)))
            im = im.crop((int(left * scale), 0, int(right * scale), h))
            im.save(dst / p.name, "JPEG", quality=90)
            print(f"{out}/{p.name}  {im.size}")


def main() -> None:
    export_archive()
    DST.mkdir(parents=True, exist_ok=True)
    sources = {p.name: p for p in SRC.glob("*.jpg")}
    for prefix, out_name in PUBLIC.items():
        match = [p for n, p in sources.items() if n.startswith(prefix)]
        if len(match) != 1:
            print(f"skip {prefix}: {len(match)} matches")
            continue
        im = Image.open(match[0]).convert("RGB")
        w, h = im.size
        im = im.crop((0, int(h * TOP_CROP), w, int(h * (1 - BOTTOM_CROP))))
        im.save(DST / out_name, "JPEG", quality=90)   # メタデータは書き出さない
        print(f"{out_name}  {im.size}")


if __name__ == "__main__":
    main()
