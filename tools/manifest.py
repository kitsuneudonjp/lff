"""証拠ファイルの SHA-256 台帳を作る。

使い方（LFF フォルダで）:
    python -I site/tools/manifest.py

出力:
    site/evidence/SHA256SUMS       公開している証拠ファイルのハッシュ（sha256sum 形式）
    site/evidence/manifest.json    同じ内容に、サイズと記録日時を加えたもの
    site/private-hashes.txt        非公開で保管している資料のハッシュ（中身は公開しない）

非公開資料のハッシュを公開しておくと、後で「その時点でそのファイルを持っていた」こと、
そしてファイルを加工していないことを、中身を出さずに示せる。
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # LFF/
SITE = ROOT / "site"
PUBLIC_DIR = SITE / "evidence"
PRIVATE_SOURCES = [ROOT / "1111-1739.txt", ROOT / "evidence", ROOT / "archive"]
SKIP_NAMES = {"SHA256SUMS", "manifest.json", "index.html"}

# Google Tag Manager（site/index.html と同じコンテナ）
GTM_ID = "GTM-5VJ6V8SR"
GA4_ID = "G-WRLJP6FQFK"  # GA4 はサイトに直書き（GTM 側に同じ ID を入れると二重計測になる）
GTM_HEAD = (
    "<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':"
    "new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],"
    "j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src="
    "'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);"
    f"}})(window,document,'script','dataLayer','{GTM_ID}');</script>"
    f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>'
    "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
    f"gtag('js',new Date());gtag('config','{GA4_ID}');</script>"
)
GTM_BODY = (
    f'<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}" '
    'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>'
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def walk(base: Path):
    if base.is_file():
        yield base
        return
    if not base.exists():
        return
    for p in sorted(base.rglob("*")):
        if p.is_file() and p.name not in SKIP_NAMES:
            yield p


def main() -> int:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    public = []
    for p in list(walk(PUBLIC_DIR)) + list(walk(SITE / "records")):
        rel = p.relative_to(SITE).as_posix()
        public.append({"path": rel, "sha256": sha256(p), "bytes": p.stat().st_size})
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    (PUBLIC_DIR / "SHA256SUMS").write_text(
        "".join(f"{e['sha256']}  {e['path']}\n" for e in public), encoding="utf-8")
    (PUBLIC_DIR / "manifest.json").write_text(
        json.dumps({"generated_utc": now, "files": public}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    # 公開ファイルの一覧ページ（GitHub Pages はフォルダの中身を表示しないため）
    from html import escape
    rows = "".join(
        f'<tr><td><a href="../{escape(e["path"])}">{escape(e["path"])}</a></td>'
        f'<td>{e["bytes"]:,}</td><td><code>{e["sha256"]}</code></td></tr>'
        for e in public)
    (PUBLIC_DIR / "index.html").write_text(
        '<!doctype html><html lang="ja"><head><meta charset="utf-8">'
        f'{GTM_HEAD}'
        '<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex">'
        '<title>公開証拠ファイル一覧</title><link rel="stylesheet" href="../style.css"></head><body>'
        f'{GTM_BODY}'
        '<main style="max-width:1080px;margin:0 auto;padding:24px 16px">'
        '<p><a href="../index.html">← 検証ノートに戻る</a></p><h1>公開証拠ファイル一覧</h1>'
        f'<p>生成：{now}（UTC）。各ファイルの SHA-256 は <a href="SHA256SUMS">SHA256SUMS</a> と同じです。</p>'
        '<div class="tbl"><table><tr><th>ファイル</th><th>バイト</th><th>SHA-256</th></tr>'
        f'{rows}</table></div></main></body></html>', encoding="utf-8")

    private_lines = [f"# 非公開資料のハッシュ（生成 {now} UTC）。中身は公開しない。\n"]
    count = 0
    for src in PRIVATE_SOURCES:
        for p in walk(src):
            rel = p.relative_to(ROOT).as_posix()
            private_lines.append(f"{sha256(p)}  {rel}\n")
            count += 1
    (SITE / "private-hashes.txt").write_text("".join(private_lines), encoding="utf-8")

    print(f"public: {len(public)} files, private: {count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
