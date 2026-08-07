#!/usr/bin/env python3
"""
Збирає ru/index.html та en/index.html з index.html.

index.html — єдине джерело правди (українська версія). Правиш його,
запускаєш `python build-i18n.py`, отримуєш дві інші мови як окремі
сторінки з власними URL, власним <title>, описом і hreflang.

Навіщо окремі URL: доки мови жили тільки в JS, Google бачив одну
українську сторінку. Російської та англійської версій для пошуку
не існувало.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "index.html"
BASE = "https://gregory-ivd.github.io/smart-attic"

# Мови, що генеруються (українська — це сам index.html)
TARGETS = {
    "ru": {
        "dir": "ru",
        "html_lang": "ru",
        "og_locale": "ru_RU",
        "description": "Smart Attic — копирайтинг, лендинги под ключ и SEO. "
                       "Григорий Йвд, 12+ лет опыта. UA / RU / EN.",
        "og_description": "Григорий Йвд, копирайтер из Ужгорода. 12+ лет опыта, "
                          "три языка, тексты и лендинги под ключ.",
        "person_desc": "Копирайтер с 12+ годами опыта: тексты, лендинги под ключ "
                       "и SEO на украинском, русском и английском.",
        "biz_desc": "Копирайтинг, лендинги под ключ и SEO в одних руках: текст, "
                    "вёрстка и публикация без посредников.",
        "locality": "Ужгород",
        "region": "Закарпатская область",
        "person_name": "Григорий Йвд",
        "job": "Копирайтер полного цикла",
        "catalog": "Услуги",
        "services": [
            ("Копирайтинг", "Лендинги, карточки товаров, рассылки, статьи.", "2000"),
            ("Лендинг под ключ", "Структура, текст, вёрстка и публикация.", "6000"),
            ("SEO-текст", "Семантика, заголовки, структура страницы.", "2000"),
        ],
        "faq": [
            ("faq1_q", "faq1_a"), ("faq2_q", "faq2_a"),
            ("faq3_q", "faq3_a"), ("faq4_q", "faq4_a"),
        ],
    },
    "en": {
        "dir": "en",
        "html_lang": "en",
        "og_locale": "en_US",
        "description": "Smart Attic — copywriting, landing pages and SEO. "
                       "Gregory Ivd, 12+ years of experience. UA / RU / EN.",
        "og_description": "Gregory Ivd, copywriter based in Uzhhorod, Ukraine. "
                          "12+ years, three languages, text and landing pages end to end.",
        "person_desc": "Copywriter with 12+ years of experience: text, landing pages "
                       "and SEO in Ukrainian, Russian and English.",
        "biz_desc": "Copywriting, landing pages and SEO in one pair of hands: "
                    "writing, build and publishing with no middlemen.",
        "locality": "Uzhhorod",
        "region": "Zakarpattia Oblast",
        "person_name": "Gregory Ivd",
        "job": "Full-cycle copywriter",
        "catalog": "Services",
        "services": [
            ("Copywriting", "Landing pages, product cards, newsletters, articles.", "2000"),
            ("Landing page, end to end", "Structure, text, build and publishing.", "6000"),
            ("SEO copy", "Semantics, headings, page structure.", "2000"),
        ],
        "faq": [
            ("faq1_q", "faq1_a"), ("faq2_q", "faq2_a"),
            ("faq3_q", "faq3_a"), ("faq4_q", "faq4_a"),
        ],
    },
}


def extract_dictionaries(html: str) -> dict:
    """Витягує об'єкт T з index.html, виконуючи його в node."""
    m = re.search(r"const T = \{.*?\n\};", html, re.S)
    if not m:
        sys.exit("Не знайдено об'єкт T у index.html")
    script = m.group(0) + "\nprocess.stdout.write(JSON.stringify(T));"
    out = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, encoding="utf-8"
    )
    if out.returncode != 0:
        sys.exit(f"node не зміг розібрати T:\n{out.stderr}")
    return json.loads(out.stdout)


