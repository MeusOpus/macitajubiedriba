# Mācītāju atbalsta biedrība

Website of Mācītāju atbalsta biedrība (www.macitajubiedriba.lv). It's a static site with three pages: home, statutes and the join form. GitHub Pages hosts it, and the only build tool is the plain Python script in this repo.

## Run locally

```
python build.py --serve
```

Open http://localhost:8000. After you change something, stop the server (Ctrl+C) and run the command again. It needs Python 3.8+ and nothing else.

## Where things are

| What | File |
|---|---|
| All page text (Latvian) | `src/i18n/lv.json` |
| Statutes text | `src/content/statuti.lv.txt` |
| Page layouts | `src/pages/index.html`, `statuti.html`, `iestaties.html` |
| Header, footer, logo, `<head>` | `src/partials/` |
| Styles | `src/assets/css/site.css` (colors and fonts are at the top) |
| Menu, copy button, form sending | `src/assets/js/site.js` |
| Settings | `src/site.json` |
| Build script | `build.py` (template syntax is explained at the top) |

The build writes the finished site to `_site/`. Git ignores that folder because GitHub builds it again on every push.

### Changing text
Edit `src/i18n/lv.json`. Strings used with `{{{ }}}` in the templates can contain HTML, for example links.

### Changing the statutes
Edit `src/content/statuti.lv.txt`. A line like `7.nodaļa. Title` starts a chapter, and `7.1. Text` is a clause. The number of dots sets the indent level. Each chapter gets a link address, e.g. `statuti.html#nodala-4`, and each clause gets one too, e.g. `statuti.html#p4-3`.

> The old site's statutes skip **7.14** and **7.15.5**. Check them against the registered original.

### Before going live
1. **Connect the form to email.** Get a free access key at https://web3forms.com using the board's email address, `macitajubiedriba@gmail.com`. Put the key in `src/site.json` → `web3formsKey`. The key is meant to be public, so it can sit in the repo. Without it, the form only shows "not connected".
2. **Keep the member count current** (`home.about.facts` in `lv.json`).

## Adding a language later

1. Copy `src/i18n/lv.json` to `src/i18n/en.json` and translate the values. Keep the keys the same.
2. Optionally add `src/content/statuti.en.txt`. Without it, the Latvian statutes are used.
3. Add the code to `src/site.json`: `"languages": ["lv", "en"]`.

The first language stays at the site root, and English goes to `/en/`. Once there's more than one language, an LV/EN switch appears in the header automatically.

## Deploying to GitHub Pages

The workflow `.github/workflows/pages.yml` builds and deploys on every push to `main`. One-time setup in the repo: **Settings → Pages → Build and deployment → Source: GitHub Actions**.

### Domain: macitajubiedriba.lv
The site's main address is the bare domain **macitajubiedriba.lv**, set in `src/CNAME`. `www.macitajubiedriba.lv` forwards to it automatically.

DNS records at the domain registrar (nic.lv):
- `macitajubiedriba.lv`: four `A` records → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
- `www.macitajubiedriba.lv`: `CNAME` → `meusopus.github.io`

In **Settings → Pages**, the custom domain is `macitajubiedriba.lv`. Turn on **Enforce HTTPS** once the certificate is ready. Web3Forms must allow `macitajubiedriba.lv` as a domain.

### Old addresses
Pages from the old Weebly site (`stat363ti.html`, `iest257ties.html`, `kontakti.html`) forward to the new ones. The list is in `src/site.json` → `redirects`.
