"""「記録の一覧」ページ（site/records.html）と、公開用の記録ファイル（site/records/）を作る。

使い方（LFF フォルダで）:
    python site/tools/make_public.py
    python site/tools/build_records.py
    python -I site/tools/manifest.py

- 出店者用チャット：11/11 17:39 版（それまでの送信者名がそろっている）に、11/13 10:15 版のそれ以降を足す。
  主催側・設営会社以外の参加者は「出店者A」などの記号にする（検証ノート本文の記号と同じ人には同じ記号）。
- 「発注確認」グループ：TOSUのスタッフ・AXISの関係者の個人名を伏せる。
- 電話番号・メールアドレス・招待リンクは伏せる。
"""
import re
import shutil
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
OUT = SITE / "records"
CHAT_OLD = ROOT / "1111-1739.txt"
CHAT_NEW = ROOT / "2026-11-13" / "[LINE]LFFin鳥取出店者グループ (1015).txt"
ORDER = ROOT / "evidence" / "files" / "F03_LINE発注確認グループ_1104-1109_保存1113-1010.txt"

ORG = {  # 主催側・設営会社（実名のまま）
    "LFF事務局": "LFF事務局（主催）", "合同会社TOSU事務局": "合同会社TOSU事務局（主催）",
    "成瀬_合同会社TOSU事務局": "合同会社TOSU事務局（主催）",
    "小澤瞬大_実行委員": "小澤瞬大氏（主催）", "さよと": "さよと氏（主催）",
    "（株）AXIS": "AXIS（設営会社）", "株式会社AXIS": "AXIS（設営会社）",
}
# 検証ノート本文で使っている記号（同じ人に同じ記号）
FIXED = {
    "Re:make Re:make": "A", "酒井謙心": "B", "丼ぶり屋幸丼": "B", "ルナパンナ　中冨": "C", "石村 @ルナパンナ": "C",
    "Tea jack②": "D", "teajack": "D", "栗処くりと": "E", "五島牛専門店ばらもん": "F", "クライチ": "G",
    "からあげ専門店鶏笑東出雲店": "H", "ロングバケーションリゾート": "K",
}
SENDERS = [  # 送信者名（長いものから照合する）
    "Re:make Re:make", "ルナパンナ　中冨", "石村 @ルナパンナ", "OREGA26  鈴木", "M's  store", "健屋　山西",
    "ベビーカステラ専門店MOGMOG 塚本", "吉岡/鳥取/ごっつお神楽", "松井酒造　岩佐", "阿出川直樹_デリカリカフェ",
    "小島慎司_Webとりーみんぐ", "からあげ専門店鶏笑東出雲店", "五島牛専門店ばらもん", "くれぇぷ＆ガレットねぇねぇ。",
    "チューハイスタンドKUKURU", "ロングバケーションリゾート", "成瀬_合同会社TOSU事務局", "合同会社TOSU事務局",
    "小澤瞬大_実行委員", "博多唐揚げ官兵衛", "おむすびにぎにぎ", "キッチンきりん組", "ベビーカステラtete",
    "三雅（みやび）", "縁溜しめなわ号", "丼ぶり屋幸丼", "craft kitchen", "（株）AXIS", "株式会社AXIS", "LFF事務局",
    "ごっつお神楽", "五島牛専門店", "松井酒造福井", "Tea jack②", "四国屋台村", "comedor🌮", "栗処くりと", "山崎商店",
    "トリベイ2", "トリベイ", "BBCやたべ", "ナカタケイジ", "塩田海斗", "酒井謙心", "クライチ", "コンセプト", "タコフク",
    "まるた", "Kazu-Y", "teajack", "Unknown", "うたか", "たけし", "ゆーた", "咲香", "翔太", "山田", "匿名", "sken",
    "amal", "さよと", "健屋", "Sth", "ttr", "NB", "t", "。",
]
# 本文中に出てくる店名・個人名（表記ゆれも）→ 送信者名
TEXT_NAMES = {
    "ごっつお神楽ホールディングス": "吉岡/鳥取/ごっつお神楽", "ごっつお×神楽": "ごっつお神楽", "ごっつお倉吉店": "ごっつお神楽",
    "ごっつお神楽グループ": "ごっつお神楽", "横浜家系ラーメン吉岡家": "吉岡/鳥取/ごっつお神楽", "ベビーカステラMOGMOG": "ベビーカステラ専門店MOGMOG 塚本",
    "株式会社四国屋台村": "四国屋台村", "四国屋台村2": "四国屋台村", "株式会社コンセプト": "コンセプト", "多幸福": "タコフク",
    "LVR.丸ロゴ.pdf": "ロングバケーションリゾート", "LVR": "ロングバケーションリゾート", "M's store": "M's  store",
    "OREGA26": "OREGA26  鈴木", "きりん組": "キッチンきりん組", "丼ぶり屋幸丼": "丼ぶり屋幸丼", "幸丼": "丼ぶり屋幸丼",
    "鶏笑": "からあげ専門店鶏笑東出雲店", "ばらもん": "五島牛専門店ばらもん", "ルナパンナ": "ルナパンナ　中冨",
    "松井酒造": "松井酒造福井", "Tea jack": "Tea jack②", "三雅": "三雅（みやび）", "くりと": "栗処くりと",
    "しめなわ号": "縁溜しめなわ号", "官兵衛": "博多唐揚げ官兵衛", "にぎにぎ": "おむすびにぎにぎ", "デリカリカフェ": "阿出川直樹_デリカリカフェ",
    "Webとりーみんぐ": "小島慎司_Webとりーみんぐ", "MOGMOG": "ベビーカステラ専門店MOGMOG 塚本",
    "ごっつおラーメン": "ごっつお神楽", "Teajack": "Tea jack②", "TeaJack": "Tea jack②", "ロングバケーション": "ロングバケーションリゾート", "健屋": "健屋　山西",
}
PERSONAL = ["酒井謙心", "中冨", "山西", "塚本", "鈴木", "吉岡", "岩佐", "石村", "阿出川直樹", "小島慎司", "塩田海斗",
            "ナカタケイジ", "井上先生", "成瀬"]
