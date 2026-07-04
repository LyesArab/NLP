"""
data_loader.py — Load claims from FactKG (JSON, pickle) or generic CSV datasets.

FactKG JSON format  (https://github.com/jiho283/FactKG):
{
  "claim text": {
      "label": "SUPPORTS" | "REFUTES",
      "evidence": [["entity_uri", ...], ...]   ← optional
  },
  ...
}

FactKG pickle format:
{
  "claim text": {
      "Label": [True | False],
      "Entity_set": ["Entity_URI", ...],
      "Evidence": {"Entity_URI": [["predicate", ...], ...], ...},
      "types": ["type1", ...]
  },
  ...
}
"""
import csv
import json
import pickle
from dataclasses import dataclass, field
from typing import List, Optional

from src.utils import get_logger

logger = get_logger(__name__)


@dataclass
class Claim:
    id: str
    text: str
    label: Optional[str] = None          # "SUPPORTS" / "REFUTES" (or variants)
    evidence: List[List[str]] = field(default_factory=list)
    entity_set: List[str] = field(default_factory=list)  # pre-linked DBpedia entity names


# --------------------------------------------------------------------------- #
#  Loaders                                                                     #
# --------------------------------------------------------------------------- #

def load_factkg(path: str) -> List[Claim]:
    """Load the FactKG dataset stored as a JSON dict keyed by claim text."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    claims: List[Claim] = []
    for idx, (claim_text, info) in enumerate(data.items()):
        label = info.get("label") or info.get("annotation")
        evidence = info.get("evidence", [])
        if isinstance(evidence, str):
            evidence = [[evidence]]
        elif evidence and isinstance(evidence[0], str):
            evidence = [evidence]
        claims.append(Claim(id=str(idx), text=claim_text, label=label, evidence=evidence))

    logger.info("Loaded %d claims from %s", len(claims), path)
    return claims


def load_csv_claims(path: str) -> List[Claim]:
    """Load claims from a CSV file.

    Expected columns: ``claim`` (required), and optionally ``id`` and ``label``.
    """
    claims: List[Claim] = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            claims.append(
                Claim(
                    id=row.get("id", str(len(claims))),
                    text=row["claim"],
                    label=row.get("label") or row.get("annotation"),
                )
            )
    logger.info("Loaded %d claims from %s", len(claims), path)
    return claims


def load_pickle_claims(path: str) -> List[Claim]:
    """Load claims from a FactKG pickle file.

    Each entry has the form::

        {
            "Label":      [True | False],
            "Entity_set": ["Entity_URI", ...],
            "Evidence":   {"Entity_URI": [["predicate", ...], ...], ...},
            "types":      ["type1", ...]
        }

    ``True`` maps to ``"SUPPORTS"``, ``False`` to ``"REFUTES"``.
    """
    with open(path, "rb") as f:
        data = pickle.load(f)

    claims: List[Claim] = []
    for idx, (claim_text, info) in enumerate(data.items()):
        raw_label = info.get("Label", [None])[0]
        if raw_label is True:
            label = "SUPPORTS"
        elif raw_label is False:
            label = "REFUTES"
        else:
            label = None

        # Flatten evidence dict into list-of-entity-lists
        evidence_dict = info.get("Evidence", {})
        evidence = [
            [entity] + preds
            for entity, pred_lists in evidence_dict.items()
            for preds in pred_lists
        ]

        entity_set = info.get("Entity_set", [])
        claims.append(Claim(id=str(idx), text=claim_text, label=label, evidence=evidence, entity_set=entity_set))

    logger.info("Loaded %d claims from %s", len(claims), path)
    return claims


def load_claims(path: str) -> List[Claim]:
    """Auto-detect format and load claims."""
    if path.endswith(".json"):
        return load_factkg(path)
    if path.endswith(".csv"):
        return load_csv_claims(path)
    if path.endswith(".pickle") or path.endswith(".pkl"):
        return load_pickle_claims(path)
    raise ValueError(f"Unsupported file format: {path}  (expected .json, .csv, or .pickle)")
