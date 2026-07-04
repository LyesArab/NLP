"""
path_retrieval.py — Build a NetworkX graph from retrieved KG triples and
extract local subgraphs / shortest paths relevant to the entities in a claim.
"""
from typing import Dict, List, Tuple

import networkx as nx

from src.utils import Config, get_logger

logger = get_logger(__name__)


def _node_label(uri_or_literal: str) -> str:
    """Convert a URI or raw literal to a human-readable label."""
    if uri_or_literal.startswith("http"):
        return uri_or_literal.rstrip("/").split("/")[-1].replace("_", " ")
    return uri_or_literal


def _pred_label(uri_or_literal: str) -> str:
    return uri_or_literal.rstrip("/").split("/")[-1].split("#")[-1]


class PathRetriever:
    def __init__(self, config: Config):
        self.config = config

    # ------------------------------------------------------------------ #
    #  Graph construction                                                  #
    # ------------------------------------------------------------------ #

    def build_graph(self, triples: List[Dict]) -> nx.DiGraph:
        """Build a directed labelled graph from a list of triple dicts."""
        G = nx.DiGraph()
        for t in triples:
            subj = _node_label(t["subject"])
            pred = _pred_label(t["predicate"])
            obj = _node_label(t["object"])
            G.add_edge(subj, obj, predicate=pred)
        logger.debug("Graph: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())
        return G

    # ------------------------------------------------------------------ #
    #  Entity → node matching (fuzzy)                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _match_nodes(G: nx.DiGraph, entity: str) -> List[str]:
        """Return graph nodes that partially match *entity*."""
        ent_lower = entity.lower().replace("_", " ")
        return [
            node
            for node in G.nodes()
            if ent_lower in node.lower() or node.lower() in ent_lower
        ]

    # ------------------------------------------------------------------ #
    #  Path finding                                                        #
    # ------------------------------------------------------------------ #

    def find_paths(
        self,
        G: nx.DiGraph,
        entities: List[str],
        max_hops: int = 3,
    ) -> List[List[Tuple[str, str, str]]]:
        """
        Find all simple paths between any pair of entity nodes (up to *max_hops*).
        Returns a list of triple-chains, each chain being [(subj, pred, obj), …].
        """
        # Resolve each entity to at most one graph node
        entity_nodes: List[str] = []
        for ent in entities:
            matches = self._match_nodes(G, ent)
            if matches:
                entity_nodes.append(matches[0])

        if len(entity_nodes) < 2:
            return []

        paths: List[List[Tuple[str, str, str]]] = []
        for i, src in enumerate(entity_nodes):
            for dst in entity_nodes[i + 1:]:
                try:
                    for node_path in nx.all_simple_paths(G, src, dst, cutoff=max_hops):
                        chain = []
                        for j in range(len(node_path) - 1):
                            data = G.get_edge_data(node_path[j], node_path[j + 1]) or {}
                            chain.append((node_path[j], data.get("predicate", "relatedTo"), node_path[j + 1]))
                        paths.append(chain)
                except nx.NetworkXError:
                    pass

        return paths

    # ------------------------------------------------------------------ #
    #  Subgraph extraction                                                 #
    # ------------------------------------------------------------------ #

    def get_subgraph_triples(
        self,
        G: nx.DiGraph,
        entities: List[str],
        hops: int = 2,
    ) -> List[Tuple[str, str, str]]:
        """
        Return all triples within *hops* graph steps of any entity node.
        This gives a broader neighbourhood than strict path finding.
        """
        seed_nodes: set = set()
        for ent in entities:
            seed_nodes.update(self._match_nodes(G, ent))

        frontier = set(seed_nodes)
        for _ in range(hops):
            new_nodes: set = set()
            for node in frontier:
                new_nodes.update(G.successors(node))
                new_nodes.update(G.predecessors(node))
            frontier.update(new_nodes)

        triples: List[Tuple[str, str, str]] = []
        for u, v, data in G.edges(data=True):
            if u in frontier or v in frontier:
                triples.append((u, data.get("predicate", "relatedTo"), v))

        return triples
