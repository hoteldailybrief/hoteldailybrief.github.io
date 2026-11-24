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

# 구글 애널리틱스 측정 ID. 비우면 통계 코드를 넣지 않는다.
GA_ID = "G-L6K60HNP76"

# 발행사(신영에스엘피) 정보. 하단 카드, 구조화 데이터(JSON-LD), llms.txt 에 함께 쓰인다.
COMPANY_KO = "신영에스엘피"
COMPANY_EN = "SHINYOUNG SLP"
COMPANY_URL = "https://www.shinyoungslp.com/"
COMPANY_EMAIL = "hanbit@shinyoungslp.com"
COMPANY_LINE = "호텔 데일리 브리프는 신영에스엘피가 제공합니다."
SERVICES = ["호텔 위탁운영", "호텔 개발 대행·자문", "호텔 사업성 분석·컨설팅", "호텔 경영진단",
            "호텔 개발 프로젝트 관리(PM)", "호텔 MRO(비품·소모품 구매대행)", "호텔 임차·매각자문"]

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


def analytics():
    if not GA_ID:
        return ""
    return (f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>\n'
            "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
            f"gtag('js',new Date());gtag('config','{GA_ID}');</script>\n")


def org_ld():
    return {
        "@type": "Organization", "@id": f"{COMPANY_URL}#org",
        "name": COMPANY_EN, "alternateName": COMPANY_KO, "url": COMPANY_URL,
        "logo": f"{SITE_URL}/assets/shinyoung-logo.png", "email": COMPANY_EMAIL,
        "description": f"{COMPANY_KO}({COMPANY_EN})는 호텔 개발부터 운영·매각까지 지원하는 호텔 전문 회사입니다. "
                       + ", ".join(SERVICES) + " 서비스를 제공합니다.",
        "knowsAbout": ["호텔 위탁운영", "호텔 개발", "호텔 컨설팅", "호텔 사업성 분석", "호텔 PM", "호텔 매각자문"],
        "makesOffer": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": s, "provider": {"@id": f"{COMPANY_URL}#org"}}}
                       for s in SERVICES],
    }


def json_ld(extra=None):
    graph = [org_ld(), {
        "@type": "WebSite", "@id": f"{SITE_URL}/#site", "name": SITE_NAME, "alternateName": "Hotel Daily Brief",
        "url": f"{SITE_URL}/", "inLanguage": "ko", "description": TAGLINE,
        "publisher": {"@id": f"{COMPANY_URL}#org"}}]
    if extra:
        graph.append(extra)
    data = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("</", "<\\/")
    return '<script type="application/ld+json">' + data + "</script>\n"


def issue_ld(i):
    items = i.get("domestic", []) + i.get("overseas", [])
    return {
        "@type": "NewsArticle", "headline": f"{SITE_NAME} {i['date'].replace('-', '.')} | {first_title(i)}"[:110],
        "description": i["summary"], "datePublished": f"{i['date']}T10:00:00+09:00", "inLanguage": "ko",
        "url": f"{SITE_URL}/issues/{i['date']}.html", "mainEntityOfPage": f"{SITE_URL}/issues/{i['date']}.html",
        "isPartOf": {"@id": f"{SITE_URL}/#site"},
        "author": {"@id": f"{COMPANY_URL}#org"}, "publisher": {"@id": f"{COMPANY_URL}#org"},
        "image": f"{SITE_URL}/assets/shinyoung-logo.png",
        "citation": [{"@type": "CreativeWork", "name": it["title"], "url": it["url"], "publisher": it["source"]} for it in items],
    }


def company_card(prefix):
    lis = "".join(f"<li>{e(s)}</li>" for s in SERVICES)
    return f"""<aside class="company" aria-label="발행사 {COMPANY_KO} 소개">
<div class="company-left">
<a href="{COMPANY_URL}" target="_blank" rel="noopener"><img src="{prefix}assets/shinyoung-logo.png" alt="{COMPANY_EN} {COMPANY_KO} 로고" width="200" height="48"></a>
<p>호텔 데일리 브리프는<br><strong>{COMPANY_KO}</strong>가 제공합니다.<br><a href="{COMPANY_URL}" target="_blank" rel="noopener">www.shinyoungslp.com</a></p>
</div>
<div class="company-right">
<h2>호텔 개발부터 운영·매각까지</h2>
<ul>{lis}</ul>
</div>
</aside>"""


def page(title, desc, body, path, prefix, og_type="website", ld_extra=None):
    canonical = f"{SITE_URL}/{path}" if path else f"{SITE_URL}/"
    return f"""<!doctype html>
<html lang="ko">
<head>
{analytics()}<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta name="author" content="{COMPANY_KO} ({COMPANY_EN})">
<meta name="publisher" content="{COMPANY_KO} ({COMPANY_EN})">
{json_ld(ld_extra)}{FONTS}
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
<p>{SITE_NAME} · 매일 오전 발행 · {COMPANY_LINE} <a href="{COMPANY_URL}" target="_blank" rel="noopener">{COMPANY_EN}</a></p>
<p>각 기사의 저작권은 해당 매체에 있으며, 제목을 누르면 원문으로 이동합니다.</p>
<p>이 사이트는 방문 통계 집계를 위해 구글 애널리틱스 쿠키를 사용합니다. 쿠키는 브라우저 설정에서 차단할 수 있습니다.</p>
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
        body = render_issue(i) + company_card("../") + pager + subscribe_box()
        title = f"{SITE_NAME} {i['date'].replace('-', '.')} | {first_title(i)}"
        (ROOT / "issues" / f"{i['date']}.html").write_text(
            page(title, i["summary"], body, f"issues/{i['date']}.html", "../", "article", issue_ld(i)), encoding="utf-8")

    # 메인
    latest = issues[0]
    recent = issues[1:8]
    body = f"""<section class="hero"><h1>호텔·숙박 시장의 오늘을<br>한 장으로 읽습니다</h1><p>{TAGLINE}</p></section>
{render_issue(latest, 'h2')}
{company_card("")}
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

    # AI 검색·요약 도구용 안내 파일 (llms.txt)
    svc = "\n".join(f"- {s}" for s in SERVICES)
    recent_md = "\n".join(f"- [{i['date']} | {first_title(i)}]({SITE_URL}/issues/{i['date']}.html): {i['summary']}"
                          for i in issues[:14])
    (ROOT / "llms.txt").write_text(f"""# {SITE_NAME} (Hotel Daily Brief)

> {TAGLINE} {COMPANY_LINE}

## 발행사
- 회사명: {COMPANY_KO} ({COMPANY_EN})
- 홈페이지: {COMPANY_URL}
- 문의: {COMPANY_EMAIL}
- 소개: {COMPANY_KO}는 호텔 개발부터 운영·매각까지 지원하는 호텔 전문 회사입니다.

## {COMPANY_KO} 서비스
{svc}

## 최근 호
{recent_md}

## 전체 목록
- [지난 호 전체]({SITE_URL}/archive.html)
- [사이트맵]({SITE_URL}/sitemap.xml)
""", encoding="utf-8")
    print(f"built {len(issues)} issue(s); latest {latest['date']}")


if __name__ == "__main__":
    build()