def esc(s: str) -> str:
    """Екранує текст для вставки в HTML-вузол."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def esc_attr(s: str) -> str:
    return esc(s).replace('"', "&quot;")


def translate_nodes(html: str, dic: dict) -> str:
    """Підставляє тексти й плейсхолдери за атрибутами data-i18n."""
    def node_sub(m):
        key = m.group("key")
        if key not in dic:
            return m.group(0)
        return f'{m.group("open")}{esc(dic[key])}{m.group("close")}'

    html = re.sub(
        r'(?P<open><(?P<tag>\w+)[^>]*\bdata-i18n="(?P<key>[\w]+)"[^>]*>)'
        r'(?P<text>.*?)'
        r'(?P<close></(?P=tag)>)',
        node_sub, html, flags=re.S,
    )

    def ph_sub(m):
        key = m.group("key")
        if key not in dic:
            return m.group(0)
        return re.sub(
            r'placeholder="[^"]*"',
            f'placeholder="{esc_attr(dic[key])}"',
            m.group(0),
        )

    html = re.sub(
        r'<input[^>]*\bdata-i18n-ph="(?P<key>[\w]+)"[^>]*>',
        ph_sub, html,
    )
    return html


def build_jsonld(lang: str, cfg: dict, dic: dict) -> str:
    url = f"{BASE}/{cfg['dir']}/"
    services = [
        {
            "@type": "Offer",
            "itemOffered": {"@type": "Service", "name": n, "description": d},
            "priceCurrency": "UAH",
            "price": p,
        }
        for n, d, p in cfg["services"]
    ]
    faq = [
        {
            "@type": "Question",
            "name": dic[q],
            "acceptedAnswer": {"@type": "Answer", "text": dic[a]},
        }
        for q, a in cfg["faq"]
        if q in dic and a in dic
    ]
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Person",
                "@id": f"{BASE}/#person",
                "name": cfg["person_name"],
                "alternateName": "Gregory Ivd",
                "url": url,
                "image": f"{BASE}/photo.jpg",
                "jobTitle": cfg["job"],
                "description": cfg["person_desc"],
                "email": "mailto:apshanuivd@gmail.com",
                "knowsLanguage": ["uk", "ru", "en"],
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": cfg["locality"],
                    "addressRegion": cfg["region"],
                    "addressCountry": "UA",
                },
                "sameAs": ["https://t.me/Gregory_ivd", "https://github.com/Gregory-Ivd"],
                "worksFor": {"@id": f"{BASE}/#business"},
            },
            {
                "@type": "ProfessionalService",
                "@id": f"{BASE}/#business",
                "name": "Smart Attic",
                "url": url,
                "image": f"{BASE}/photo.jpg",
                "description": cfg["biz_desc"],
                "founder": {"@id": f"{BASE}/#person"},
                "priceRange": "2000–15000 UAH",
                "currenciesAccepted": "UAH",
                "areaServed": {"@type": "Country", "name": "Ukraine"},
                "availableLanguage": ["uk", "ru", "en"],
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": cfg["locality"],
                    "addressCountry": "UA",
                },
                "hasOfferCatalog": {
                    "@type": "OfferCatalog",
                    "name": cfg["catalog"],
                    "itemListElement": services,
                },
            },
            {
                "@type": "WebSite",
                "@id": f"{BASE}/#website",
                "url": url,
                "name": "Smart Attic",
                "inLanguage": cfg["html_lang"],
                "publisher": {"@id": f"{BASE}/#person"},
            },
            {
                "@type": "FAQPage",
                "@id": f"{url}#faq",
                "inLanguage": cfg["html_lang"],
                "mainEntity": faq,
            },
        ],
    }
    body = json.dumps(graph, ensure_ascii=False, indent=2)
    return (
        "<!-- JSONLD:START (згенеровано build-i18n.py — не правити тут) -->\n"
        f'<script type="application/ld+json">\n{body}\n</script>\n'
        "<!-- JSONLD:END -->"
    )


def build(lang: str, cfg: dict, src: str, dicts: dict) -> str:
    dic = dicts[lang]
    html = src
    url = f"{BASE}/{cfg['dir']}/"

    # 1. Тексти
    html = translate_nodes(html, dic)

    # 2. Мова документа
    html = html.replace('<html lang="uk">', f'<html lang="{cfg["html_lang"]}">', 1)

    # 3. <title> і мета-описи
    html = re.sub(r"<title>.*?</title>", f"<title>{esc(dic['title'])}</title>",
                  html, count=1, flags=re.S)
    for name, value in (
        ("description", cfg["description"]),
        ("twitter:description", cfg["og_description"]),
        ("twitter:title", dic["title"]),
    ):
        html = re.sub(
            rf'(<meta name="{re.escape(name)}" content=")[^"]*(">)',
            lambda m: m.group(1) + esc_attr(value) + m.group(2),
            html, count=1,
        )
    for prop, value in (
        ("og:description", cfg["og_description"]),
        ("og:title", dic["title"]),
        ("og:url", url),
        ("og:locale", cfg["og_locale"]),
    ):
        html = re.sub(
            rf'(<meta property="{re.escape(prop)}" content=")[^"]*(">)',
            lambda m: m.group(1) + esc_attr(value) + m.group(2),
            html, count=1,
        )

    # og:locale:alternate — перелічуємо дві інші мови
    others = [c["og_locale"] for l, c in TARGETS.items() if l != lang]
    others.insert(0, "uk_UA")
    alt_block = "\n".join(
        f'<meta property="og:locale:alternate" content="{o}">' for o in others
    )
    html = re.sub(
        r'(<meta property="og:locale:alternate" content="[^"]*">\s*)+',
        alt_block + "\n", html, count=1,
    )

    # 4. canonical на себе (hreflang-блок лишається спільним для всіх мов)
    html = re.sub(
        r'(<link rel="canonical" href=")[^"]*(">)',
        lambda m: m.group(1) + url + m.group(2), html, count=1,
    )

    # 5. Відносні шляхи: сторінка лежить на рівень глибше
    html = html.replace('src="photo.jpg"', 'src="../photo.jpg"')
    html = html.replace('href="privacy.html"', 'href="../privacy.html"')

    # 6. Активна кнопка мови
    html = html.replace('<button data-lang="ua" class="on">UA</button>',
                        '<button data-lang="ua">UA</button>', 1)
    html = html.replace(f'<button data-lang="{lang}">',
                        f'<button data-lang="{lang}" class="on">', 1)

    # 7. Поточна мова для перемикача
    html = html.replace('const CURRENT_LANG = "ua";',
                        f'const CURRENT_LANG = "{lang}";', 1)

    # 8. JSON-LD
    html = re.sub(
        r"<!-- JSONLD:START.*?JSONLD:END -->",
        lambda m: build_jsonld(lang, cfg, dic),
        html, count=1, flags=re.S,
    )

    return html


def main():
    src = SRC.read_text(encoding="utf-8")
    dicts = extract_dictionaries(src)

    for lang, cfg in TARGETS.items():
        if lang not in dicts:
            sys.exit(f"У словнику T немає мови {lang}")
        out_dir = ROOT / cfg["dir"]
        out_dir.mkdir(exist_ok=True)
        page = build(lang, cfg, src, dicts)
        (out_dir / "index.html").write_text(page, encoding="utf-8")
        print(f"  {cfg['dir']}/index.html — {len(page):,} байт")

    # sitemap
    pages = [f"{BASE}/"] + [f"{BASE}/{c['dir']}/" for c in TARGETS.values()]
    entries = "\n".join(
        "  <url>\n"
        f"    <loc>{p}</loc>\n"
        f"    <xhtml:link rel=\"alternate\" hreflang=\"uk\" href=\"{BASE}/\"/>\n"
        f"    <xhtml:link rel=\"alternate\" hreflang=\"ru\" href=\"{BASE}/ru/\"/>\n"
        f"    <xhtml:link rel=\"alternate\" hreflang=\"en\" href=\"{BASE}/en/\"/>\n"
        f"    <xhtml:link rel=\"alternate\" hreflang=\"x-default\" href=\"{BASE}/\"/>\n"
        "  </url>"
        for p in pages
    )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        f"{entries}\n"
        "</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print("  sitemap.xml")

    robots = (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {BASE}/sitemap.xml\n"
    )
    (ROOT / "robots.txt").write_text(robots, encoding="utf-8")
    print("  robots.txt")


if __name__ == "__main__":
    print("Збираю мовні версії з index.html:")
    main()
    print("Готово.")
