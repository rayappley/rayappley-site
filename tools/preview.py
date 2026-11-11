#!/usr/bin/env python3
"""Tiny offline preview of the Jekyll site (no Ruby needed).

GitHub Pages builds the real site with Jekyll. This script only imitates the
small part of Jekyll/Liquid the templates use, so the design can be checked
locally. Output: preview/<page>/index.html with relative links and the CSS
inlined, so the folder can be opened straight from disk.

    python3 tools/preview.py
"""
import html
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "preview")


# ---------------------------------------------------------------- YAML-ish
def parse_yaml(text):
    data = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or line.startswith(" "):
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        val = re.sub(r"\s+#.*$", "", val) if not val.startswith(('"', "'")) else val
        if val.startswith('"') and val.endswith('"') or val.startswith("'") and val.endswith("'"):
            val = val[1:-1]
        elif val in ("true", "false"):
            val = val == "true"
        elif re.fullmatch(r"-?\d+", val):
            val = int(val)
        data[key] = val
    return data


def split_front_matter(text):
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        return parse_yaml(fm), body.lstrip("\n")
    return None, text


# ---------------------------------------------------------------- Markdown subset
def slug(s):
    s = re.sub(r"<[^>]+>", "", s).lower()
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"\s+", "-", s.strip())


def inline(s):
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])_([^_]+)_(?!\w)", r"<em>\1</em>", s)
    s = re.sub(r"(?<![\w*])\*([^*]+)\*(?!\w)", r"<em>\1</em>", s)
    return s


def markdown(text):
    lines = text.split("\n")
    out, i, headings, toc_at = [], 0, [], None
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.strip() == "* TOC" and i + 1 < len(lines) and lines[i + 1].strip() == "{:toc}":
            toc_at = len(out)
            out.append("")
            i += 2
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            lvl, txt = len(m.group(1)), inline(m.group(2))
            hid = slug(m.group(2))
            headings.append((lvl, hid, txt))
            out.append(f'<h{lvl} id="{hid}">{txt}</h{lvl}>')
            i += 1
            continue
        if ln.lstrip().startswith("<"):
            block = []
            while i < len(lines) and lines[i].strip():
                block.append(lines[i])
                i += 1
            out.append("\n".join(block))
            continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], [r for r in rows[2:]]
            t = ["<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"]
            for r in body:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t))
            continue
        if ln.startswith(">"):
            block = []
            while i < len(lines) and lines[i].startswith(">"):
                block.append(lines[i][1:].strip())
                i += 1
            out.append(f"<blockquote><p>{inline(' '.join(block))}</p></blockquote>")
            continue
        if re.match(r"^\s*([-*]|\d+\.)\s+", ln):
            ordered = bool(re.match(r"^\s*\d+\.", ln))
            items = []
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                items.append(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i]))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||>|\s*[-*]\s|<)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    if toc_at is not None:
        items = "".join(f'<li><a href="#{h}">{t}</a></li>' for lvl, h, t in headings if lvl == 2)
        out[toc_at] = f'<ul id="markdown-toc">{items}</ul>'
    return "\n".join(out)


# ---------------------------------------------------------------- Liquid subset
class Ctx(dict):
    def lookup(self, expr):
        expr = expr.strip()
        if expr.startswith(("'", '"')):
            return expr[1:-1]
        if re.fullmatch(r"-?\d+", expr):
            return int(expr)
        if expr in ("true", "false"):
            return expr == "true"
        cur = self
        for dotted, bracket in re.findall(r"([^.\[\]]+)|\[([^\]]+)\]", expr):
            part = self.lookup(bracket) if bracket else dotted
            if part == "size" and isinstance(cur, (list, str)):
                cur = len(cur)
            elif isinstance(cur, dict):
                cur = cur.get(part)
            else:
                return None
        return cur


def relative(path, depth):
    if not isinstance(path, str) or path.startswith(("http://", "https://", "#", "mailto:")):
        return path
    rel = "../" * depth + path.lstrip("/")
    if rel.endswith("/") or rel == "":
        rel += "index.html"
    return rel or "index.html"


