"""
Inflexion Intelligence Engine — Page Ingestion
Phase 4: Page Ingestion
"""

from __future__ import annotations
import re
import json
from pathlib import Path
from typing import Any
from bs4 import BeautifulSoup
from datetime import datetime

try:
    from intelligence.core.models import PageState, PageType, Claim, Argument, Statistic
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from intelligence.core.models import PageState, PageType, Claim, Argument, Statistic


class PageIngestion:
    def __init__(self, site_root: Path):
        self.site_root = site_root

    def discover_pages(self) -> list[Path]:
        html_files = list(self.site_root.glob("*.html"))
        return [f for f in html_files if not f.name.startswith("_")]

    def classify_page_type(self, path: Path, soup: BeautifulSoup) -> PageType:
        name = path.stem.lower()
        if name == "index":
            return PageType.FOUNDATIONAL
        if name in ("aeo", "ai-discovery", "ai-visibility-analytics", "technical-geo", "digital-pr"):
            return PageType.SERVICE
        if name in ("retail-media", "amazon", "beauty-media-strategy"):
            return PageType.APPLICATION
        if name in ("ai-media", "media", "consultancy", "measurement"):
            return PageType.SERVICE
        if name in ("ecommerce-whitepaper",):
            return PageType.WHITEPAPER
        if name in ("contact",):
            return PageType.NAVIGATIONAL
        if name.startswith("blog-") or "blog" in name:
            return PageType.EDITORIAL
        return PageType.OTHER

    def extract_text(self, soup: BeautifulSoup) -> str:
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return re.sub(r"\s+", " ", text)

    def extract_headings(self, soup: BeautifulSoup) -> list[str]:
        headings = []
        for h in soup.find_all(["h1", "h2", "h3", "h4"]):
            text = h.get_text(strip=True)
            if text:
                headings.append(text)
        return headings

    def extract_sections(self, soup: BeautifulSoup) -> list[dict]:
        sections = []
        for section in soup.find_all(["section", "article"]):
            sec_id = section.get("id", "")
            heading = section.find(["h1", "h2", "h3", "h4"])
            heading_text = heading.get_text(strip=True) if heading else ""
            text = section.get_text(separator=" ", strip=True)
            if text and len(text) > 50:
                sections.append({
                    "id": sec_id,
                    "heading": heading_text,
                    "text": text[:5000]
                })
        return sections

    def extract_claims(self, soup: BeautifulSoup, page_id: str) -> list[Claim]:
        claims = []
        claim_id = 0
        text = self.extract_text(soup)
        sentences = re.split(r"[.!?]+", text)
        for i, sent in enumerate(sentences):
            sent = sent.strip()
            if len(sent) > 80 and any(kw in sent.lower() for kw in [
                "shows", "indicates", "reveals", "demonstrates", "proves",
                "study", "research", "data", "analysis", "found", "reports",
                "according to", "evidence", "suggests", "confirms"
            ]):
                claims.append(Claim(
                    claim_id=f"{page_id}_claim_{claim_id}",
                    text=sent,
                    page_id=page_id,
                    section_id=None,
                    evidence_refs=[],
                    claim_type="factual",
                    confidence=0.5,
                    is_central=False
                ))
                claim_id += 1
        return claims[:20]

    def extract_arguments(self, soup: BeautifulSoup, page_id: str) -> list[Argument]:
        arguments = []
        arg_id = 0
        for section in soup.find_all(["section", "article"]):
            heading = section.find(["h2", "h3"])
            if heading:
                text = section.get_text(separator=" ", strip=True)
                if len(text) > 200:
                    arguments.append(Argument(
                        argument_id=f"{page_id}_arg_{arg_id}",
                        text=text[:2000],
                        page_id=page_id,
                        claims=[],
                        objectives=[],
                        is_distinctive=False,
                        overlap_pages=[]
                    ))
                    arg_id += 1
        return arguments[:10]

    def extract_statistics(self, soup: BeautifulSoup, page_id: str) -> list[Statistic]:
        statistics = []
        text = self.extract_text(soup)
        stat_patterns = [
            r"(\d+(?:,\d{3})*(?:\.\d+)?%?)",
            r"(\$?\d+(?:,\d{3})*(?:\.\d+)?[MBK]?)",
        ]
        stat_id = 0
        for pattern in stat_patterns:
            for match in re.finditer(pattern, text):
                context_start = max(0, match.start() - 100)
                context_end = min(len(text), match.end() + 100)
                context = text[context_start:context_end].strip()
                statistics.append(Statistic(
                    statistic_id=f"{page_id}_stat_{stat_id}",
                    value=match.group(1),
                    context=context,
                    page_id=page_id,
                    source=None,
                    date=None,
                    used_on_pages=[]
                ))
                stat_id += 1
        return statistics[:30]

    def extract_evidence_refs(self, soup: BeautifulSoup) -> list[str]:
        refs = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if any(d in href for d in [".pdf", "study", "research", "report", "data", "source"]):
                refs.append(href)
        return list(set(refs))

    def extract_internal_links(self, soup: BeautifulSoup, site_root: Path) -> list[str]:
        links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.endswith(".html") and not href.startswith("http"):
                clean = href.replace(".html", "")
                links.append(clean)
        return list(set(links))

    def extract_images(self, soup: BeautifulSoup) -> list[dict]:
        images = []
        for img in soup.find_all("img"):
            images.append({
                "src": img.get("src", ""),
                "alt": img.get("alt", ""),
                "width": img.get("width", ""),
                "height": img.get("height", "")
            })
        return images

    def extract_schema(self, soup: BeautifulSoup) -> dict:
        scripts = soup.find_all("script", type="application/ld+json")
        schema = {}
        for script in scripts:
            try:
                schema = json.loads(script.string)
                break
            except:
                pass
        return schema

    def get_git_commit(self, path: Path) -> str:
        try:
            import subprocess
            result = subprocess.run(
                ["git", "log", "-1", "--format=%h", "--", str(path)],
                capture_output=True, text=True, cwd=self.site_root
            )
            return result.stdout.strip() or "unknown"
        except:
            return "unknown"

    def get_last_modified(self, path: Path) -> datetime:
        try:
            import subprocess
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ci", "--", str(path)],
                capture_output=True, text=True, cwd=self.site_root
            )
            if result.stdout.strip():
                return datetime.fromisoformat(result.stdout.strip().replace(" ", "T"))
        except:
            pass
        return datetime.fromtimestamp(path.stat().st_mtime)

    def ingest_page(self, path: Path) -> PageState:
        html = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")

        page_id = path.stem
        url = f"https://nicksc1cc.github.io/inflexion-website/{path.name}"
        title = soup.title.string if soup.title else page_id
        meta_title = ""
        meta_desc = ""
        for meta in soup.find_all("meta"):
            if meta.get("property") == "og:title":
                meta_title = meta.get("content", "")
            if meta.get("name") == "description":
                meta_desc = meta.get("content", "")

        page_type = self.classify_page_type(path, soup)
        body_text = self.extract_text(soup)
        headings = self.extract_headings(soup)
        sections = self.extract_sections(soup)
        claims = self.extract_claims(soup, page_id)
        arguments = self.extract_arguments(soup, page_id)
        statistics = self.extract_statistics(soup, page_id)
        evidence_refs = self.extract_evidence_refs(soup)
        internal_links = self.extract_internal_links(soup, self.site_root)
        images = self.extract_images(soup)
        schema = self.extract_schema(soup)
        git_commit = self.get_git_commit(path)
        last_modified = self.get_last_modified(path)

        topics = []
        entities = []

        return PageState(
            page_id=page_id,
            url=url,
            title=title,
            page_type=page_type,
            body_text=body_text,
            headings=headings,
            sections=sections,
            claims=claims,
            arguments=arguments,
            topics=topics,
            entities=entities,
            statistics=statistics,
            evidence_refs=evidence_refs,
            internal_links=internal_links,
            images=images,
            schema=schema,
            word_count=len(body_text.split()),
            last_modified=last_modified,
            git_commit=git_commit
        )

    def ingest_all(self) -> dict[str, PageState]:
        pages = {}
        for path in self.discover_pages():
            try:
                pages[path.stem] = self.ingest_page(path)
            except Exception as e:
                print(f"Failed to ingest {path}: {e}")
        return pages