SENDERS_SORTED = sorted(SENDERS, key=len, reverse=True)
LETTERS = [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"] + ["A" + c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]

DATE = re.compile(r"^(\d{4})\.(\d{2})\.(\d{2}) (\S+曜日)$")
MSG = re.compile(r"^(\d{2}:\d{2}) (.*)$")
SYS = re.compile(r"(が参加しました。|がメッセージの送信を取り消しました|をグループに追加しました。|が退会しました。|グループ通話が.*しました。)$")


def parse(path):
    days, cur, msg = [], None, None
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        m = DATE.match(line)
        if m:
            cur = {"date": f"{int(m.group(2))}/{int(m.group(3))}", "key": m.group(1) + m.group(2) + m.group(3), "dow": m.group(4)[0], "msgs": []}
            days.append(cur); msg = None; continue
        m = MSG.match(line)
        if m and cur is not None:
            msg = [m.group(1), m.group(2)]; cur["msgs"].append(msg); continue
        if msg is not None:
            msg[1] += "\n" + line
    return days


def split_sender(rest):
    if SYS.search(rest.split("\n")[0]):
        return None, rest
    for s in SENDERS_SORTED:
        if rest.startswith(s + " "):
            return s, rest[len(s) + 1:]
    return "?", rest


alias = {}


def name_of(sender):
    if sender in ORG:
        return ORG[sender], "org"
    if sender not in alias:
        if sender in FIXED:
            alias[sender] = FIXED[sender]
        else:
            used = set(alias.values()) | set(FIXED.values())
            alias[sender] = next(l for l in LETTERS if l not in used)
    return "出店者" + alias[sender], "vendor"


def scrub(text):
    text = re.sub(r"https?://line\.me/ti/g2/\S+", "（オープンチャットの招待リンク・省略）", text)
    text = re.sub(r"https?://line\.me/R/\S+|https?://lin\.ee/\S+", "（LINEのリンク・省略）", text)
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "（メールアドレス・省略）", text)
    text = re.sub(r"0\d{1,4}-\d{1,4}-\d{3,4}", "（電話番号・省略）", text)
    text = text.replace("成瀬_合同会社TOSU事務局", "合同会社TOSU事務局").replace("松林安美_実行委員長その2", "松林安美氏")
    for s in sorted([x for x in SENDERS if len(x) >= 3 and x not in ORG], key=len, reverse=True):
        if s in text:
            text = text.replace(s, name_of(s)[0])
    for k in sorted(TEXT_NAMES, key=len, reverse=True):
        if k in text:
            text = text.replace(k, name_of(TEXT_NAMES[k])[0])
    for n in PERSONAL:
        text = text.replace(n, "（個人名）")
    return text


