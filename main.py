"""
main.py — FactKG Claim Verifier
================================
Full pipeline:
  Claim → NER (spaCy) → Entity Linking (DBpedia/Wikidata)
        → KG Retrieval (SPARQL) → Graph Paths (NetworkX)
        → Evidence Ranking (Sentence-Transformer)
        → Reasoning (Groq / HuggingFace / heuristic)
        → SUPPORTED | REFUTED + evidence path

Usage
-----
# Interactive mode (default when no --input given):
    python main.py

# Batch mode on a FactKG JSON file:
    python main.py --input data/train.json --limit 100

# Use Groq LLM (free):
    GROQ_API_KEY=<key> python main.py --llm groq --interactive
"""
import argparse
import os
import sys
from typing import Dict, List, Optional

from dotenv import load_dotenv
load_dotenv()  # loads .env into os.environ before Config is built

# If the user stored the key as KEY= instead of GROQ_API_KEY=, bridge it
if os.environ.get("KEY") and not os.environ.get("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = os.environ["KEY"]

from src.data_loader import Claim, load_claims
from src.entity_linking import EntityLinker
from src.evaluation import (
    compute_metrics,
    save_error_analysis,
    save_metrics,
    save_predictions,
)
from src.evidence_ranker import EvidenceRanker
from src.path_retrieval import PathRetriever
from src.sparql_retriever import SPARQLRetriever
from src.utils import Config, get_logger
from src.verifier import Verifier

logger = get_logger("main")


# ------------------------------------------------------------------ #
#  Single-claim pipeline                                               #
# ------------------------------------------------------------------ #

def verify_single(
    claim_text: str,
    linker: EntityLinker,
    retriever: SPARQLRetriever,
    path_retriever: PathRetriever,
    verifier: Verifier,
    verbose: bool = True,
    entity_set: Optional[List[str]] = None,
) -> Dict:
    if verbose:
        logger.info("=" * 60)
        logger.info("Claim: %s", claim_text)

    # 1. NER + Entity Linking
    if entity_set:
        ner_entities, linked_entities = linker.link_from_entity_set(claim_text, entity_set)
    else:
        ner_entities, linked_entities = linker.link(claim_text)
    if verbose:
        logger.info("NER     : %s", [e["text"] for e in ner_entities])
        logger.info("Linked  : %s", [e.get("uri", e.get("text")) for e in linked_entities[:5]])

    # 2. SPARQL retrieval
    triples = retriever.retrieve(linked_entities)
    if verbose:
        logger.info("Triples : %d retrieved from KG", len(triples))

    # 3. Graph construction + subgraph extraction
    entity_names = [e["text"] for e in ner_entities if e["label"] != "NOUN_CHUNK"]
    graph = path_retriever.build_graph(triples)
    path_triples = path_retriever.get_subgraph_triples(graph, entity_names, hops=2)
    if verbose:
        logger.info("Graph   : %d nodes, %d edges", graph.number_of_nodes(), graph.number_of_edges())

    # 4. Evidence ranking + 5. Reasoning
    result = verifier.verify(claim_text, triples, path_triples)

    if verbose:
        logger.info("Verdict : %s", result["verdict"])
        logger.info("Path    : %s", result["evidence_path"])
        logger.info("Explain : %.200s", result["explanation"])

    return result


# ------------------------------------------------------------------ #
#  Batch mode                                                          #
# ------------------------------------------------------------------ #

def run_batch(args: argparse.Namespace, config: Config) -> None:
    claims = load_claims(args.input)
    if args.limit:
        claims = claims[: args.limit]

    linker         = EntityLinker(config)
    retriever      = SPARQLRetriever(config)
    path_retriever = PathRetriever(config)
    ranker         = EvidenceRanker(config)
    verifier       = Verifier(config, ranker)

    results: List[Dict] = []
    for i, claim in enumerate(claims, 1):
        logger.info("[%d/%d] %s", i, len(claims), claim.text[:70])
        try:
            result = verify_single(
                claim.text, linker, retriever, path_retriever, verifier,
                verbose=False, entity_set=claim.entity_set or None,
            )
        except Exception as exc:
            logger.error("Error on claim %s: %s", claim.id, exc)
            result = {"verdict": "REFUTED", "explanation": str(exc), "evidence_path": [], "evidence": []}
        results.append(result)

    save_predictions(claims, results, os.path.join(config.results_dir, "predictions.csv"))

    labeled = [(c, r) for c, r in zip(claims, results) if c.label]
    if labeled:
        labeled_claims, labeled_results = zip(*labeled)
        metrics = compute_metrics(
            [r["verdict"] for r in labeled_results],
            [c.label for c in labeled_claims],
        )
        save_metrics(metrics, os.path.join(config.results_dir, "metrics.csv"))
        save_error_analysis(
            list(labeled_claims), list(labeled_results),
            os.path.join(config.results_dir, "error_analysis.csv"),
        )


# ------------------------------------------------------------------ #
#  Interactive mode                                                    #
# ------------------------------------------------------------------ #

def run_interactive(config: Config) -> None:
    linker         = EntityLinker(config)
    retriever      = SPARQLRetriever(config)
    path_retriever = PathRetriever(config)
    ranker         = EvidenceRanker(config)
    verifier       = Verifier(config, ranker)

    print("\n" + "=" * 60)
    print("  FactKG Claim Verifier  (type 'quit' to exit)")
    print("=" * 60 + "\n")

    while True:
        try:
            claim_text = input("Claim: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if claim_text.lower() in {"quit", "exit", "q", ""}:
            break

        result = verify_single(claim_text, linker, retriever, path_retriever, verifier)

        print(f"\n  Verdict  : {result['verdict']}")
        if result["evidence_path"]:
            print("  Evidence path:")
            for s, p, o in result["evidence_path"]:
                print(f"    {s}  --[{p}]-->  {o}")
        print()


# ------------------------------------------------------------------ #
#  Entry point                                                         #
# ------------------------------------------------------------------ #

def main() -> None:
    parser = argparse.ArgumentParser(
        description="FactKG Claim Verifier — verify claims against DBpedia/Wikidata"
    )
    parser.add_argument("--input",       type=str,   help="Path to dataset (.json or .csv)")
    parser.add_argument("--config",      type=str,   default=None, help="Config JSON file")
    parser.add_argument("--limit",       type=int,   default=None, help="Max claims to process")
    parser.add_argument("--llm",         type=str,   default=None,
                        choices=["groq", "huggingface", "sentence_transformer"],
                        help="LLM/reasoning back-end")
    parser.add_argument("--interactive", action="store_true",
                        help="Force interactive mode even when --input is given")
    args = parser.parse_args()

    config = Config.from_json(args.config) if args.config else Config()
    if args.llm:
        config.llm_provider = args.llm

    os.makedirs(config.results_dir, exist_ok=True)

    if args.interactive or not args.input:
        run_interactive(config)
    else:
        run_batch(args, config)


if __name__ == "__main__":
    main()
