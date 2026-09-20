from __future__ import annotations
import re
import json
from pathlib import Path
from typing import Any
from bs4 import BeautifulSoup

try:
    from .models import PageState, PageType, Claim, Statistic, Source, Argument
except ImportError:
    from core.models import PageState, PageType, Claim, Statistic, Source, Argument


class PageIngestion:
    def __init__(self, site_root: Path):
        self.site_root = Path(site_root)
        self.html_files = self._discover_html_files()

    def _discover_html_files(self) -> list[Path]:
        """Dynamically discover all HTML files in the repository"""
        files = list(self.site_root.glob("*.html"))
        # Exclude assets/diagram files
        files = [f for f in files if not any(part.startswith("assets") for part in f.parts)]
        return sorted(files)

    def _classify_page_type(self, filepath: Path, soup: BeautifulSoup) -> PageType:
        """Classify page based on filename and content"""
        name = filepath.stem.lower()
        
        if name == "index":
            return PageType.HOMEPAGE
        elif name == "contact":
            return PageType.CONTACT
        elif name == "blog":
            return PageType.BLOG_INDEX
        elif name == "ecommerce-whitepaper":
            return PageType.WHITEPAPER
        elif name in ["aeo", "ai-discovery", "ai-visibility-analytics", "technical-geo", "digital-pr",
                      "retail-media", "amazon", "ai-media", "consultancy", "measurement", "media"]:
            return PageType.SERVICE
        elif name in ["aeo-rankings-to-citations", "agentic-media-buying", "ai-in-retail-media",
                      "amazon-ai-creative-studio", "amazon-rufus-sponsored-prompts", "shoppable-ai-search"]:
            return PageType.ARTICLE
        elif name in ["beauty-media-strategy"]:
            return PageType.THOUGHT_LEADERSHIP
        return PageType.OTHER

    def _extract_meta(self, soup: BeautifulSoup) -> dict[str, str]:
        """Extract meta tags"""
        meta = {}
        for tag in soup.find_all("meta"):
            if tag.get("name"):
                meta[tag["name"]] = tag.get("content", "")
            elif tag.get("property"):
                meta[tag["property"]] = tag.get("content", "")
        return meta

    def _extract_schema(self, soup: BeautifulSoup) -> list[dict]:
        """Extract JSON-LD schema"""
        schemas = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    schemas.extend(data)
                else:
                    schemas.append(data)
            except json.JSONDecodeError:
                pass
        return schemas

    def _extract_headings(self, soup: BeautifulSoup) -> list[str]:
        """Extract all heading text"""
        headings = []
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            text = tag.get_text(strip=True)
            if text:
                headings.append(text)
        return headings

    def _extract_sections(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract semantic sections with their content"""
        sections = []
        
        # Find section elements and content areas
        for section in soup.find_all(["section", "div", "article"], class_=re.compile(r"(sec|bx|content|hero|cta|framework|applied|audit|problem|evidence|measure|deliverable|cta)")):
            section_data = {
                "id": section.get("id", ""),
                "classes": section.get("class", []),
                "heading": "",
                "text": section.get_text(" ", strip=True)[:500],
                "tag": section.name
            }
            
            # Find heading within section
            heading = section.find(["h1", "h2", "h3", "h4"])
            if heading:
                section_data["heading"] = heading.get_text(strip=True)
            
            if len(section_data["text"]) > 100:
                sections.append(section_data)
        
        return sections[:30]  # Limit to prevent overflow

    def _extract_body_text(self, soup: BeautifulSoup) -> str:
        """Extract clean body text for analysis"""
        # Remove scripts, styles, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "canvas"]):
            tag.decompose()
        
        text = soup.get_text(" ", strip=True)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text[:50000]  # Limit size

    def _extract_statistics(self, soup: BeautifulSoup, page_id: str) -> list[Statistic]:
        """Extract statistics from stat cards and data banners"""
        stats = []
        
        # Look for stat cards, data banners, dark-stats
        for container in soup.find_all(class_=re.compile(r"(stat-card|data-banner|dark-stat|big-stat)")):
            value_elem = container.find(class_=re.compile(r"\bv\b"))
            label_elem = container.find(class_=re.compile(r"\bl\b"))
            source_elem = container.find(class_=re.compile(r"\bs\b"))
            
            if value_elem and label_elem:
                stats.append(Statistic(
                    value=value_elem.get_text(strip=True),
                    label=label_elem.get_text(strip=True),
                    source=source_elem.get_text(strip=True) if source_elem else "",
                    context="",
                    page_id=page_id
                ))
        
        return stats

    def _extract_claims(self, soup: BeautifulSoup, page_id: str) -> list[Claim]:
        """Extract claims with supporting evidence"""
        claims = []
        body_text = self._extract_body_text(soup)
        
        # Look for claim-like patterns: "X is Y", "We have measured Z", "Research shows"
        claim_patterns = [
            r'We (have measured|have found|measured|found) ([^.]+)',
            r'Research (shows|indicates|suggests) ([^.]+)',
            r'(Studies|Study) (show|shows|indicate) ([^.]+)',
            r'(Source:|According to) ([^.]+)',
            r'(\d+%|\d+\.?\d*\s*(?:million|billion|trillion)) ([^.]+)',
        ]
        
        for pattern in claim_patterns:
            for match in re.finditer(pattern, body_text, re.IGNORECASE):
                claim_text = match.group(0)[:200]
                if len(claim_text) > 20:
                    claims.append(Claim(
                        text=claim_text,
                        claim_type="observation",
                        evidence=[],
                        sources=[],
                        confidence=0.5,
                        location=match.group(0)[:100]
                    ))
        
        return claims[:20]  # Limit

    def _extract_arguments(self, soup: BeautifulSoup, page_id: str) -> list[Argument]:
        """Extract arguments from the page"""
        arguments = []
        body_text = self._extract_body_text(soup)
        
        # Look for argument structures
        # This is a simplified extraction - real implementation would use LLM
        arg_indicators = [
            "The argument is", "The core argument", "The central point",
            "This means", "This suggests", "The implication",
            "The evidence shows", "The data indicates", "We argue"
        ]
        
        for indicator in arg_indicators:
            idx = body_text.find(indicator)
            if idx >= 0:
                arg_text = body_text[idx:idx+300]
                arguments.append(Argument(
                    id=f"{page_id}_arg_{len(arguments)}",
                    text=arg_text,
                    argument_type="core",
                    strength=0.7,
                    evidence=[],
                    is_distinctive=True
                ))
        
        return arguments[:10]

    def _extract_observations(self, soup: BeautifulSoup) -> list[str]:
        """Extract observations/insights"""
        observations = []
        body_text = self._extract_body_text(soup)
        
        obs_patterns = [
            r'(We notice|We observe|We see|The pattern is|The data reveals) ([^.]+)',
            r'(Interestingly|Notably|Surprisingly|Significantly), ([^.]+)',
        ]
        
        for pattern in obs_patterns:
            for match in re.finditer(pattern, body_text, re.IGNORECASE):
                observations.append(match.group(0)[:200])
        
        return observations[:15]

    def _extract_images(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        """Extract editorial images"""
        images = []
        for img in soup.find_all("img", class_=re.compile(r"(img-editorial|editorial)")):
            images.append({
                "src": img.get("src", ""),
                "alt": img.get("alt", ""),
                "class": " ".join(img.get("class", []))
            })
        return images

    def _extract_links(self, soup: BeautifulSoup) -> tuple[list[str], list[str], list[str]]:
        """Extract internal, external, and source links"""
        internal = []
        external = []
        sources = []
        
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http"):
                if "inflexion" in href or "nicksc1cc.github.io" in href:
                    internal.append(href)
                else:
                    external.append(href)
            elif href.startswith("#"):
                internal.append(href)
            elif href.endswith(".html") or "/" in href:
                internal.append(href)
        
        # Look for source citations
        for tag in soup.find_all(class_=re.compile(r"(source|citation|src)")):
            text = tag.get_text(strip=True)
            if text and len(text) > 10:
                sources.append(text)
        
        return internal, external, sources

    def ingest_page(self, filepath: Path) -> PageState:
        """Ingest a single HTML page into a PageState"""
        with open(filepath, "r", encoding="utf-8") as f:
            html = f.read()
        
        soup = BeautifulSoup(html, "html.parser")
        page_id = filepath.stem
        page_type = self._classify_page_type(filepath, soup)
        
        # Extract all data
        meta = self._extract_meta(soup)
        schemas = self._extract_schema(soup)
        headings = self._extract_headings(soup)
        sections = self._extract_sections(soup)
        body_text = self._extract_body_text(soup)
        statistics = self._extract_statistics(soup, page_id)
        claims = self._extract_claims(soup, page_id)
        arguments = self._extract_arguments(soup, page_id)
        observations = self._extract_observations(soup)
        images = self._extract_images(soup)
        internal_links, external_links, source_links = self._extract_links(soup)
        
        # Extract services, platforms, technologies, concepts from content
        services = self._extract_entities(body_text, "service")
        platforms = self._extract_entities(body_text, "platform")
        technologies = self._extract_entities(body_text, "technology")
        concepts = self._extract_entities(body_text, "concept")
        
        return PageState(
            page_id=page_id,
            url=f"https://nicksc1cc.github.io/inflexion-website/{filepath.name}",
            file_path=str(filepath),
            title=soup.title.string if soup.title else page_id,
            meta_title=meta.get("og:title", meta.get("twitter:title", "")),
            meta_description=meta.get("description", meta.get("og:description", meta.get("twitter:description", ""))),
            page_type=page_type,
            headings=headings,
            sections=sections,
            body_text=body_text,
            claims=claims,
            statistics=statistics,
            sources=[],  # Would need deeper parsing
            citations=[],
            arguments=arguments,
            observations=observations,
            recommendations=[],  # Extract from CTA sections
            conclusions=[],  # Extract from final sections
            services=services,
            platforms=platforms,
            technologies=technologies,
            concepts=concepts,
            images=images,
            internal_links=internal_links,
            external_links=external_links,
            source_links=source_links,
            previous_evaluations=[],
            quality_vector=None,
            issues=[],
            protected_content=[],
            relationships={}
        )

    def _extract_entities(self, text: str, entity_type: str) -> list[str]:
        """Extract named entities of a specific type from text"""
        entities = set()
        
        # Common entities by type
        entity_map = {
            "platform": ["ChatGPT", "Gemini", "Perplexity", "Claude", "Copilot", "Rufus", "Grok", "Amazon Rufus", "Google AI Mode", "Google AI Overviews"],
            "technology": ["A9", "DSP", "SSP", "PMP", "UCP", "ACP", "MPP", "Schema", "JSON-LD", "llms.txt", "robots.txt"],
            "service": ["AEO", "GEO", "SEO", "PR", "Retail Media", "Amazon Advertising", "Programmatic", "CTV", "DOOH"],
            "concept": ["share of answer", "share of shelf", "share of voice", "citation velocity", "entity graph", "prompt set", "zero-click", "agentic commerce"]
        }
        
        if entity_type in entity_map:
            for entity in entity_map[entity_type]:
                if entity.lower() in text.lower():
                    entities.add(entity)
        
        return sorted(entities)

    def ingest_all(self) -> dict[str, PageState]:
        """Ingest all pages and return a registry"""
        registry = {}
        for filepath in self.html_files:
            try:
                state = self.ingest_page(filepath)
                registry[state.page_id] = state
                print(f"  ✓ Ingested: {state.page_id} ({state.page_type.value})")
            except Exception as e:
                print(f"  ✗ Failed: {filepath.name} - {e}")
        return registry


import json