def chat():
    old = parse(CHAT_OLD)
    new = parse(CHAT_NEW)
    last_key, last_time = old[-1]["key"], old[-1]["msgs"][-1][0]
    for d in new:
        if d["key"] < last_key:
            continue
        msgs = [m for m in d["msgs"] if d["key"] > last_key or m[0] > last_time]
        if not msgs:
            continue
        if d["key"] == last_key:
            old[-1]["msgs"].extend(msgs)
        else:
            old.append({**d, "msgs": msgs})
    return old


def render_day(d, kind_of):
    rows = []
    for t, rest in d["msgs"]:
        sender, body = kind_of(rest)
        if sender is None:
            txt = scrub(body)
            rows.append(f'<li class="sys"><time>{t}</time><span>{escape(txt)}</span></li>')
            continue
        who, cls = sender
        body = scrub(body).strip()
        if body in ("画像", "動画", "[写真]", "[ファイル]", "ファイル", "[動画]", "スタンプ", "[スタンプ]"):
            body_html = f'<em>（{escape(body.strip("[]"))}）</em>'
        else:
            body_html = escape(body).replace("\n", "<br>")
        rows.append(f'<li class="{cls}"><time>{t}</time><b>{escape(who)}</b><p>{body_html}</p></li>')
    return "\n".join(rows)


def chat_html():
    days = chat()

    def kind(rest):
        s, body = split_sender(rest)
        if s is None:
            return None, body
        return name_of(s), body

    out, total = [], 0
    for d in days:
        total += len(d["msgs"])
        out.append(f'<details class="day" data-n="{len(d["msgs"])}"><summary><span>{d["date"]}（{d["dow"]}）</span><span class="n">{len(d["msgs"])}件</span></summary><ol class="chat">\n{render_day(d, kind)}\n</ol></details>')
    return "\n".join(out), total, days


