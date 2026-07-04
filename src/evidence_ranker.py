"""
evidence_ranker.py — Rank KG triples by semantic similarity to the claim
using a Sentence-Transformer model (runs fully locally, no API key needed).
"""
from typing import Dict, List, Optional, Tuple, Union

import torch
from sentence_transformers import SentenceTransformer, util

from src.utils import Config, get_logger, triple_to_text

logger = get_logger(__name__)

# A triple can be either a dict (from SPARQL) or a (subj, pred, obj) tuple.
Triple = Union[Dict, Tuple[str, str, str]]


def _triple_to_sentence(triple: Triple) -> str:
    if isinstance(triple, dict):
        subj = triple.get("subject", "").rstrip("/").split("/")[-1].replace("_", " ")
        pred = triple.get("predicate", "")
        obj_raw = triple.get("object", "")
        obj = obj_raw.rstrip("/").split("/")[-1].replace("_", " ") if obj_raw.startswith("http") else obj_raw
        return triple_to_text(subj, pred, obj)
    # tuple
    return f"{triple[0]} {triple[1]} {triple[2]}"


class EvidenceRanker:
    def __init__(self, config: Config):
        self.config = config
        logger.info("Loading sentence-transformer: %s", config.sentence_transformer_model)
        self.model = SentenceTransformer(config.sentence_transformer_model)

    # ------------------------------------------------------------------ #
    #  Core ranking                                                        #
    # ------------------------------------------------------------------ #

    def _rank(self, claim: str, items: List, texts: List[str], top_k: int) -> List[Tuple]:
        if not items:
            return []
        claim_emb = self.model.encode(claim, convert_to_tensor=True)
        item_embs = self.model.encode(texts, convert_to_tensor=True)
        scores = util.cos_sim(claim_emb, item_embs)[0]
        k = min(top_k, len(items))
        top_idx = torch.topk(scores, k).indices.tolist()
        return [(items[i], float(scores[i])) for i in top_idx]

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def rank(
        self,
        claim: str,
        triples: List[Triple],
        top_k: Optional[int] = None,
    ) -> List[Tuple[Triple, float]]:
        """Rank *triples* (dicts or tuples) by relevance to *claim*."""
        k = top_k or self.config.top_k_evidence
        texts = [_triple_to_sentence(t) for t in triples]
        return self._rank(claim, triples, texts, k)

    def rank_path_triples(
        self,
        claim: str,
        path_triples: List[Tuple[str, str, str]],
        top_k: Optional[int] = None,
    ) -> List[Tuple[Tuple[str, str, str], float]]:
        """Rank subgraph / path triples by relevance to *claim*."""
        k = top_k or self.config.top_k_evidence
        texts = [f"{s} {p} {o}" for s, p, o in path_triples]
        return self._rank(claim, path_triples, texts, k)
