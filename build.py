"""Build the static site into _site/.

Usage:
    python build.py            # build once
    python build.py --serve    # build, then serve on http://localhost:8000

Everything the visitor reads comes from src/i18n/<lang>.json, so a new language is one more JSON file.
The first language in site.json "languages" is published at the site root, the others under /<code>/.

Template syntax (used in src/pages and src/partials):
    {{> header }}                     include src/partials/header.html
    {{ key.path }}                    text from the language file, HTML-escaped
    {{{ key.path }}}                  same, but raw HTML (use for strings that contain links or <strong>)
    {{#each list}} ... {{/each}}      repeat for each item; inside use {{ .field }}, {{{ .field }}}, {{ @n }} (1, 2, 3...)
    {{#if key}} ... {{/if}}           keep the block only when the value is not empty
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
OUT = ROOT / "_site"

PARTIAL = re.compile(r"\{\{>\s*([\w-]+)\s*\}\}")
EACH = re.compile(r"\{\{#each\s+([\w.]+)\s*\}\}(.*?)\{\{/each\}\}", re.S)
IF = re.compile(r"\{\{#if\s+([\w.]+)\s*\}\}(.*?)\{\{/if\}\}", re.S)
RAW = re.compile(r"\{\{\{\s*([\w.@]+)\s*\}\}\}")
VAR = re.compile(r"\{\{\s*([\w.@]+)\s*\}\}")


def lookup(ctx, path, where):
    value = ctx
    for part in path.split("."):
        if isinstance(value, list) and part.isdigit():
            value = value[int(part)]
        elif isinstance(value, dict) and part in value:
            value = value[part]
        else:
            raise KeyError(f"{where}: unknown key '{path}'")
    return value


def render(text, ctx, where):
    for _ in range(5):  # partials may include partials
        text = PARTIAL.sub(lambda m: (SRC / "partials" / f"{m.group(1)}.html").read_text("utf-8"), text)

    def each(m):
        items = lookup(ctx, m.group(1), where)
        out = []
        for i, item in enumerate(items, 1):
            block = m.group(2).replace("{{ @n }}", str(i))
            block = re.sub(r"\{\{\{\s*\.([\w]+)\s*\}\}\}", lambda f: str(item[f.group(1)]), block)
            block = re.sub(r"\{\{\s*\.([\w]+)\s*\}\}", lambda f: html.escape(str(item[f.group(1)])), block)
            out.append(block)
        return "".join(out)

    text = EACH.sub(each, text)
    text = IF.sub(lambda m: m.group(2) if lookup(ctx, m.group(1), where) else "", text)
    text = RAW.sub(lambda m: str(lookup(ctx, m.group(1), where)), text)
    text = VAR.sub(lambda m: html.escape(str(lookup(ctx, m.group(1), where))), text)
    return text


CHAPTER = re.compile(r"^(\d+)\.\s*nodaļa\.?\s*(.*)$")
CLAUSE = re.compile(r"^(\d+(?:\.\d+)+)\s*\.?\s+(.*)$")


def statutes(lang, default):
    """Turn the plain-text statutes into HTML. Lines starting with '1.nodaļa.' start a chapter, '4.1.' a clause."""
    path = SRC / "content" / f"statuti.{lang}.txt"
    if not path.exists():
        path = SRC / "content" / f"statuti.{default}.txt"
    chapters, toc = [], []
    for line in path.read_text("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        if m := CHAPTER.match(line):
            num, title = m.group(1), m.group(2).rstrip(".")
            chapters.append([f'<section class="chapter" id="nodala-{num}">'
                             f'<h2><span class="ch-num">{num}. nodaļa</span>{html.escape(title)}</h2><ol class="clauses">'])
            toc.append(f'<li><a href="#nodala-{num}"><span>{num}.</span> {html.escape(title)}</a></li>')
        elif m := CLAUSE.match(line):
            num = m.group(1)
            depth = num.count(".")
            chapters[-1].append(f'<li class="d{depth}" id="p{num.replace(".", "-")}"><span class="cl-num">{num}.</span>'
                                f'<p>{html.escape(m.group(2))}</p></li>')
        else:
            raise ValueError(f"{path.name}: cannot read line: {line!r}")
    body = "".join("".join(c) + "</ol></section>" for c in chapters)
    return body, "".join(toc)


def build():
    site = json.loads((SRC / "site.json").read_text("utf-8"))
    langs = site["languages"]
    default = langs[0]
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(SRC / "assets", OUT / "assets")
    for extra in ("CNAME", "favicon.svg"):
        if (SRC / extra).exists():
            shutil.copy(SRC / extra, OUT / extra)

    for lang in langs:
        t = json.loads((SRC / "i18n" / f"{lang}.json").read_text("utf-8"))
        prefix = "" if lang == default else f"{lang}/"
        root = "" if lang == default else "../"
        (OUT / prefix).mkdir(parents=True, exist_ok=True)
        statutes_html, toc_html = statutes(lang, default)
        for page_file in sorted((SRC / "pages").glob("*.html")):
            page_id = page_file.stem
            nav = ""
            for item in t["nav"]:
                attrs = ' class="nav-cta"' if item.get("cta") else ""
                attrs += ' aria-current="page"' if item.get("page") == page_id else ""
                nav += f'<a href="{item["href"]}"{attrs}>{html.escape(item["label"])}</a>'
            switch = ""
            if len(langs) > 1:
                links = ""
                for code in langs:
                    current = ' aria-current="true"' if code == lang else ""
                    href = root + ("" if code == default else code + "/") + page_file.name
                    links += f'<a href="{href}" hreflang="{code}" lang="{code}"{current}>{code.upper()}</a>'
                switch = f'<div class="lang" aria-label="{html.escape(t["ui"]["language"])}">{links}</div>'
            ctx = dict(t, site=site, lang=lang, root=root, nav=nav, langSwitch=switch,
                       page=dict(t["pages"][page_id], id=page_id, file=page_file.name),
                       statutesHtml=statutes_html, statutesToc=toc_html)
            out = render(page_file.read_text("utf-8"), ctx, f"{lang}/{page_file.name}")
            (OUT / prefix / page_file.name).write_text(out, "utf-8")
            print(f"  {prefix}{page_file.name}")
    print(f"Built into {OUT}")


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print("Serving on http://localhost:8000 (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()