def order_html():
    text = ORDER.read_text(encoding="utf-8-sig")
    text = text.replace("⁨", "").replace("⁩", "")
    rep = {"成瀬友稀": "TOSUスタッフ", "成瀬さん": "TOSUスタッフ", "めいえもぉぉぉぉん": "（AXIS関係者のあだ名）", "めいえもぉぉぉん": "（AXIS関係者のあだ名）",
           "めいえもん": "（AXIS関係者のあだ名）", "MEI": "AXIS関係者", "酒井さん": "出店者Bさん"}
    for k, v in rep.items():
        text = text.replace(k, v)
    names = {"株式会社AXIS": ("AXIS（設営会社）", "org"), "松林安美": ("松林安美氏（主催）", "org"), "小澤 瞬大": ("小澤瞬大氏（主催）", "org"),
             "さよと。": ("さよと氏（主催）", "org"), "TOSUスタッフ": ("TOSUスタッフ（主催）", "org")}
    days, cur = [], None
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(\d{4})/(\d{2})/(\d{2})\((.)\)$", line)
        if m:
            cur = {"date": f"{int(m.group(2))}/{int(m.group(3))}", "dow": m.group(4), "msgs": []}; days.append(cur); i += 1; continue
        m = re.match(r"^(\d{2}:\d{2})\t([^\t]*)\t?(.*)$", line)
        if m and cur is not None:
            t, who, body = m.groups()
            if body.startswith('"') and not (body.endswith('"') and len(body) > 1):
                buf = [body[1:]]
                i += 1
                while i < len(lines) and not lines[i].endswith('"'):
                    buf.append(lines[i]); i += 1
                if i < len(lines):
                    buf.append(lines[i][:-1])
                body = "\n".join(buf)
            elif body.startswith('"') and body.endswith('"'):
                body = body[1:-1]
            cur["msgs"].append((t, who, body))
        i += 1
    out = []
    for d in days:
        rows = []
        for t, who, body in d["msgs"]:
            body = re.sub(r"0\d{1,4}-\d{1,4}-\d{3,4}", "（電話番号・省略）", body)
            if not who:
                rows.append(f'<li class="sys"><time>{t}</time><span>{escape(body)}</span></li>'); continue
            nm, cls = names.get(who, (who, "vendor"))
            b = body.strip()
            bh = f'<em>（{escape(b.strip("[]"))}）</em>' if b in ("[写真]", "[ファイル]") else escape(b).replace("\n", "<br>")
            rows.append(f'<li class="{cls}"><time>{t}</time><b>{escape(nm)}</b><p>{bh}</p></li>')
        out.append(f'<details class="day" open><summary><span>{d["date"]}（{d["dow"]}）</span><span class="n">{len(d["msgs"])}件</span></summary><ol class="chat">\n' + "\n".join(rows) + '\n</ol></details>')
    return "\n".join(out)


# ---------- 画像の一覧 ----------
GROUPS = [
    ("line", "出店者用チャット・「発注確認」グループに投稿された画像", "evidence/line"),
    ("sns/x_ms759sk", "松林安美氏のX（削除済み）", "evidence/sns/x_ms759sk"),
    ("sns/threads_axis", "AXIS代表のThreads", "evidence/sns/threads_axis"),
    ("sns/threads_sayoto2tyan", "さよと氏のThreads", "evidence/sns/threads_sayoto2tyan"),
    ("sns/x_1123sayoto", "さよと氏のX（募集チラシ）", "evidence/sns/x_1123sayoto"),
    ("sns/deleted_20261113", "削除の記録（Wayback Machine・チケットショップ）", "evidence/sns/deleted_20261113"),
    ("official", "公式サイト・公的記録", "evidence/official"),
]


def labels():
    lab = {}
    for f in ("index.html", "deleted.html"):
        s = (SITE / f).read_text(encoding="utf-8")
        for m in re.finditer(r'<img src="([^"]+)" alt="([^"]*)"', s):
            if m.group(2):
                lab.setdefault(m.group(1), m.group(2))
    return lab


def gallery_html():
    lab = labels()
    out, n = [], 0
    for _, title, rel in GROUPS:
        d = SITE / rel
        files = sorted([p for p in d.rglob("*") if p.suffix.lower() in (".jpg", ".png")])
        if not files:
            continue
        figs = []
        for p in files:
            src = p.relative_to(SITE).as_posix()
            cap = lab.get(src) or p.stem.replace("_", " ")
            if len(cap) > 46:
                cap = cap[:45] + "…"
            figs.append(f'<figure><img src="{src}" alt="{escape(cap)}" loading="lazy"><figcaption>{escape(cap)}</figcaption></figure>')
        n += len(files)
        out.append(f'<details class="fold" open><summary><h3>{escape(title)}</h3><span class="n">{len(files)}点</span></summary><div class="evgrid">\n' + "\n".join(figs) + '\n</div></details>')
    return "\n".join(out), n