def apply_filters(val, filters, ctx):
    for f in filters:
        name, _, arg = f.partition(":")
        name, arg = name.strip(), arg.strip()
        if name in ("relative_url", "absolute_url"):
            val = relative(val, ctx["__depth"])
        elif name == "default":
            if val in (None, "", False):
                val = ctx.lookup(arg)
        elif name == "escape":
            val = html.escape(str(val or ""))
        elif name == "sort":
            key = ctx.lookup(arg)
            val = sorted(val or [], key=lambda d: d.get(key, 0))
        elif name == "group_by":
            key = ctx.lookup(arg)
            groups = []
            for item in val or []:
                g = next((x for x in groups if x["name"] == item.get(key)), None)
                if g is None:
                    g = {"name": item.get(key), "items": []}
                    groups.append(g)
                g["items"].append(item)
            for g in groups:
                g["size"] = len(g["items"])
            val = groups
        elif name == "where":
            key, want = [ctx.lookup(a) for a in arg.split(",", 1)]
            val = [d for d in val or [] if d.get(key) == want]
        elif name == "map":
            key = ctx.lookup(arg)
            val = [d.get(key) for d in val or []]
        elif name == "uniq":
            seen = []
            for x in val or []:
                if x not in seen:
                    seen.append(x)
            val = seen
        elif name == "join":
            val = ctx.lookup(arg).join(str(x) for x in val or [])
        elif name == "date":
            fmt = ctx.lookup(arg)
            val = val.strftime(fmt) if hasattr(val, "strftime") else val
        elif name == "slugify":
            val = re.sub(r"[^a-z0-9]+", "-", str(val).lower()).strip("-")
    return val


def evaluate(expr, ctx):
    parts = [p for p in re.split(r"\|(?=(?:[^\"']|[\"'][^\"']*[\"'])*$)", expr)]
    val = ctx.lookup(parts[0])
    return apply_filters(val, parts[1:], ctx)


def condition(expr, ctx):
    expr = expr.strip()
    for op in ("==", "!=", " contains ", ">=", "<=", " > ", " < "):
        if op in expr:
            a, b = expr.split(op, 1)
            av, bv = ctx.lookup(a), ctx.lookup(b)
            if op == "==":
                return av == bv
            if op == "!=":
                return av != bv
            if op == " contains ":
                return bv in (av or "")
            av, bv = av or 0, bv or 0
            return {">=": av >= bv, "<=": av <= bv, " > ": av > bv, " < ": av < bv}[op]
    return bool(ctx.lookup(expr))


TOKEN = re.compile(r"({%-?.*?-?%}|{{.*?}})", re.S)


def parse(tokens, pos, stop=()):
    nodes = []
    while pos < len(tokens):
        t = tokens[pos]
        if t.startswith("{%"):
            tag = t.strip("{%- }").strip()
            name = tag.split()[0] if tag else ""
            if name in stop:
                return nodes, pos
            if name in ("if", "unless"):
                branches, cur_cond = [], tag[len(name):].strip()
                neg = name == "unless"
                pos += 1
                while True:
                    body, pos = parse(tokens, pos, ("elsif", "else", "endif", "endunless"))
                    branches.append((cur_cond, neg, body))
                    end = tokens[pos].strip("{%- }").strip()
                    pos += 1
                    if end.startswith("elsif"):
                        cur_cond, neg = end[5:].strip(), False
                    elif end == "else":
                        cur_cond, neg = None, False
                    else:
                        break
                nodes.append(("if", branches))
                continue
            if name == "for":
                m = re.match(r"for\s+(\w+)\s+in\s+(.+)", tag)
                body, pos = parse(tokens, pos + 1, ("endfor",))
                nodes.append(("for", m.group(1), m.group(2), body))
                pos += 1
                continue
            nodes.append(("tag", tag))
        else:
            nodes.append(("text", t))
        pos += 1
    return nodes, pos


