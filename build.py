#!/usr/bin/env python3
"""호텔 데일리 브리프 사이트 생성기.

content/YYYY-MM-DD.json 파일을 읽어 다음을 만든다.
  index.html            최신 호 + 구독 안내 + 최근 지난 호
  archive.html          전체 지난 호 목록
  issues/YYYY-MM-DD.html 호별 페이지
  sitemap.xml, robots.txt

새 호를 올릴 때는 content/ 에 JSON 하나를 추가하고 `python3 build.py` 만 실행하면 된다.
"""
import datetime as dt
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
CONTENT = ROOT / "content"
SITE_URL = "https://hoteldailybrief.github.io"
SITE_NAME = "호텔 데일리 브리프"
TAGLINE = "국내외 호텔 브랜드, 신규 개발·개관, 관광 수요, 수수료·플랫폼 정책 소식을 매일 아침 정리합니다."

# 구글 폼 등 구독 신청 링크. 비어 있으면 '준비 중' 버튼으로 표시된다.
SUBSCRIBE_URL = ""

WEEKDAYS = "월화수목금토일"
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600;700'
         '&family=Noto+Serif+KR:wght@700;900&display=swap">')

e = html.escape


def load_issues():
    issues = []
    for p in sorted(CONTENT.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        d["_date"] = dt.date.fromisoformat(d["date"])
        issues.append(d)
    issues.sort(key=lambda d: d["_date"], reverse=True)
    return issues


def fmt_date(d):
    return f"{d.year}. {d.month:02d}. {d.day:02d} ({WEEKDAYS[d.weekday()]})"


def first_title(i):
    items = i.get("domestic", []) + i.get("overseas", [])
    return items[0]["title"] if items else ""


def page(title, desc, body, path, prefix, og_type="website"):
    canonical = f"{SITE_URL}/{path}" if path else f"{SITE_URL}/"
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
{FONTS}
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
<header class="site-head"><div class="wrap">
<a class="brand" href="{prefix}index.html"><span class="brand-en">HOTEL DAILY BRIEF</span><span class="brand-ko">{SITE_NAME}</span></a>
<nav class="nav" aria-label="주 메뉴"><a href="{prefix}archive.html">지난 호</a><a class="cta" href="{prefix}index.html#subscribe">구독하기</a></nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="site-foot"><div class="wrap">
<p>{SITE_NAME} · 매일 오전 발행</p>
<p>각 기사의 저작권은 해당 매체에 있으며, 제목을 누르면 원문으로 이동합니다.</p>
</div></footer>
</body>
</html>
"""


def render_items(items):
    out = []
    for it in items:
        out.append(f"""<article class="item">
<div class="tag">{e(it['tag'])}</div>
<h3><a href="{e(it['url'])}" target="_blank" rel="noopener">{e(it['title'])} ↗</a></h3>
<p>{e(it['summary'])}</p>
<div class="src"><a href="{e(it['url'])}" target="_blank" rel="noopener">{e(it['source'])}</a> · {e(it['time'])}</div>
</article>""")
    return "\n".join(out)


def render_issue(i, heading_tag="h1"):
    nums = "".join(
        f"<div><b>{e(n['value'])}<small>{e(n['unit'])}</small></b><span>{e(n['label'])}</span></div>"
        for n in i.get("numbers", []))
    sections = []
    for key, name in (("domestic", "국내"), ("overseas", "해외")):
        if i.get(key):
            sections.append(f'<section class="section"><h2>{name}</h2>\n{render_items(i[key])}\n</section>')
    return f"""<section class="issue">
<div class="issue-meta">
<div><div class="label">TODAY'S BRIEF</div><{heading_tag} class="issue-title">{fmt_date(i['_date'])}</{heading_tag}></div>
<div class="no">No. {i['no']:03d}</div>
</div>
<p class="lede">{e(i['summary'])}</p>
{f'<div class="numbers">{nums}</div>' if nums else ''}
{''.join(sections)}
</section>"""


def subscribe_box():
    if SUBSCRIBE_URL:
        btn = f'<a class="btn" href="{e(SUBSCRIBE_URL)}" target="_blank" rel="noopener">무료 구독 신청 ↗</a>'
    else:
        btn = '<a class="btn" aria-disabled="true">구독 신청 준비 중</a>'
    return f"""<section class="subscribe" id="subscribe">
<h2>매일 아침, 메일로 받아 보세요</h2>
<p>국내외 호텔 브랜드, 신규 개발·개관, 관광 수요, 수수료·플랫폼 정책 소식을 하루 한 번 정리해 보내 드립니다. 구독료는 없습니다.</p>
{btn}
<p class="fine">구독 신청 시 이메일 수신 및 개인정보 수집·이용에 동의하게 되며, 언제든 수신을 거부할 수 있습니다.</p>
</section>"""


def archive_list(issues, prefix):
    rows = "\n".join(
        f'<li><a href="{prefix}issues/{i["date"]}.html"><span class="d">{fmt_date(i["_date"])}</span>'
        f'<span class="t">{e(first_title(i))}</span></a></li>' for i in issues)
    return f"<ul>\n{rows}\n</ul>"


def build():
    issues = load_issues()
    if not issues:
        raise SystemExit("content/ 에 호가 없습니다.")
    (ROOT / "issues").mkdir(exist_ok=True)

    # 호별 페이지
    for idx, i in enumerate(issues):
        newer = issues[idx - 1] if idx > 0 else None
        older = issues[idx + 1] if idx + 1 < len(issues) else None
        pager = '<nav class="pager" aria-label="호 이동">'
        pager += f'<a href="{older["date"]}.html">← 이전 호 {fmt_date(older["_date"])}</a>' if older else "<span></span>"
        pager += f'<a href="{newer["date"]}.html">다음 호 {fmt_date(newer["_date"])} →</a>' if newer else "<span></span>"
        pager += "</nav>"
        body = render_issue(i) + pager + subscribe_box()
        title = f"{SITE_NAME} {i['date'].replace('-', '.')} | {first_title(i)}"
        (ROOT / "issues" / f"{i['date']}.html").write_text(
            page(title, i["summary"], body, f"issues/{i['date']}.html", "../", "article"), encoding="utf-8")

    # 메인
    latest = issues[0]
    recent = issues[1:8]
    body = f"""<section class="hero"><h1>호텔·숙박 시장의 오늘을<br>한 장으로 읽습니다</h1><p>{TAGLINE}</p></section>
{render_issue(latest, 'h2')}
{subscribe_box()}"""
    if recent:
        body += f'<section class="archive"><h2>지난 호</h2>{archive_list(recent, "")}<a class="more" href="archive.html">전체 보기 →</a></section>'
    (ROOT / "index.html").write_text(page(f"{SITE_NAME} | 매일 아침 호텔 산업 뉴스", TAGLINE, body, "", ""), encoding="utf-8")

    # 아카이브
    body = f'<section class="hero"><h1>지난 호</h1><p>지금까지 발행한 {len(issues)}개 호입니다.</p></section><section class="archive">{archive_list(issues, "")}</section>'
    (ROOT / "archive.html").write_text(page(f"지난 호 | {SITE_NAME}", TAGLINE, body, "archive.html", ""), encoding="utf-8")

    # 검색엔진용
    urls = [f"{SITE_URL}/", f"{SITE_URL}/archive.html"] + [f"{SITE_URL}/issues/{i['date']}.html" for i in issues]
    sm = "\n".join(f"<url><loc>{u}</loc></url>" for u in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sm}\n</urlset>\n',
        encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    print(f"built {len(issues)} issue(s); latest {latest['date']}")


if __name__ == "__main__":
    build()
