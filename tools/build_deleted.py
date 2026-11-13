"""削除された投稿の記録ページ（site/deleted.html）を作る。

使い方（LFF フォルダで）:
    python site/tools/make_public.py      # 先に公開用の画像を作る
    python site/tools/build_deleted.py
    python -I site/tools/manifest.py      # 最後にハッシュ台帳を作り直す

本文は archive/x_ms759sk/*.md の「本文（DOMから取得、原文ママ）」をそのまま載せる。
画像は site/evidence/sns/x_ms759sk/ にあるもの（make_public.py が作る）を、ファイル名の順に並べる。
"""
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
SRC = ROOT / "archive" / "x_ms759sk"
IMG = SITE / "evidence" / "sns" / "x_ms759sk"
IMG_URL = "evidence/sns/x_ms759sk"

# 投稿ごとの見出し（内容の要約。本文の言葉を使う）と、検証ノートの関連箇所
POSTS = [
    ("2120317312121368663", "固定ポスト：謝罪と経緯の長文", "来場者数、設営業者が25人の予定から4人に、冷凍冷蔵車の二重払い、フォークリフトのキャンセル料、入金の予定など。保存時点で731.1万表示", "#claims"),
    ("2120324127827628161", "地元業者の見積もりとAXISを選んだ経緯（連投1）", "地元業者の見積もりは1000万円超で前金即金。さよと氏からAXISの提案。登記簿で「株式会社紀の国ラボ」と分かった", "#money"),
    ("2120329698169569573", "証憑が出てこなかった、前入金が跳ね上がった（連投2）", "西宮での面談、発注書が出てこない、前入金が直前に数百万円単位で増えた、振込先が分からなかった", "#money"),
    ("2120332762347639105", "「唯一送られてきたハイエース」（連投3）", "ステージ機材を持ってこなかった、音響を雨でキャンセルされた。返信の形で投稿されたため「ポスト」欄には出ていなかった", "#after"),
    ("2120345970294808701", "市・県は関係ない", "「行政は何も悪くないです」「私が悪いです」", "#claims"),
    ("2120353181502964008", "事務局の範囲を超えて立て替えている", "フォークリフトを当日キャンセルされた", "#after"),
    ("2120358112859488346", "旅館の支払いと、設営業者21人分のキャンセル料", "", "#after"),
    ("2120361942846202140", "実行委員長になった経緯", "小澤瞬大氏に勧められて地元から実行委員長に立った", "#people"),
    ("2120364504076952008", "更新停止の告知", "病院の指示で更新を止める、取材はさよと氏へ", ""),
]


def meta(md: str, key: str) -> str:
    m = re.search(rf"^- {re.escape(key)}: (.+)$", md, re.M)
    return m.group(1).strip() if m else ""


def body(md: str) -> str:
    part = md.split("## 本文", 1)[1].split("\n", 1)[1]
    return part.strip()


def paragraphs(text: str) -> str:
    out = []
    for block in re.split(r"\n\s*\n", text):
        lines = [escape(l) for l in block.strip().split("\n")]
        out.append("<p>" + "<br>".join(lines) + "</p>")
    return "\n".join(out)


def figs(prefix: str, label: str) -> str:
    files = sorted(p.name for p in IMG.glob(f"{prefix}*.jpg"))
    if not files:
        return ""
    n = len(files)
    items = []
    for i, name in enumerate(files, 1):
        cap = f"{label}（{i}/{n}）" if n > 1 else label
        items.append(
            f'<figure><img src="{IMG_URL}/{name}" alt="{escape(cap)}のスクリーンショット" loading="lazy">'
            f'<figcaption>{escape(cap)}<br><code>{name}</code></figcaption></figure>')
    return '<div class="shots">' + "".join(items) + "</div>"


