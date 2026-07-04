"""
sparql_retriever.py — Retrieve triples from DBpedia and Wikidata via SPARQL.

For each linked entity the retriever fires two complementary queries:
  • outgoing triples  (<entity> ?p ?o)
  • incoming triples  (?s ?p <entity>)
Results are deduplicated and returned as plain Python dicts.
"""
from typing import Dict, List

from SPARQLWrapper import JSON, SPARQLWrapper

from src.utils import Config, get_logger

logger = get_logger(__name__)

# ------------------------------------------------------------------ #
#  SPARQL query templates                                              #
# ------------------------------------------------------------------ #

_DBPEDIA_Q = """
SELECT DISTINCT ?subject ?predicate ?object WHERE {{
  {{
    <{uri}> ?predicate ?object .
    BIND(<{uri}> AS ?subject)
    FILTER(!isBlank(?object))
  }}
  UNION
  {{
    ?subject ?predicate <{uri}> .
    BIND(<{uri}> AS ?object)
    FILTER(!isBlank(?subject))
  }}
}}
LIMIT {limit}
"""

_WIKIDATA_Q = """
SELECT DISTINCT ?prop ?propLabel ?value ?valueLabel WHERE {{
  wd:{qid} ?p ?stmt .
  ?stmt ?prop ?value .
  ?wdProp wikibase:statementProperty ?prop .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
  FILTER(!isBlank(?value))
  FILTER(!STRSTARTS(STR(?prop), "http://www.w3.org/"))
}}
LIMIT {limit}
"""


class SPARQLRetriever:
    def __init__(self, config: Config):
        self.config = config
        self._dbpedia: SPARQLWrapper | None = None
        self._wikidata: SPARQLWrapper | None = None

    # ------------------------------------------------------------------ #
    #  Lazy endpoint initialisation                                        #
    # ------------------------------------------------------------------ #

    def _dbpedia_ep(self) -> SPARQLWrapper:
        if self._dbpedia is None:
            ep = SPARQLWrapper(self.config.dbpedia_endpoint)
            ep.setReturnFormat(JSON)
            ep.setTimeout(self.config.sparql_timeout)
            self._dbpedia = ep
        return self._dbpedia

    def _wikidata_ep(self) -> SPARQLWrapper:
        if self._wikidata is None:
            ep = SPARQLWrapper(self.config.wikidata_endpoint)
            ep.addCustomHttpHeader("User-Agent", "FactKG-Verifier/1.0 (academic research)")
            ep.setReturnFormat(JSON)
            ep.setTimeout(self.config.sparql_timeout)
            self._wikidata = ep
        return self._wikidata

    # ------------------------------------------------------------------ #
    #  Per-source retrievers                                               #
    # ------------------------------------------------------------------ #

    def get_triples_dbpedia(self, uri: str) -> List[Dict]:
        query = _DBPEDIA_Q.format(uri=uri, limit=self.config.max_triples)
        try:
            ep = self._dbpedia_ep()
            ep.setQuery(query)
            bindings = ep.query().convert()["results"]["bindings"]
            triples = [
                {
                    "subject": b["subject"]["value"],
                    "predicate": b["predicate"]["value"],
                    "object": b["object"]["value"],
                    "source": "dbpedia",
                }
                for b in bindings
            ]
            logger.debug("DBpedia: %d triples for %s", len(triples), uri)
            return triples
        except Exception as exc:
            logger.warning("DBpedia SPARQL error (%s): %s", uri, exc)
            return []

    def get_triples_wikidata(self, qid: str) -> List[Dict]:
        query = _WIKIDATA_Q.format(qid=qid, limit=self.config.max_triples)
        try:
            ep = self._wikidata_ep()
            ep.setQuery(query)
            bindings = ep.query().convert()["results"]["bindings"]
            triples = [
                {
                    "subject": qid,
                    "predicate": b.get("propLabel", b["prop"])["value"],
                    "object": b.get("valueLabel", b["value"])["value"],
                    "source": "wikidata",
                }
                for b in bindings
            ]
            logger.debug("Wikidata: %d triples for %s", len(triples), qid)
            return triples
        except Exception as exc:
            logger.warning("Wikidata SPARQL error (%s): %s", qid, exc)
            return []

    # ------------------------------------------------------------------ #
    #  Public interface                                                     #
    # ------------------------------------------------------------------ #

    def retrieve(self, linked_entities: List[Dict]) -> List[Dict]:
        """Return all triples for every linked entity (deduplicated)."""
        all_triples: List[Dict] = []
        seen_uris: set = set()

        for entity in linked_entities:
            uri = entity.get("uri", "")
            if not uri or uri in seen_uris:
                continue
            seen_uris.add(uri)

            if "dbpedia.org" in uri:
                triples = self.get_triples_dbpedia(uri)
            elif "wikidata.org" in uri:
                qid = uri.rstrip("/").split("/")[-1]
                triples = self.get_triples_wikidata(qid)
            else:
                continue

            entity_name = entity.get("text", uri.split("/")[-1].replace("_", " "))
            for t in triples:
                t["entity_name"] = entity_name

            all_triples.extend(triples)

        logger.info("Retrieved %d KG triples total", len(all_triples))
        return all_triples
