# Book site (GitHub Pages)

The landing page for *Hands-On RAG for Production* is this `docs/` folder, served by
GitHub Pages at:

**https://ofermend.github.io/hands-on-rag/**

It's a single static page (`index.html` + `styles.css`), no build step — the files here
are both the source and what gets served. GitHub Pages treats `docs/` as the site root,
so the chapter code at the repo root is untouched.

## Update / redeploy

Edit `index.html` / `styles.css`, then from the repo root:

```bash
git add docs
git commit -s -m "Update book site"
git push origin main
```

Pages rebuilds automatically within ~1–2 minutes.

## First-time: enable Pages (branch = `main`, folder = `/docs`)

Only needed once.

```bash
gh api --method POST /repos/ofermend/hands-on-rag/pages \
  -f 'source[branch]=main' -f 'source[path]=/docs'
```

Or via the web UI: **Settings → Pages → Source:** "Deploy from a branch" →
**Branch:** `main` · **Folder:** `/docs` → **Save**.

Verify:

```bash
gh api /repos/ofermend/hands-on-rag/pages --jq '{status: .status, url: .html_url}'
curl -sS -o /dev/null -w "%{http_code}\n" https://ofermend.github.io/hands-on-rag/
curl -sS -o /dev/null -w "%{http_code}\n" https://ofermend.github.io/hands-on-rag/styles.css
```

Both `curl` calls should print `200`.

## Custom domain (optional)

1. Add a `CNAME` file in this `docs/` folder containing just the domain, e.g.
   `handsonrag.com`.
2. Set it under **Settings → Pages → Custom domain**.
3. DNS: apex domain → four `A` records (`185.199.108.153`, `.109.153`, `.110.153`,
   `.111.153`); or subdomain → `CNAME` to `ofermend.github.io`.
4. Enable **Enforce HTTPS**.

## Real cover art

The hero shows a CSS book mockup. To use the real cover, put `cover.jpg` in this folder
and replace the `<div class="book">…</div>` block in `index.html` with:

```html
<img src="cover.jpg" alt="Hands-On RAG for Production" class="book-img" />
```