def post_html(no: int, sid: str, title: str, summary: str, rel: str) -> str:
    md_path = next(SRC.glob(f"{no:02d}_{sid}.md"))
    md = md_path.read_text(encoding="utf-8")
    when = meta(md, "投稿日時")
    jst = re.search(r"JST (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})", when)
    when_txt = f"{jst.group(1).replace('-', '/')} {jst.group(2)}" if jst else when
    stats = meta(md, "反応数（取得時）")
    attach = meta(md, "添付画像")
    url = f"https://x.com/ms759sk/status/{sid}"
    rel_html = f' ／ 検証ノートの関連箇所：<a href="index.html{rel}">こちら</a>' if rel else ""
    attach_html = f"<li>添付画像：{escape(attach)}</li>" if attach and attach != "なし" else ""
    return f'''
<article class="post" id="p{no}">
  <header>
    <span class="no">{no:02d}</span>
    <div>
      <h3>{escape(title)}</h3>
      <p class="when">{escape(when_txt)} JST 投稿{(" ・ " + escape(summary)) if summary else ""}</p>
    </div>
  </header>
  <ul class="meta">
    <li>元のURL（現在は表示されない）：<code>{escape(url)}</code></li>
    <li>保存時点の反応：{escape(stats)}</li>
    {attach_html}
  </ul>
  <div class="text">
    <p class="label">本文（ページから文字のまま取得。原文のまま）</p>
    {paragraphs(body(md))}
  </div>
  {figs(f"{no:02d}_{sid}", f"{no:02d} {when_txt} の投稿")}
  <p class="src">保存したファイル：<code>archive/x_ms759sk/{md_path.name}</code> ほか（ハッシュは <a href="private-hashes.txt">非公開資料のSHA-256一覧</a>）{rel_html}</p>
</article>'''


def main() -> None:
    profile = (SRC / "00_profile.md").read_text(encoding="utf-8")
    bio = profile.split("## プロフィール文（原文ママ）", 1)[1].strip()
    posts = "\n".join(post_html(i, *p) for i, p in enumerate(POSTS, 1))
    deleted = sorted(p.name for p in (IMG / "deleted").glob("*.jpg"))
    deleted_figs = "".join(
        f'<figure><img src="{IMG_URL}/deleted/{n}" alt="削除を確認した画面" loading="lazy">'
        f'<figcaption>{"プロフィール" if "profile" in n else "投稿 " + n.split("_")[2].removesuffix(".jpg")}'
        f'（11/12 21:08 JST）</figcaption></figure>' for n in deleted)
    toc = "".join(f'<li><a href="#p{i}">{i:02d} {escape(t)}</a></li>' for i, (_, t, _, _) in enumerate(POSTS, 1))

    html = f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','GTM-5VJ6V8SR');</script>
