#!/usr/bin/env python3
"""Turn the offline preview (tools/preview.py) into ONE clickable HTML page.

Every site page becomes a section; links switch sections with #tokens, so the
whole site can be browsed inside a single file (used for the claude.ai preview).

    python3 tools/preview.py && python3 tools/artifact_preview.py OUT.html
"""
import base64
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PV = os.path.join(ROOT, "preview")

ROUTES = {  # route token -> built file
    "home": "index.html",
    "guides": "guides/index.html",
    "about": "about/index.html",
    "privacy": "privacy/index.html",
    "wtrek": "guides/w-trek-torres-del-paine/index.html",
    "hu-home": "hu/index.html",
    "hu-guides": "hu/utmutatok/index.html",
    "hu-about": "hu/rolam/index.html",
    "hu-privacy": "hu/adatvedelem/index.html",
    "hu-wtrek": "hu/utmutatok/w-trek-torres-del-paine/index.html",
}
FILE_TO_ROUTE = {v: k for k, v in ROUTES.items()}


def norm(href):
    return re.sub(r"^(\.\./)+", "", href)


def img_data(path):
    data = base64.b64encode(open(os.path.join(ROOT, path), "rb").read()).decode()
    mime = "image/svg+xml" if path.endswith(".svg") else "image/jpeg"
    return f"data:{mime};base64,{data}"


def fix_links(html, route):
    def href(m):
        h = m.group(1)
        if h.startswith("#"):
            return f'href="#p-{route}-{h[1:]}"' if route else f'href="{h}"'
        if h.startswith(("http://", "https://")):
            return m.group(0)
        target = FILE_TO_ROUTE.get(norm(h))
        return f'href="#{target}"' if target else 'href="#home"'

    html = re.sub(r'href="([^"]*)"', href, html)
    html = re.sub(r'src="((?:\.\./)*assets/img/[^"]+\.(?:svg|jpg))"', lambda m: f'src="{img_data(norm(m.group(1)))}"', html)
    if route:
        html = re.sub(r'\bid="([^"]+)"', lambda m: f'id="p-{route}-{m.group(1)}"', html)
        html = re.sub(r'aria-labelledby="([^"]+)"', lambda m: f'aria-labelledby="p-{route}-{m.group(1)}"', html)
    return html


def main(out):
    home = open(os.path.join(PV, "index.html"), encoding="utf-8").read()
    css = open(os.path.join(ROOT, "assets/css/main.css"), encoding="utf-8").read()
    # self-hosted fonts: inline the @font-face rules with the woff2 files as data URIs
    fonts_css = open(os.path.join(ROOT, "assets/css/fonts.css"), encoding="utf-8").read()
    def font_uri(m):
        data = base64.b64encode(open(os.path.join(ROOT, "assets/fonts", m.group(1)), "rb").read()).decode()
        return f"url(data:font/woff2;base64,{data})"
    fonts = "<style>\n" + re.sub(r"url\(\.\./fonts/([^)]+)\)", font_uri, fonts_css) + "\n</style>"

    sections = []
    for route, path in ROUTES.items():
        page = open(os.path.join(PV, path), encoding="utf-8").read()
        lang = re.search(r'<html lang="([^"]+)"', page).group(1)
        header = re.search(r"<header class=\"site-header\">.*?</header>", page, re.S).group(0)
        main_html = re.search(r'<main id="main">(.*)</main>', page, re.S).group(1)
        footer = re.search(r"<footer class=\"site-footer\">.*?</footer>", page, re.S).group(0)
        hidden = "" if route == "home" else " hidden"
        body = fix_links(header + '<main class="pv-main">' + main_html + "</main>" + footer, route)
        sections.append(f'<section class="pv-page" id="{route}" data-route="{route}" lang="{lang}"{hidden}>{body}</section>')

    site_js = open(os.path.join(ROOT, "assets/js/site.js"), encoding="utf-8").read()
    script = "<script>\n" + site_js + "\n</script>" + """
<script>
(function () {
  var pages = Array.prototype.slice.call(document.querySelectorAll('.pv-page'));
  function show(hash) {
    var token = (hash || '').replace('#', '') || 'home';
    var page = document.querySelector('.pv-page[data-route="' + token + '"]');
    var target = null;
    if (!page) {
      target = document.getElementById(token);
      page = target ? target.closest('.pv-page') : document.querySelector('.pv-page[data-route="home"]');
    }
    pages.forEach(function (p) { p.hidden = p !== page; });
    if (target) target.scrollIntoView(); else window.scrollTo(0, 0);
  }
  window.addEventListener('hashchange', function () { show(location.hash); });
  show(location.hash);
})();
</script>"""

    note = ('<div class="pv-note"><div class="wrap">Launch preview, English and Hungarian. '
            'Use the EN / HU switch in the header. Click around: every page of the site is here.'
            f'<span class="pv-fav">Favicon <img src="{img_data(os.path.join(ROOT, "assets/img/favicon.svg"))}" width="20" height="20" alt=""></span></div></div>')
    extra_css = """
.pv-note { background: var(--band); color: var(--on-band); font-family: var(--font-mono); font-size: 0.8rem; padding-block: 10px; }
.pv-page:not([hidden]) { display: flex; flex-direction: column; min-height: 100vh; }
.pv-main { flex: 1 0 auto; }
.pv-fav { display: inline-flex; align-items: center; gap: 6px; margin-left: 12px; white-space: nowrap; }
.pv-fav img { border-radius: 4px; box-shadow: 0 0 0 1px color-mix(in srgb, var(--on-band) 40%, transparent); }
"""
    page = f"""<title>rayappley Site Draft</title>
<meta name="claude:viewport-fit-sides" content="cover">
{fonts}
<style>
{css}
{extra_css}
</style>
{note}
{''.join(sections)}
{script}
"""
    open(out, "w", encoding="utf-8").write(page)
    print(out, len(page))


if __name__ == "__main__":
    main(sys.argv[1])
