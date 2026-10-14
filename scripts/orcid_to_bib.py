#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional

import requests

ORCID_API = "https://pub.orcid.org/v3.0"


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    words = [w for w in text.split() if w]
    return "".join(words[:4]) or "work"


def last_name(name: str) -> str:
    name = name.strip()
    if "," in name:
        return name.split(",", 1)[0].strip().lower()
    parts = name.split()
    return (parts[-1] if parts else "work").lower()


def normalize_doi(doi: str) -> str:
    doi = doi.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.I)
    return doi.lower()


def clean_value(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    return value


def score_entry(entry: Dict) -> int:
    score = 0
    if entry.get("doi"):
        score += 10
    if entry.get("title"):
        score += 3
    if entry.get("year"):
        score += 2
    if entry.get("author"):
        score += 2
    if entry.get("journal"):
        score += 1
    if entry.get("booktitle"):
        score += 1
    if entry.get("url"):
        score += 1
    return score


def extract_doi(work: Dict) -> Optional[str]:
    external_ids = work.get("external-ids", {}).get("external-id", []) or []
    for external_id in external_ids:
        if external_id.get("external-id-type", "").lower() == "doi":
            value = external_id.get("external-id-value")
            if value:
                return normalize_doi(value)
    return None


def extract_url(work: Dict) -> Optional[str]:
    url = work.get("url", {}).get("value")
    if url:
        return clean_value(url)
    external_ids = work.get("external-ids", {}).get("external-id", []) or []
    for external_id in external_ids:
        uri = external_id.get("external-id-url", {}).get("value")
        if uri:
            return clean_value(uri)
    return None


def extract_authors(work: Dict) -> Optional[str]:
    contributors = work.get("contributors", {}).get("contributor", []) or []
    if not contributors:
        return None
    ordered = []
    firsts = []
    additionals = []
    for contrib in contributors:
        name = contrib.get("credit-name", {}).get("value")
        if not name:
            continue
        seq = contrib.get("contributor-attributes", {}).get("contributor-sequence")
        if seq == "FIRST":
            firsts.append(name)
        else:
            additionals.append(name)
    ordered.extend(firsts + additionals)
    ordered = [clean_value(n) for n in ordered if n]
    if not ordered:
        return None
    return " and ".join(ordered)


def work_type_to_bib(work_type: str) -> str:
    mapping = {
        "JOURNAL_ARTICLE": "article",
        "CONFERENCE_PAPER": "inproceedings",
        "BOOK_CHAPTER": "incollection",
        "BOOK": "book",
        "THESIS": "phdthesis",
    }
    return mapping.get(work_type, "misc")


def build_entry(work: Dict) -> Dict:
    title_obj = work.get("title", {})
    title = title_obj.get("title", {}).get("value")
    subtitle = title_obj.get("subtitle", {}).get("value")
    full_title = ""
    if title:
        full_title = title
    if subtitle:
        full_title = f"{full_title}: {subtitle}" if full_title else subtitle

    pub_date = work.get("publication-date", {})
    year = pub_date.get("year", {}).get("value")

    authors = extract_authors(work)
    doi = extract_doi(work)
    url = extract_url(work)

    journal_title = work.get("journal-title", {}).get("value")
    work_type = work.get("type") or "misc"

    entrytype = work_type_to_bib(work_type)
    journal = clean_value(journal_title) if journal_title else None
    booktitle = None
    if work_type == "CONFERENCE_PAPER" and journal:
        booktitle = journal
        journal = None

    entry = {
        "entrytype": entrytype,
        "title": clean_value(full_title) if full_title else "Untitled work",
        "author": authors,
        "year": year,
        "doi": doi,
        "url": url,
        "journal": journal,
        "booktitle": booktitle,
        "_work_type": work_type,
    }
    return entry


def make_key(entry: Dict) -> str:
    author = entry.get("author") or "work"
    first_author = author.split(" and ")[0]
    last = last_name(first_author)
    year = entry.get("year") or "nd"
    title = entry.get("title") or "work"
    slug = slugify(title)
    return f"{last}{year}{slug}"


def dedupe_entries(entries: List[Dict]) -> List[Dict]:
    doi_groups: Dict[str, List[Dict]] = {}
    nodoi_groups: Dict[str, List[Dict]] = {}

    for entry in entries:
        doi = entry.get("doi")
        title_norm = re.sub(r"[^a-z0-9]", "", (entry.get("title") or "").lower())
        year = entry.get("year") or ""
        entry["_title_norm"] = title_norm
        entry["_year_norm"] = year
        if doi:
            doi_groups.setdefault(doi, []).append(entry)
        else:
            key = f"{title_norm}:{year}"
            nodoi_groups.setdefault(key, []).append(entry)

    selected: List[Dict] = []
    title_year_with_doi = set()

    for doi, group in doi_groups.items():
        best = sorted(group, key=lambda e: (-score_entry(e), e.get("_put_code", 0)))[0]
        selected.append(best)
        title_year_with_doi.add(f"{best.get('_title_norm')}:{best.get('_year_norm')}")

    for key, group in nodoi_groups.items():
        if key in title_year_with_doi:
            continue
        best = sorted(group, key=lambda e: (-score_entry(e), e.get("_put_code", 0)))[0]
        selected.append(best)

    return selected


def format_bibtex(entries: List[Dict]) -> str:
    field_order = ["author", "title", "year", "doi", "journal", "booktitle", "publisher", "url"]

    def bib_value(value: str) -> str:
        return "{" + value.replace("{", "\\{").replace("}", "\\}") + "}"

    lines = []
    for entry in entries:
        key = entry["_key"]
        entrytype = entry.get("entrytype", "misc")
        lines.append(f"@{entrytype}{{{key},")
        fields = {k: v for k, v in entry.items() if k in field_order and v}
        for field in field_order:
            if field in fields:
                lines.append(f"  {field} = {bib_value(str(fields[field]))},")
        extra_fields = sorted(k for k in entry.keys() if k not in field_order and not k.startswith("_") and k not in ("entrytype",))
        for field in extra_fields:
            value = entry.get(field)
            if value:
                lines.append(f"  {field} = {bib_value(str(value))},")
        if lines[-1].endswith(","):
            lines[-1] = lines[-1][:-1]
        lines.append("}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def fetch_orcid_works(orcid: str, token: str) -> List[Dict]:
    headers = {
        "Accept": "application/vnd.orcid+json",
        "Authorization": f"Bearer {token}",
    }
    works_url = f"{ORCID_API}/{orcid}/works"
    response = requests.get(works_url, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    groups = data.get("group", []) or []

    put_codes = []
    for group in groups:
        summaries = group.get("work-summary", []) or []
        for summary in summaries:
            put_code = summary.get("put-code")
            if put_code is not None:
                put_codes.append(int(put_code))

    entries = []
    for put_code in sorted(set(put_codes)):
        detail_url = f"{ORCID_API}/{orcid}/work/{put_code}"
        detail = requests.get(detail_url, headers=headers, timeout=30)
        detail.raise_for_status()
        work = detail.json()
        entry = build_entry(work)
        entry["_put_code"] = put_code
        entries.append(entry)

    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch ORCID works and generate BibTeX.")
    parser.add_argument("--orcid", default="0009-0003-9125-7265", help="ORCID iD")
    parser.add_argument("--token", required=True, help="ORCID access token with /read-public")
    parser.add_argument("--out", default="data/publications.bib", help="Output BibTeX file")
    args = parser.parse_args()

    entries = fetch_orcid_works(args.orcid, args.token)
    entries = dedupe_entries(entries)

    # Assign stable keys and resolve collisions
    used = set()
    for entry in entries:
        base_key = make_key(entry)
        key = base_key
        suffix = 0
        while key in used:
            suffix += 1
            key = f"{base_key}{chr(96 + suffix)}"
        used.add(key)
        entry["_key"] = key

    entries = sorted(entries, key=lambda e: e["_key"])
    bibtex = format_bibtex(entries)

    out_path = args.out
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("@comment{Generated by scripts/orcid_to_bib.py}\n\n")
        f.write(bibtex if bibtex.strip() else "")

    return 0


if __name__ == "__main__":
    sys.exit(main())