# ---------- SNS の保存テキスト ----------
TEXTS = [
    ("archive/threads_sayoto2tyan/04_lff_related_posts.txt", "sayoto_threads_lff.txt", "さよと氏のThreads（イベント関連の222件）"),
    ("archive/official_lff/threads_loca.lfoodfight_all.txt", "official_threads_all.txt", "実行委員会の公式Threads（全269件）"),
    ("archive/official_lff/x_localfoodfight_posts.txt", "official_x_posts.txt", "実行委員会の公式X（全165件）"),
    ("archive/threads_axis.official_prod/01_posts_all.md", "axis_company_threads.txt", "株式会社AXISのThreads（全31件）"),
    ("archive/wayback_recovered/tosukurayoshi_x.md", "tosu_x_wayback.txt", "合同会社TOSUのX（削除済み・Wayback Machineから）"),
]


def texts():
    OUT.mkdir(parents=True, exist_ok=True)
    items = []
    for src, name, title in TEXTS:
        t = (ROOT / src).read_text(encoding="utf-8")
        t = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "（メールアドレス・省略）", t)
        (OUT / name).write_text(t, encoding="utf-8")
        items.append((name, title, len(t)))
    # AXIS代表：他のユーザーの返信の引用（〔…〕）は省く
    parts = []
    for p in sorted((ROOT / "archive" / "threads_axis.nao.official").glob("*.md")):
        t = p.read_text(encoding="utf-8")
        t = re.sub(r"〔[^〕]*〕", "〔他のユーザーの投稿の引用・省略〕", t)
        parts.append(f"\n\n######## {p.name}\n\n" + t)
    (OUT / "axis_rep_threads.txt").write_text("AXIS代表 @axis.nao.official（Threads）の保存記録。他のユーザーの返信の引用は省いています。\n" + "".join(parts), encoding="utf-8")
    items.insert(3, ("axis_rep_threads.txt", "AXIS代表のThreads（本人の投稿と返信）", 0))
    # 松林安美氏のX（全9件）
    parts = []
    for p in sorted((ROOT / "archive" / "x_ms759sk").glob("*.md")):
        parts.append(f"\n\n######## {p.name}\n\n" + p.read_text(encoding="utf-8"))
    (OUT / "matsubayashi_x.txt").write_text("松林安美氏 @ms759sk（X、2026-11-12に削除）の保存記録\n" + "".join(parts), encoding="utf-8")
    items.insert(0, ("matsubayashi_x.txt", "松林安美氏のX（削除済み・全9件）", 0))
    return items


def main():
    chat_body, total, days = chat_html()
    order_body = order_html()
    gal, nimg = gallery_html()
    tx = texts()
    # 公開用のテキスト版も置く
    lines = []
    for d in days:
        lines.append(f"\n==== {d['date']}（{d['dow']}）")
        for t, rest in d["msgs"]:
            s, body = split_sender(rest)
            who = name_of(s)[0] if s else ""
            lines.append(f"{t} {who} {scrub(body)}".replace("  ", " "))
    (OUT / "vendor_chat_anonymized.txt").write_text("出店者用LINEグループ（10/20〜11/13 10:15）。主催側・設営会社以外は記号に置き換え。\n" + "\n".join(lines), encoding="utf-8")
    tlist = "\n".join(f'<li><a href="records/{n}">{escape(t)}</a></li>' for n, t, _ in tx)
    page = TEMPLATE.format(chat=chat_body, total=total, ndays=len(days), order=order_body, gallery=gal, nimg=nimg, texts=tlist, nalias=len(alias))
    (SITE / "records.html").write_text(page, encoding="utf-8")
    print("records.html", total, "messages,", nimg, "images, aliases", len(alias))
    unknown = [r for d in days for _, r in d["msgs"] if split_sender(r)[0] == "?"]
    print("unknown senders:", len(unknown))
    for u in unknown[:10]:
        print("  ", u[:40].replace("\n", " "))


TEMPLATE = open(Path(__file__).with_name("records_template.html"), encoding="utf-8").read()

if __name__ == "__main__":
    main()