<!-- End Google Tag Manager -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-WRLJP6FQFK"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-WRLJP6FQFK');
</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>削除された投稿の記録 LFF鳥取 検証ノート</title>
<meta name="description" content="ローカルフードファイト in 鳥取の主催側が削除した投稿と記録（松林安美氏のX、合同会社TOSUのX、公式Xの投稿、チケットショップの商品）を、削除前の保存とインターネットアーカイブの記録から公開する。">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css?v=10">
<style>
.page{{max-width:880px;margin:0 auto;padding:40px 16px 96px}}
.page main{{padding-bottom:0}}
.back{{font-size:14px}}
.page h1{{margin-top:14px}}
.facts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:24px 0}}
.facts div{{background:var(--surface);border-radius:var(--r);box-shadow:var(--shadow);padding:14px 16px}}
.facts b{{display:block;font-size:22px;font-weight:900;line-height:1.3}}
.facts span{{font-size:13px;color:var(--muted)}}
.how{{background:var(--surface);border-radius:var(--r);box-shadow:var(--shadow);padding:6px 20px;margin:20px 0}}
.how li{{margin:6px 0}}
.list{{columns:2 260px;font-size:14.5px;padding-left:1.4em}}
.post{{background:var(--surface);border-radius:var(--r);box-shadow:var(--shadow);padding:22px 22px 14px;margin:28px 0;scroll-margin-top:16px}}
.post > header{{display:flex;gap:14px;align-items:flex-start}}
.post .no{{flex:none;font-size:13px;font-weight:900;color:#fff;background:var(--accent);border-radius:8px;padding:2px 8px;margin-top:4px}}
.post h3{{margin:0;font-size:19px}}
.post .when{{margin:4px 0 0;font-size:13.5px;color:var(--muted)}}
.post .meta{{font-size:13px;color:var(--muted);padding-left:1.2em;margin:12px 0}}
.post .text{{border-left:3px solid var(--line);padding:2px 0 2px 16px;margin:14px 0}}
.post .text p{{margin:10px 0}}
.post .label{{font-size:12px;font-weight:700;letter-spacing:.06em;color:var(--muted)}}
.shots{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin:16px 0}}
.shots figure,.gone figure{{margin:0;background:#f1f0eb;box-shadow:none;cursor:zoom-in}}
.records{{list-style:none;padding:0;margin:22px 0;display:grid;gap:8px;counter-reset:r}}
.records li{{counter-increment:r}}
.records a{{display:block;background:var(--surface);border-radius:12px;box-shadow:var(--shadow);padding:10px 14px;position:relative;color:var(--ink);text-decoration:none;font-size:14px}}
.records b{{display:block;font-size:15.5px}}
.part{{margin-top:40px;padding-top:24px;border-top:2px solid var(--ink)}}
.gone{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin:16px 0}}
@media (max-width:600px){{.post{{padding:18px 14px 10px}}.shots{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body>
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-5VJ6V8SR"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
<div class="page">
<p class="back"><a href="index.html">← 検証ノートに戻る</a></p>
<span class="status">重要資料の開示</span>
<h1>削除された投稿の記録 <span>主催側が消したもの</span></h1>
<p class="sub">イベントのあと、主催側のSNSの投稿やアカウント、チケットショップの商品が次々に消えています。削除の前に保存していたものと、インターネットアーカイブ（Wayback Machine）に残っていた記録から、消されたものを公開します。</p>
<ol class="records">
  <li><a href="#posts"><b>松林安美氏のX（@ms759sk）</b>11/12 にアカウントごと削除。全9件</a></li>
  <li><a href="#tosu-x"><b>合同会社TOSUのX（@TOSUkurayoshi）</b>アカウントごと削除。「全国から5社テレビ局」「すでに50店舗」</a></li>
  <li><a href="#lff-x"><b>公式X（@localfoodfight）の投稿 7件</b>「かつて9.4万人超を動員した熱狂が再び！」</a></li>
  <li><a href="#base"><b>公式チケットショップの商品</b>すべて削除</a></li>
  <li><a href="#line"><b>出店者用LINEの送信取り消し</b>主催側・設営会社の10件</a></li>
  <li><a href="#checked"><b>消えていなかったもの</b>保存済みの投稿 1,440件を確認</a></li>
</ol>
<h2 class="part">松林安美氏のX（@ms759sk）</h2>
<p>合同会社TOSUの代表で実行委員の松林安美氏は、2026年11月11日にXで謝罪と経緯の説明を投稿しました。そのアカウントは翌12日に削除され、投稿はすべて見られなくなりました。削除の前日に保存していた全投稿を公開します。</p>

<div class="facts">
  <div><b>9件</b><span>本人の投稿すべて（11/11 9:46〜12:54）</span></div>
  <div><b>731.1万</b><span>固定ポストの表示数（保存時点）</span></div>
  <div><b>11/11 18時ごろ</b><span>保存した時刻（JST）</span></div>
  <div><b>11/12 21:08</b><span>削除を確認した時刻（JST）</span></div>
</div>

<main>
<section id="why">
<h2>なぜ公開するのか</h2>
<p>松林安美氏のXの投稿には、実行委員会の内部の経緯（見積もり、前入金、設営業者とのやり取り、立て替え）が、当事者本人の言葉で書かれていました。出店者や関係者が支払いや補償を求めるとき、また報道や行政が事実を確かめるとき、<strong>本人が何を説明していたか</strong>は欠かせない資料です。削除で消えてしまわないよう、全文を残します。</p>
<p>内容が事実かどうかは、このページでは判断していません。ほかの記録と照らし合わせた結果は、<a href="index.html#claims">検証ノートの「発言の検証」</a>にあります。</p>
<div class="warn"><strong>お願い</strong>：この記録は、事実を確かめるための資料です。松林安美氏本人やご家族への誹謗中傷、自宅や家族への接触は、絶対にしないでください。</div>
</section>

<section id="method">
<h2>保存の方法と、加えた加工</h2>
<ul class="how">
  <li><b>保存日時</b>：2026年11月11日 17:58〜18:30ごろ（JST、ファイルの更新日時）。ブラウザで閲覧しただけで、いいね・返信などの操作はしていません。</li>
  <li><b>本文</b>：ページから文字をそのまま取り出したもので、改行も含めて原文のままです。</li>
  <li><b>投稿は9件ですべて</b>：プロフィールの「29件のポスト」は、本人の投稿9件と、2026年1〜4月のリポスト20件（イベントと無関係）でした。11/10以前に本人が書いた投稿はありませんでした。04は本人の連投への返信の形で、「ポスト」欄には出ていなかったものです。</li>
  <li><b>返信欄</b>：どの投稿も「一部のアカウントのみが返信できます」の設定で、ほかの人の返信は表示されていませんでした。</li>
  <li><b>加えた加工は2つだけ</b>：(1) 画面の左右の列（<strong>保存した人のアカウント表示</strong>と、おすすめ欄）を切り落とし、投稿が写る中央の列だけにしました。(2) プロフィール画面の「〇〇さんにフォローされています」の1行を黒塗りにしました（保存した人のつながりが分かるため）。<strong>投稿の文章や画像には、手を加えていません。</strong></li>
  <li><b>改ざんの検出</b>：公開画像のSHA-256は <a href="evidence/SHA256SUMS">SHA256SUMS</a>、加工前の元画像と本文テキストのSHA-256は <a href="private-hashes.txt">非公開資料の一覧</a>（<code>archive/x_ms759sk/</code>）にあります。</li>
</ul>
</section>

<section id="deleted">
<h2>削除の確認</h2>
<p>2026年11月12日 21:08（JST）に確認したところ、プロフィールは「このアカウントは存在しません」、9件の投稿はすべて「削除されたアカウントによるポストです」と表示されました。同じ日の 9:33 までは表示できていたので、その間に削除されたことになります。凍結ではなく「削除」の表示で、30日以内なら本人が復活させられる状態の可能性があります。</p>
<div class="gone">{deleted_figs}</div>
</section>

<section id="profile">
<h2>プロフィール（削除前）</h2>
<p>表示名「松林安美」（認証バッジあり）、2026年1月から利用、フォロー12・フォロワー3,013（11/11 18時ごろ）。</p>
<div class="text post" style="margin:12px 0;padding:14px 18px"><p class="label">プロフィール文（原文のまま）</p>{paragraphs(bio)}</div>
{figs("00_", "プロフィールと返信タブ")}
</section>

<section id="posts">
<h2>投稿 9件（投稿順）</h2>
<ul class="list" style="list-style:none;padding-left:0">{toc}</ul>
{posts}
</section>
{{EXTRA}}
</main>

<footer>
  事実の誤り、反論、資料の提供を受け付けています（<a href="index.html#contribute">資料提供のお願い</a>）。<br>
  最終更新：2026年11月13日（主催側の削除の調査を追加）
</footer>
</div>
<script src="app.js?v=5" defer></script>
</body>
</html>
'''
    html = html.replace("{EXTRA}", (SITE / "tools" / "deleted_extra.html").read_text(encoding="utf-8"))
    (SITE / "deleted.html").write_text(html, encoding="utf-8")
    print("deleted.html written")


if __name__ == "__main__":
    main()
