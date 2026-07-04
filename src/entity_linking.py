"""
entity_linking.py — NER with spaCy + entity linking to DBpedia / Wikidata.

Pipeline
--------
1. spaCy  →  extract named entities & important noun chunks.
2. DBpedia Spotlight  →  map surface forms to DBpedia resource URIs.
3. Wikidata fallback  →  for any named entity not matched by Spotlight.
"""
import requests
import spacy
from typing import Dict, List, Optional, Tuple

from src.utils import Config, get_logger

logger = get_logger(__name__)


class EntityLinker:
    def __init__(self, config: Config):
        self.config = config
        logger.info("Loading spaCy model: %s", config.spacy_model)
        try:
            self.nlp = spacy.load(config.spacy_model)
        except OSError:
            logger.warning("Model not found — downloading %s …", config.spacy_model)
            spacy.cli.download(config.spacy_model)
            self.nlp = spacy.load(config.spacy_model)

    # ------------------------------------------------------------------ #
    #  Step 1 — spaCy NER                                                  #
    # ------------------------------------------------------------------ #

    def extract_entities(self, text: str) -> List[Dict]:
        """Return NER spans and prominent noun chunks from *text*."""
        doc = self.nlp(text)
        entities: List[Dict] = []
        seen: set = set()

        for ent in doc.ents:
            entities.append(
                {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
            )
            seen.add(ent.text.lower())

        # Include short noun chunks not already captured as named entities
        for chunk in doc.noun_chunks:
            if chunk.text.lower() not in seen and len(chunk.text.split()) <= 4:
                entities.append(
                    {"text": chunk.text, "label": "NOUN_CHUNK", "start": chunk.start_char, "end": chunk.end_char}
                )
                seen.add(chunk.text.lower())

        return entities

    # ------------------------------------------------------------------ #
    #  Step 2 — DBpedia Spotlight                                          #
    # ------------------------------------------------------------------ #

    def link_to_dbpedia(self, text: str) -> List[Dict]:
        """Call DBpedia Spotlight and return a list of linked entity dicts."""
        try:
            resp = requests.get(
                self.config.spotlight_url,
                headers={"Accept": "application/json"},
                params={"text": text, "confidence": self.config.spotlight_confidence},
                timeout=15,
            )
            if resp.status_code != 200:
                logger.warning("Spotlight HTTP %d", resp.status_code)
                return []
            resources = resp.json().get("Resources", [])
            return [
                {
                    "text": r["@surfaceForm"],
                    "uri": r["@URI"],
                    "types": r.get("@types", ""),
                    "label": "SPOTLIGHT",
                }
                for r in resources
            ]
        except requests.RequestException as exc:
            logger.warning("DBpedia Spotlight error: %s", exc)
            return []

    # ------------------------------------------------------------------ #
    #  Step 3 — Wikidata fallback                                          #
    # ------------------------------------------------------------------ #

    def link_to_wikidata(self, entity_text: str) -> Optional[Dict]:
        """Search Wikidata by label and return the top hit, or None."""
        try:
            resp = requests.get(
                "https://www.wikidata.org/w/api.php",
                params={
                    "action": "wbsearchentities",
                    "search": entity_text,
                    "language": "en",
                    "format": "json",
                    "limit": 1,
                },
                timeout=10,
            )
            results = resp.json().get("search", [])
            if results:
                item = results[0]
                return {
                    "text": entity_text,
                    "uri": f"http://www.wikidata.org/entity/{item['id']}",
                    "wikidata_id": item["id"],
                    "label": item.get("label", entity_text),
                    "description": item.get("description", ""),
                }
        except requests.RequestException as exc:
            logger.warning("Wikidata search error for '%s': %s", entity_text, exc)
        return None

    # ------------------------------------------------------------------ #
    #  Public interface                                                     #
    # ------------------------------------------------------------------ #

    def link_from_entity_set(self, text: str, entity_names: List[str]) -> Tuple[List[Dict], List[Dict]]:
        """
        Skip external APIs and build linked entities directly from a pre-linked
        entity name list (e.g. FactKG's ``Entity_set`` field).

        Each name like ``"John_E._Beck"`` is mapped to the DBpedia URI
        ``http://dbpedia.org/resource/John_E._Beck``.
        """
        ner_entities = self.extract_entities(text)
        linked: List[Dict] = [
            {
                "text": name.replace("_", " "),
                "uri": f"http://dbpedia.org/resource/{name}",
                "label": "ENTITY_SET",
            }
            for name in entity_names
        ]
        logger.debug("Using %d pre-linked entities for: %.60s", len(linked), text)
        return ner_entities, linked

    def link(self, text: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Run the full NER + linking pipeline.

        Returns
        -------
        ner_entities  : raw spaCy entities/chunks
        linked_entities : entities enriched with ``uri`` (DBpedia or Wikidata)
        """
        ner_entities = self.extract_entities(text)
        linked = self.link_to_dbpedia(text)

        if self.config.use_wikidata_fallback:
            spotlight_texts = {e["text"].lower() for e in linked}
            for ent in ner_entities:
                # Only attempt Wikidata for recognised named-entity types
                if ent["label"] == "NOUN_CHUNK":
                    continue
                if ent["text"].lower() not in spotlight_texts:
                    wd = self.link_to_wikidata(ent["text"])
                    if wd:
                        linked.append(wd)

        logger.debug("Linked %d entities for: %.60s", len(linked), text)
        return ner_entities, linked
