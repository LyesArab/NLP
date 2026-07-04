"""
verifier.py — Final reasoning step: given ranked evidence, output SUPPORTED or REFUTED.

Three reasoning back-ends (controlled by Config.llm_provider):
  1. "groq"                → Groq API  (free tier, Llama 3 / Mixtral)
  2. "huggingface"         → HuggingFace Inference API (free tier)
  3. "sentence_transformer"→ heuristic similarity threshold (no API key needed)

The Groq and HuggingFace back-ends automatically fall back to the heuristic
if the API call fails or the key is missing.
"""
from typing import Dict, List, Optional, Tuple, Union

import requests

from src.evidence_ranker import EvidenceRanker
from src.utils import Config, get_logger

logger = get_logger(__name__)

Triple = Union[Dict, Tuple[str, str, str]]

_PROMPT_TEMPLATE = """\
You are a fact-checking assistant that verifies claims against knowledge-graph evidence.

Claim: {claim}

Knowledge-graph evidence:
{evidence}

Task: Decide whether the evidence SUPPORTS or REFUTES the claim.
Rules:
- Reply with exactly one word on the first line: SUPPORTED or REFUTED.
- Then give a one-sentence justification referencing the evidence.

Answer:"""

_NEGATION_WORDS = frozenset(
    ["not", "never", "no", "nobody", "nothing", "nor", "neither",
     "wasn't", "isn't", "aren't", "weren't", "hasn't", "hadn't",
     "doesn't", "didn't", "won't", "wouldn't", "can't", "couldn't"]
)


def _triple_label(triple: Triple) -> str:
    if isinstance(triple, dict):
        subj = triple.get("subject", "").rstrip("/").split("/")[-1].replace("_", " ")
        pred = triple.get("predicate", "").rstrip("/").split("/")[-1].split("#")[-1]
        obj_raw = triple.get("object", "")
        obj = obj_raw.rstrip("/").split("/")[-1].replace("_", " ") if obj_raw.startswith("http") else obj_raw
        return f"{subj}  --[{pred}]-->  {obj}"
    return f"{triple[0]}  --[{triple[1]}]-->  {triple[2]}"


