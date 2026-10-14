# Luke Priestley's website

Quarto source for https://lpriestley.github.io/.
GitHub repository: https://github.com/lpriestley/lpriestley.github.io

## Local preview

Install Quarto 1.2.269 (the version pinned in the publish workflow), then run from
this directory:

```sh
quarto preview --no-browser
```

Open the localhost address printed by Quarto. Stop the preview with Ctrl+C.
Use `quarto render` to build all five pages into `_site/`.

## Editing

- `index.qmd`: landing-page bio
- `research.qmd`, `data/publications.bib`, `apa.csl`: publications and formatting
- `writing.qmd`, `contact.qmd`: writing and contact pages
- `includes/nav.html`: shared portrait, navigation and profile links
- `styles.css`: shared typography and layout
- `assets/cv.pdf`: CV displayed by the locally hosted PDF.js viewer

Keep generated output, local experiments and credentials out of commits.
The `.gitignore` excludes these files; the project explicitly renders only
the five website pages.

## Publishing

The repository and website are public. GitHub Pages serves the site at
https://lpriestley.github.io/ from the `gh-pages` branch (`/ (root)`).

Commit and push source changes to `main` to run the Publish Site workflow, which
renders the website and publishes the output to `gh-pages`. It can also be run
manually from the repository's Actions tab.

For a manual deployment from this directory:

```sh
quarto publish gh-pages
```

Check the workflow result and the live homepage, Research page and embedded CV
after publishing. Local `quarto preview` and `quarto render` commands do not
publish anything.

## Optional ORCID updates

The Update Publications workflow runs weekly or on manual dispatch and requires
the repository Actions secret `ORCID_ACCESS_TOKEN` with `/read-public` access.
Set it in Settings > Secrets and variables > Actions. It is not required to
render or publish the existing bibliography.

The updater replaces `data/publications.bib` with ORCID records. Review how this
affects the curated list and citation keys before enabling it; the Research page
uses a specific key to annotate shared first authorship.

For a local trial that leaves the curated bibliography unchanged:

```sh
python -m pip install -r requirements.txt
python scripts/orcid_to_bib.py --token "$ORCID_ACCESS_TOKEN" --out /tmp/orcid-publications.bib
```
