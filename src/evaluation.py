"""
evaluation.py — Compute and persist evaluation metrics.

Metrics computed: Accuracy, Precision, Recall, F1.
Outputs:
  results/predictions.csv  — per-claim results
  results/metrics.csv      — aggregate numbers
  results/error_analysis.csv — wrong predictions only
"""
import csv
import os
from typing import Dict, List

from src.data_loader import Claim
from src.utils import get_logger

logger = get_logger(__name__)


# ------------------------------------------------------------------ #
#  Label normalisation                                                 #
# ------------------------------------------------------------------ #

def _is_supported(label: str) -> bool:
    return "SUPPORT" in label.upper()


# ------------------------------------------------------------------ #
#  Metric computation                                                  #
# ------------------------------------------------------------------ #

def compute_metrics(predictions: List[str], labels: List[str]) -> Dict[str, float]:
    """
    Compute binary classification metrics treating SUPPORTED as positive.

    Parameters
    ----------
    predictions : list of predicted verdict strings
    labels      : list of ground-truth label strings
    """
    assert len(predictions) == len(labels), "Length mismatch between predictions and labels"

    tp = fp = tn = fn = 0
    for pred, label in zip(predictions, labels):
        pos_pred = _is_supported(pred)
        pos_true = _is_supported(label)
        if pos_pred and pos_true:
            tp += 1
        elif pos_pred and not pos_true:
            fp += 1
        elif not pos_pred and not pos_true:
            tn += 1
        else:
            fn += 1

    total = len(predictions)
    accuracy  = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "accuracy":  round(accuracy, 4),
        "precision": round(precision, 4),
        "recall":    round(recall, 4),
        "f1":        round(f1, 4),
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "total": total,
    }


# ------------------------------------------------------------------ #
#  CSV writers                                                         #
# ------------------------------------------------------------------ #

def save_predictions(claims: List[Claim], results: List[Dict], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "claim", "true_label", "predicted", "evidence_path", "explanation"])
        for claim, result in zip(claims, results):
            path_str = " | ".join(
                f"{s}→[{p}]→{o}" for s, p, o in result.get("evidence_path", [])
            )
            writer.writerow([
                claim.id,
                claim.text,
                claim.label or "",
                result.get("verdict", ""),
                path_str,
                result.get("explanation", "")[:300],
            ])
    logger.info("Saved predictions → %s", output_path)


def save_metrics(metrics: Dict, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for k, v in metrics.items():
            writer.writerow([k, v])
    logger.info("Metrics → %s  |  %s", output_path, metrics)


def save_error_analysis(claims: List[Claim], results: List[Dict], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    errors = []
    for claim, result in zip(claims, results):
        if not claim.label:
            continue
        pred = result.get("verdict", "")
        if _is_supported(pred) != _is_supported(claim.label):
            errors.append({
                "id": claim.id,
                "claim": claim.text,
                "true_label": claim.label,
                "predicted": pred,
                "evidence_path": str(result.get("evidence_path", [])),
                "explanation": result.get("explanation", "")[:200],
            })
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["id", "claim", "true_label", "predicted", "evidence_path", "explanation"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(errors)
    logger.info("Error analysis (%d errors) → %s", len(errors), output_path)
