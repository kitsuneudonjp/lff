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
#
# 松林安美氏の X（@ms759sk）は 2026-11-12 にアカウントごと削除された。
# 削除前の記録として、本文の画面はすべて加工せずに公開する（ユーザー指示 2026-11-13）。
# 切り落とすのは左右の列（閲覧者のアカウント表示・おすすめ欄）だけ。
ARCHIVE_SKIP = {
    "06_DfildE2H3rq_b.jpg", "07_Dfi1o6Gn7pG_b.jpg", "07_Dfi1o6Gn7pG_c.jpg",
    "07_Dfi1o6Gn7pG_d.jpg", "07_Dfi1o6Gn7pG_e.jpg",
}
# 黒塗りする範囲（1440px 幅の元画像の座標）：健康状態に触れる文
# 黒塗りする範囲（1440px 幅の元画像の座標）
REDACT = {
    # プロフィールの「〇〇さんにフォローされています」は、閲覧者（このサイトの作成者）のつながりが分かるので消す
    "00_profile_20261111.jpg": [(368, 552, 950, 584)],
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


# さよと氏が 2026-08-03 に X へ投稿した募集チラシ（表・裏）。
# X の画像ビューアのスクショから、チラシの部分だけを切り出す（周りには閲覧者のアカウント表示が写る）。
# 裏面の右下にある人物写真3枚は、主張の裏付けに要らないので黒塗りにする。
FLYER_BOX = (487, 0, 954, 661)          # 1440px 幅の元画像でのチラシの範囲
FLYER = {
    "00a_2084031304883163524_photo1.jpg": ("flyer_20260803_front.jpg", []),
    "00a_2084031304883163524_photo2.jpg": ("flyer_20260803_back.jpg", [(718, 526, 952, 624)]),
}


def export_flyer() -> None:
    dst = ROOT / "site" / "evidence" / "sns" / "x_1123sayoto"
    dst.mkdir(parents=True, exist_ok=True)
    for name, (out_name, boxes) in FLYER.items():
        im = Image.open(ARCHIVE / "x_1123sayoto" / name).convert("RGB")
        scale = im.size[0] / 1440
        for (x0, y0, x1, y1) in boxes:
            im.paste((0, 0, 0), (int(x0 * scale), int(y0 * scale), int(x1 * scale), int(y1 * scale)))
        im = im.crop(tuple(int(v * scale) for v in FLYER_BOX))
        im.save(dst / out_name, "JPEG", quality=92)   # メタデータは書き出さない
        print(f"sns/x_1123sayoto/{out_name}  {im.size}")


# 削除を確認した画面（2026-11-12 21:08 JST）。中央の列の上の部分だけを切り出す。
DELETED_SRC = ARCHIVE / "watch" / "deleted"
DELETED_BOX = (356, 0, 955, 250)


def export_deleted() -> None:
    dst = ROOT / "site" / "evidence" / "sns" / "x_ms759sk" / "deleted"
    dst.mkdir(parents=True, exist_ok=True)
    for p in sorted(DELETED_SRC.glob("20261112_2108_*.jpg")):
        im = Image.open(p).convert("RGB")
        scale = im.size[0] / 1440
        im = im.crop(tuple(int(v * scale) for v in DELETED_BOX))
        im.save(dst / p.name, "JPEG", quality=90)   # メタデータは書き出さない
        print(f"sns/x_ms759sk/deleted/{p.name}  {im.size}")


# 2026-11-13 の削除調査で見つけたもの（archive/20261113_deletion_investigation.md）。
# Wayback Machine の記録画面は投稿カードの部分だけ、BASE と X の画面はそのまま使う。
# どの画面にも閲覧者のアカウント表示は写っていない（Wayback と BASE はログインなしの表示、X は中央の列だけを撮影）。
FOUND_SRC = ARCHIVE / "watch" / "deleted"
FOUND = {
    "20261113_wayback_localfoodfight_2109909971098120393_94000.jpg": ("lff_x_2109909971098120393_wayback.jpg", (395, 150, 1045, 545)),
    "20261113_wayback_localfoodfight_2110221559415930956_94000.jpg": ("lff_x_2110221559415930956_wayback.jpg", (395, 150, 1045, 550)),
    "20261113_x_localfoodfight_2110221559415930956_now.png": ("lff_x_2110221559415930956_now.jpg", None),
    "20261113_wayback_sayoto_RT_tosukurayoshi_0909.jpg": ("tosu_x_rt_0909_wayback.jpg", (395, 150, 1045, 709)),
    "20261113_wayback_sayoto_RT_tosukurayoshi_1015.jpg": ("tosu_x_rt_1015_wayback.jpg", (395, 150, 1045, 709)),
    "20261113_base_shop_top_no_items.jpg": ("base_shop_20261113_top.jpg", None),
    "20261113_base_shop_law.jpg": ("base_shop_20261113_law.jpg", None),
}


def export_found() -> None:
    dst = ROOT / "site" / "evidence" / "sns" / "deleted_20261113"
    dst.mkdir(parents=True, exist_ok=True)
    for name, (out_name, box) in FOUND.items():
        im = Image.open(FOUND_SRC / name).convert("RGB")
        if box:
            scale = im.size[0] / 1440
            im = im.crop(tuple(int(v * scale) for v in box))
        im.save(dst / out_name, "JPEG", quality=90)   # メタデータは書き出さない
        print(f"sns/deleted_20261113/{out_name}  {im.size}")


# 2026-11-13 に受け取った資料（evidence/line/LI20〜LI24）。
# 黒塗り：口座番号、銀行の企業コード・受付番号・顧客番号、携帯番号、業者の担当者名・納品先の担当者名。
# 座標は元画像のピクセル（縮小しない）。
NEW_LINE = {
    "LI20_": ("LI20_axis_line_55man_account_not_opened_1004.jpg", []),
    "LI21_": ("LI21_axis_estimate_consulting_fee_1070000.jpg", []),
    "LI22a_": ("LI22a_duskin_estimate_1102_2936780yen.jpg", [
        (395, 498, 540, 526),     # 携帯番号
        (615, 208, 735, 236),     # 業者の担当者名
        (290, 582, 360, 608),     # 納品先の担当者名
    ]),
    "LI22e_": ("LI22e_duskin_estimate_unit_prices.jpg", []),
    "LI23a_": ("LI23a_order_group_1104_maruchou_598400yen.jpg", [
        (110, 245, 205, 290),     # 受取口座の番号
        (405, 893, 462, 930),     # グループに追加された個人の表示名
    ]),
    "LI23b_": ("LI23b_order_group_1104_tosu_transfer_598400yen.jpg", [
        (685, 398, 785, 428),     # 業者の担当者名
        (425, 818, 545, 848),     # 顧客番号
        (500, 838, 640, 866),     # 企業コード
        (560, 965, 820, 1012),    # 受付No・企業コード
        (560, 1040, 640, 1062),   # 受付番号
        (680, 1095, 800, 1125),   # 出金口座の番号
        (690, 1155, 800, 1185),   # 入金口座の番号
    ]),
    "LI24_": ("LI24_tosu_transfer_1105_jnet_114000yen_requester_axis.jpg", [
        (0, 0, 1108, 30),         # 企業コード（上端）
        (470, 285, 820, 365),     # 受付No・企業コード
        (430, 440, 560, 480),     # 受付番号
        (620, 495, 800, 560),     # 出金口座の番号
        (640, 600, 760, 660),     # 入金口座の番号
    ]),
}


def export_new_line() -> None:
    sources = {p.name: p for p in SRC.glob("LI2*.jpg")}
    for prefix, (out_name, boxes) in NEW_LINE.items():
        match = [p for n, p in sources.items() if n.startswith(prefix)]
        if len(match) != 1:
            print(f"skip {prefix}: {len(match)} matches")
            continue
        im = Image.open(match[0]).convert("RGB")
        for box in boxes:
            im.paste((0, 0, 0), box)
        im.save(DST / out_name, "JPEG", quality=90)   # メタデータは書き出さない
        print(f"{out_name}  {im.size}")


def main() -> None:
    export_archive()
    export_deleted()
    export_found()
    DST.mkdir(parents=True, exist_ok=True)
    export_new_line()
    export_flyer()
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
