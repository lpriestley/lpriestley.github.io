# Luke Priestley's website

Quarto source for https://lpriestley.github.io/.
GitHub repository: https://github.com/lpriestley/lpriestley.github.io

## Local preview

Install Quarto, then run from this directory:

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

## First publication (only when ready to go live)

The repository is private. Public GitHub Pages hosting from a private personal
repository requires GitHub Pro. Confirm plan eligibility before publishing.

1. Push the source on `main` to the configured `origin` repository.
2. Run `quarto publish gh-pages` to initialise the published branch and publishing
   configuration. This command publishes the website publicly.
3. In GitHub Settings > Pages, select Deploy from a branch, `gh-pages`, `/ (root)`.
4. If Quarto creates `_publish.yml`, commit and push it. Verify the Publish Site
   workflow and the live homepage, Research page and embedded CV.

The publish workflow runs on pushes to `main` and manual dispatch. After the
initial setup, pushing changes to `main` updates the live website.

Private source does not make the rendered site private: published pages, images,
the CV and other site assets can be accessed by visitors.

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