def render_nodes(nodes, ctx):
    out = []
    for n in nodes:
        kind = n[0]
        if kind == "text":
            t = n[1]
            if t.startswith("{{"):
                v = evaluate(t[2:-2], ctx)
                out.append("" if v is None or v is False else str(v))
            else:
                out.append(t)
        elif kind == "if":
            for cond, neg, body in n[1]:
                ok = True if cond is None else condition(cond, ctx)
                if neg:
                    ok = not ok
                if ok:
                    out.append(render_nodes(body, ctx))
                    break
        elif kind == "for":
            for item in evaluate(n[2], ctx) or []:
                ctx[n[1]] = item
                out.append(render_nodes(n[3], ctx))
        elif kind == "tag":
            tag = n[1]
            name = tag.split()[0]
            if name == "assign":
                m = re.match(r"assign\s+(\w+)\s*=\s*(.+)", tag)
                ctx[m.group(1)] = evaluate(m.group(2), ctx)
            elif name == "include":
                parts = tag.split(None, 2)
                fname = parts[1]
                params = dict(re.findall(r'(\w+)="([^"]*)"', parts[2] if len(parts) > 2 else ""))
                prev = ctx.get("include")
                ctx["include"] = params
                src = open(os.path.join(ROOT, "_includes", fname), encoding="utf-8").read()
                out.append(liquid(src, ctx))
                ctx["include"] = prev
            elif name == "seo":
                page, site = ctx["page"], ctx["site"]
                title = page.get("title")
                full = f"{title} | {site['title']}" if title else site["title"]
                desc = page.get("description") or page.get("summary") or site.get("description")
                out.append(f"<title>{html.escape(full)}</title>\n<meta name=\"description\" content=\"{html.escape(desc)}\">")
    return "".join(out)


def liquid(src, ctx):
    tokens = [t for t in TOKEN.split(src) if t != ""]
    nodes, _ = parse(tokens, 0)
    return render_nodes(nodes, ctx)


# ---------------------------------------------------------------- build
def main():
    site = parse_yaml(open(os.path.join(ROOT, "_config.yml"), encoding="utf-8").read())
    import datetime
    site["time"] = datetime.datetime.now()
    import yaml
    site["data"] = {}
    ddir = os.path.join(ROOT, "_data")
    if os.path.isdir(ddir):
        for fn in os.listdir(ddir):
            if fn.endswith((".yml", ".yaml")):
                site["data"][fn.rsplit(".", 1)[0]] = yaml.safe_load(open(os.path.join(ddir, fn), encoding="utf-8"))
    css = open(os.path.join(ROOT, "assets/css/main.css"), encoding="utf-8").read()

    guides = []
    gdir = os.path.join(ROOT, "_guides")
    for fn in sorted(os.listdir(gdir)):
        fm, body = split_front_matter(open(os.path.join(gdir, fn), encoding="utf-8").read())
        if fm.get("published") is False:
            continue
        fm.setdefault("lang", "en")
        fm.update(url=fm.get("permalink") or f"/guides/{fn[:-3]}/", __body=body, __md=True, layout=fm.get("layout", "guide"))
        guides.append(fm)
    site["guides"] = guides

    pages = []
    for rel in ("index.html", "guides/index.html", "maps/index.md", "about/index.md", "privacy/index.md", "404.html",
                "hu/index.html", "hu/utmutatok/index.html", "hu/rolam/index.md", "hu/adatvedelem/index.md"):
        fm, body = split_front_matter(open(os.path.join(ROOT, rel), encoding="utf-8").read())
        if fm.get("published") is False:
            continue
        fm.setdefault("lang", "en")
        url = "/" + rel.replace("index.html", "").replace("index.md", "")
        if rel == "404.html":
            url = "/404.html"
        fm.update(url=url, __body=body, __md=rel.endswith(".md"), layout=fm.get("layout", "page"))
        pages.append(fm)

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))

    for page in pages + guides:
        url = page["url"]
        out_path = url.lstrip("/") + ("index.html" if url.endswith("/") else "")
        depth = out_path.count("/")
        ctx = Ctx(site=site, page=page, __depth=depth)
        content = liquid(page["__body"], ctx)
        if page["__md"]:
            content = markdown(content)
        layout = page.get("layout")
        while layout and layout != "null":
            fm, lsrc = split_front_matter(open(os.path.join(ROOT, "_layouts", layout + ".html"), encoding="utf-8").read())
            ctx["content"] = content
            content = liquid(lsrc, ctx)
            layout = (fm or {}).get("layout")
        css_rel = relative("/assets/css/main.css", depth)
        content = content.replace(f'<link rel="stylesheet" href="{css_rel}">', "<style>\n" + css + "\n</style>")
        dest = os.path.join(OUT, out_path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "w", encoding="utf-8").write(content)
        print("built", out_path)


if __name__ == "__main__":
    sys.exit(main())