class Verifier:
    def __init__(self, config: Config, ranker: EvidenceRanker):
        self.config = config
        self.ranker = ranker

    # ------------------------------------------------------------------ #
    #  LLM back-ends                                                       #
    # ------------------------------------------------------------------ #

    def _call_groq(self, claim: str, evidence_text: str) -> Tuple[str, str]:
        if not self.config.groq_api_key:
            raise RuntimeError("GROQ_API_KEY not set")
        payload = {
            "model": self.config.groq_model,
            "messages": [{"role": "user", "content": _PROMPT_TEMPLATE.format(claim=claim, evidence=evidence_text)}],
            "max_tokens": 150,
            "temperature": 0.0,
        }
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.config.groq_api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        verdict = "SUPPORTED" if "SUPPORTED" in content.upper() else "REFUTED"
        return verdict, content

    def _call_huggingface(self, claim: str, evidence_text: str) -> Tuple[str, str]:
        if not self.config.hf_api_key:
            raise RuntimeError("HF_API_KEY not set")
        prompt = _PROMPT_TEMPLATE.format(claim=claim, evidence=evidence_text)
        resp = requests.post(
            f"https://api-inference.huggingface.co/models/{self.config.hf_model}",
            headers={"Authorization": f"Bearer {self.config.hf_api_key}"},
            json={"inputs": prompt, "parameters": {"max_new_tokens": 150, "temperature": 0.01}},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        raw = data[0].get("generated_text", "") if isinstance(data, list) else str(data)
        # Strip echoed prompt
        content = raw[len(prompt):].strip() if raw.startswith(prompt) else raw.strip()
        verdict = "SUPPORTED" if "SUPPORTED" in content.upper() else "REFUTED"
        return verdict, content

    # ------------------------------------------------------------------ #
    #  Heuristic back-end (sentence-transformer only)                      #
    # ------------------------------------------------------------------ #

    def _heuristic(
        self,
        claim: str,
        ranked: List[Tuple[Triple, float]],
    ) -> Tuple[str, str]:
        """
        Simple but surprisingly effective heuristic:
        • If any top-K evidence has similarity ≥ threshold AND the claim
          does not contain a negation word → SUPPORTED.
        • Otherwise → REFUTED.
        """
        if not ranked:
            return "REFUTED", "No relevant evidence retrieved."

        THRESHOLD = 0.35
        claim_tokens = set(claim.lower().split())
        claim_negated = bool(claim_tokens & _NEGATION_WORDS)

        avg_score = sum(s for _, s in ranked) / len(ranked)
        max_score = max(s for _, s in ranked)

        evidence_summary = "\n".join(
            f"  [{score:.3f}] {_triple_label(t)}" for t, score in ranked
        )

        if max_score >= THRESHOLD and not claim_negated:
            verdict = "SUPPORTED"
            reason = f"Max evidence similarity {max_score:.3f} ≥ {THRESHOLD}; no negation in claim."
        elif max_score >= THRESHOLD and claim_negated:
            verdict = "REFUTED"
            reason = f"Evidence exists (similarity {max_score:.3f}) but claim contains negation."
        else:
            verdict = "REFUTED"
            reason = f"Insufficient evidence (max similarity {max_score:.3f} < {THRESHOLD})."

        explanation = f"{reason}\n\nTop evidence:\n{evidence_summary}"
        return verdict, explanation

    # ------------------------------------------------------------------ #
    #  Public interface                                                     #
    # ------------------------------------------------------------------ #

    def verify(
        self,
        claim: str,
        triples: List[Triple],
        path_triples: Optional[List[Tuple[str, str, str]]] = None,
    ) -> Dict:
        """
        Full reasoning step.

        Parameters
        ----------
        claim        : the natural-language claim to verify
        triples      : list of KG triple dicts from SPARQL
        path_triples : optional list of (subj, pred, obj) tuples from graph traversal

        Returns
        -------
        dict with keys: verdict, explanation, evidence, evidence_path, top_scores
        """
        # Merge and de-duplicate evidence sources
        ranked_sparql = self.ranker.rank(claim, triples)
        ranked_paths: List[Tuple] = []
        if path_triples:
            ranked_paths = self.ranker.rank_path_triples(claim, path_triples)

        # Use the higher-scoring source as primary evidence
        ranked = ranked_sparql or ranked_paths

        # Build human-readable evidence block for LLM prompts
        evidence_lines = [_triple_label(t) for t, _ in ranked]
        evidence_text = "\n".join(f"- {line}" for line in evidence_lines) or "No evidence found."

        # Choose back-end
        provider = self.config.llm_provider
        verdict, explanation = "REFUTED", "No evidence."

        if provider == "groq":
            try:
                verdict, explanation = self._call_groq(claim, evidence_text)
            except Exception as exc:
                logger.warning("Groq failed (%s) — using heuristic fallback", exc)
                verdict, explanation = self._heuristic(claim, ranked)

        elif provider == "huggingface":
            try:
                verdict, explanation = self._call_huggingface(claim, evidence_text)
            except Exception as exc:
                logger.warning("HuggingFace failed (%s) — using heuristic fallback", exc)
                verdict, explanation = self._heuristic(claim, ranked)

        else:  # "sentence_transformer" or unknown
            verdict, explanation = self._heuristic(claim, ranked)

        # Build evidence path (top-3 triples as tuples for display)
        evidence_path: List[Tuple[str, str, str]] = []
        for item, _ in ranked[:3]:
            if isinstance(item, dict):
                subj = item.get("subject", "").rstrip("/").split("/")[-1].replace("_", " ")
                pred = item.get("predicate", "").rstrip("/").split("/")[-1].split("#")[-1]
                obj_raw = item.get("object", "")
                obj = obj_raw.rstrip("/").split("/")[-1].replace("_", " ") if obj_raw.startswith("http") else obj_raw
                evidence_path.append((subj, pred, obj))
            else:
                evidence_path.append(item)

        return {
            "verdict": verdict,
            "explanation": explanation,
            "evidence": [t for t, _ in ranked],
            "evidence_path": evidence_path,
            "top_scores": [s for _, s in ranked[:5]],
        }
