import logging
import os
import json
from dataclasses import dataclass, field
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


@dataclass
class Config:
    # NER
    spacy_model: str = "en_core_web_sm"

    # Entity Linking
    spotlight_url: str = "https://api.dbpedia-spotlight.org/en/annotate"
    spotlight_confidence: float = 0.5
    use_wikidata_fallback: bool = True

    # SPARQL
    dbpedia_endpoint: str = "https://dbpedia.org/sparql"
    wikidata_endpoint: str = "https://query.wikidata.org/sparql"
    sparql_timeout: int = 30
    max_triples: int = 50

    # Evidence Ranking
    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    top_k_evidence: int = 5

    # LLM — free alternatives:
    #   "groq"                → Groq API (Llama 3, free tier, set GROQ_API_KEY)
    #   "huggingface"         → HuggingFace Inference API (free tier, set HF_API_KEY)
    #   "sentence_transformer"→ no API key needed (heuristic similarity)
    llm_provider: str = "sentence_transformer"
    groq_model: str = "llama3-8b-8192"
    groq_api_key: str = field(default_factory=lambda: os.environ.get("GROQ_API_KEY", ""))
    hf_api_key: str = field(default_factory=lambda: os.environ.get("HF_API_KEY", ""))
    hf_model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"

    # Output
    results_dir: str = "results"

    @classmethod
    def from_json(cls, path: str) -> "Config":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)


def normalize_entity(entity: str) -> str:
    return entity.strip().replace(" ", "_")


def triple_to_text(subject: str, predicate: str, obj: str) -> str:
    """Convert a KG triple to a readable sentence fragment."""
    pred_clean = predicate.split("/")[-1].split("#")[-1]
    # camelCase → words
    words = []
    buf = ""
    for ch in pred_clean:
        if ch.isupper() and buf:
            words.append(buf)
            buf = ch
        else:
            buf += ch
    if buf:
        words.append(buf)
    pred_clean = " ".join(words).lower()
    return f"{subject} {pred_clean} {obj}"
