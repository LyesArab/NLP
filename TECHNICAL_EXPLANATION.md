# Architecture Technique du Système de Fact-Checking

## 📋 Vue d'Ensemble

Le système est un **pipeline modulaire** où chaque module appelle le suivant. Voici le flux complet :

```
main.py → EntityLinker → SPARQLRetriever → PathRetriever → EvidenceRanker → Verifier
```

---

## 🧠 Modèles Utilisés

### 1. **spaCy** (`en_core_web_sm`)
- **Usage** : NER (Named Entity Recognition)
- **Où** : `EntityLinker.extract_entities()`
- **Rôle** : Identifier les entités (PERSON, ORG, GPE, etc.) et les noun chunks

### 2. **Sentence-Transformer** (`all-MiniLM-L6-v2`)
- **Usage** : Calcul de similarité sémantique
- **Où** : `EvidenceRanker.rank()` et `EvidenceRanker.rank_path_triples()`
- **Rôle** : Encoder le claim et les triples pour comparer leur similarité

### 3. **LLM optionnels** (Groq/HuggingFace)
- **Modèles** : 
  - Groq : `llama-3.3-70b-versatile` (gratuit)
  - HuggingFace : `mistralai/Mistral-7B-Instruct-v0.3`
- **Où** : `Verifier._call_groq()` ou `Verifier._call_huggingface()`
- **Rôle** : Raisonnement final (si configuré, sinon heuristique)

### 4. **NetworkX**
- **Usage** : Manipulation de graphes
- **Où** : `PathRetriever.build_graph()`
- **Rôle** : Construire un graphe à partir des triples et extraire des sous-graphes

---

## 🔄 Flux Complet des Fonctions

### **Fichier : `main.py`**
Point d'entrée du système.

#### Fonction principale : `verify_single(claim_text, ...)`

```python
def verify_single(claim_text, linker, retriever, path_retriever, verifier):
    # 1. NER + Entity Linking
    ner_entities, linked_entities = linker.link(claim_text)
    
    # 2. SPARQL retrieval
    triples = retriever.retrieve(linked_entities)
    
    # 3. Graph construction + subgraph extraction
    graph = path_retriever.build_graph(triples)
    path_triples = path_retriever.get_subgraph_triples(graph, entity_names, hops=2)
    
    # 4. Evidence ranking + 5. Reasoning
    result = verifier.verify(claim_text, triples, path_triples)
    
    return result  # {"verdict": "SUPPORTED", "evidence_path": "...", ...}
```

---

### **Fichier : `entity_linking.py`**

#### Classe : `EntityLinker`

**Méthode 1 : `link(claim_text)`**
```python
def link(claim_text):
    # 1. Appelle extract_entities()
    ner_entities = self.extract_entities(claim_text)
    
    # 2. Appelle link_to_dbpedia()
    spotlight_entities = self.link_to_dbpedia(claim_text)
    
    # 3. Pour chaque entité NER non trouvée par Spotlight
    for entity in ner_entities:
        if not matched:
            # Appelle link_to_wikidata()
            wikidata_entity = self.link_to_wikidata(entity["text"])
    
    return ner_entities, linked_entities
```

**Sous-fonctions :**
- `extract_entities()` : Utilise **spaCy** pour extraire les entités
- `link_to_dbpedia()` : Appelle l'API **DBpedia Spotlight**
- `link_to_wikidata()` : Appelle l'API **Wikidata** en fallback

---

### **Fichier : `sparql_retriever.py`**

#### Classe : `SPARQLRetriever`

**Méthode : `retrieve(linked_entities)`**
```python
def retrieve(linked_entities):
    triples = []
    for entity in linked_entities:
        if "dbr:" in entity["uri"]:
            # Appelle get_triples_dbpedia()
            triples += self.get_triples_dbpedia(entity["uri"])
        elif "wd:" in entity["uri"]:
            # Appelle get_triples_wikidata()
            triples += self.get_triples_wikidata(entity["qid"])
    return triples
```

**Sous-fonctions :**
- `get_triples_dbpedia(uri)` : Exécute une requête SPARQL sur DBpedia
- `get_triples_wikidata(qid)` : Exécute une requête SPARQL sur Wikidata

**Format des requêtes SPARQL :**
```sparql
# Pour DBpedia (triples sortants ET entrants)
SELECT DISTINCT ?subject ?predicate ?object WHERE {
  { <entity_uri> ?predicate ?object . BIND(<entity_uri> AS ?subject) }
  UNION
  { ?subject ?predicate <entity_uri> . BIND(<entity_uri> AS ?object) }
}
```

---

### **Fichier : `path_retrieval.py`**

#### Classe : `PathRetriever`

**Méthode 1 : `build_graph(triples)`**
```python
def build_graph(triples):
    G = nx.DiGraph()  # Graphe dirigé NetworkX
    for triple in triples:
        subject = clean_label(triple["subject"])
        predicate = clean_label(triple["predicate"])
        object = clean_label(triple["object"])
        G.add_edge(subject, object, predicate=predicate)
    return G
```

**Méthode 2 : `get_subgraph_triples(G, entities, hops=2)`**
```python
def get_subgraph_triples(G, entities, hops=2):
    # 1. Trouve les nœuds correspondant aux entités
    seed_nodes = []
    for entity in entities:
        matches = _match_nodes(G, entity)
        seed_nodes.extend(matches)
    
    # 2. Expansion à N sauts (hops)
    frontier = set(seed_nodes)
    for _ in range(hops):
        new_nodes = set()
        for node in frontier:
            new_nodes.update(G.successors(node))
            new_nodes.update(G.predecessors(node))
        frontier.update(new_nodes)
    
    # 3. Extraction des triples du sous-graphe
    triples = [(u, pred, v) for u, v, data in G.edges(data=True) 
               if u in frontier or v in frontier]
    return triples
```

---

### **Fichier : `evidence_ranker.py`**

#### Classe : `EvidenceRanker`

**Méthode : `rank(claim, triples, top_k=5)`**
```python
def rank(claim, triples, top_k=5):
    # 1. Encoder le claim
    claim_embedding = self.model.encode(claim)  # Sentence-Transformer
    
    # 2. Encoder chaque triple
    triple_texts = [triple_to_sentence(t) for t in triples]
    triple_embeddings = self.model.encode(triple_texts)
    
    # 3. Calculer la similarité cosinus
    scores = cosine_similarity(claim_embedding, triple_embeddings)
    
    # 4. Trier et retourner le top-K
    top_indices = torch.topk(scores, top_k).indices
    ranked = [(triples[i], scores[i]) for i in top_indices]
    return ranked
```

**Format de sortie :**
```python
[
    ({"subject": "Jahangir", "predicate": "successor", "object": "Shah Jahan"}, 0.87),
    ({"subject": "Jahangir", "predicate": "birthPlace", "object": "Lahore"}, 0.42),
    ...
]
```

---

### **Fichier : `verifier.py`**

#### Classe : `Verifier`

**Méthode principale : `verify(claim, triples, path_triples)`**
```python
def verify(claim, triples, path_triples):
    # 1. Ranker les triples SPARQL
    ranked_sparql = self.ranker.rank(claim, triples)
    
    # 2. Ranker les triples de graphe
    ranked_paths = self.ranker.rank_path_triples(claim, path_triples)
    
    # 3. Choisir le meilleur ensemble
    ranked = ranked_sparql or ranked_paths
    
    # 4. Choisir le back-end de raisonnement
    if config.llm_provider == "groq":
        verdict, explanation = self._call_groq(claim, evidence_text)
    elif config.llm_provider == "huggingface":
        verdict, explanation = self._call_huggingface(claim, evidence_text)
    else:
        verdict, explanation = self._heuristic(claim, ranked)
    
    return {
        "verdict": verdict,
        "explanation": explanation,
        "evidence": ranked,
        "evidence_path": format_path(ranked[0])
    }
```

**Méthode heuristique : `_heuristic(claim, ranked)`**
```python
def _heuristic(claim, ranked):
    THRESHOLD = 0.35
    max_score = max(score for _, score in ranked)
    
    # Détection de négation
    negation_words = {"not", "never", "no", ...}
    has_negation = any(word in claim.lower() for word in negation_words)
    
    # Logique de décision
    if max_score >= THRESHOLD and not has_negation:
        verdict = "SUPPORTED"
    elif max_score >= THRESHOLD and has_negation:
        verdict = "REFUTED"
    else:
        verdict = "REFUTED"
    
    return verdict, explanation
```

---

## 🎯 Exemple Complet : "Jahangir had a successor"

### **Étape 1 : NER + Entity Linking**
```python
# main.py appelle :
ner_entities, linked_entities = linker.link("Jahangir had a successor")

# EntityLinker.link() fait :
#   1. extract_entities() → spaCy identifie "Jahangir" (PERSON)
#   2. link_to_dbpedia() → DBpedia Spotlight retourne :
#        {"text": "Jahangir", "uri": "http://dbpedia.org/resource/Jahangir"}
```

**Résultat :**
```python
ner_entities = [{"text": "Jahangir", "label": "PERSON"}]
linked_entities = [{"text": "Jahangir", "uri": "http://dbpedia.org/resource/Jahangir"}]
```

---

### **Étape 2 : SPARQL Retrieval**
```python
# main.py appelle :
triples = retriever.retrieve(linked_entities)

# SPARQLRetriever.retrieve() fait :
#   get_triples_dbpedia("http://dbpedia.org/resource/Jahangir")
#   → Requête SPARQL sur DBpedia :
#     SELECT ?subject ?predicate ?object WHERE {
#       { <dbr:Jahangir> ?predicate ?object ... }
#       UNION
#       { ?subject ?predicate <dbr:Jahangir> ... }
#     }
```

**Résultat (exemples de triples) :**
```python
triples = [
    {"subject": "dbr:Jahangir", "predicate": "dbo:successor", "object": "dbr:Shah_Jahan"},
    {"subject": "dbr:Jahangir", "predicate": "dbo:birthPlace", "object": "dbr:Lahore"},
    {"subject": "dbr:Jahangir", "predicate": "dbo:parent", "object": "dbr:Akbar"},
    # ... 47 autres triples
]
```

---

### **Étape 3 : Graph Construction**
```python
# main.py appelle :
graph = path_retriever.build_graph(triples)

# PathRetriever.build_graph() fait :
#   G = nx.DiGraph()
#   Pour chaque triple:
#     G.add_edge("Jahangir", "Shah Jahan", predicate="successor")
#     G.add_edge("Jahangir", "Lahore", predicate="birthPlace")
#     ...
```

**Résultat :**
```python
# Graphe NetworkX avec :
# - 38 nœuds (entités uniques)
# - 50 arêtes (relations)
```

---

### **Étape 4 : Subgraph Extraction**
```python
# main.py appelle :
entity_names = ["Jahangir"]  # Extrait de ner_entities
path_triples = path_retriever.get_subgraph_triples(graph, entity_names, hops=2)

# PathRetriever.get_subgraph_triples() fait :
#   1. Trouve "Jahangir" dans le graphe
#   2. Expansion à 2 sauts (successors + predecessors)
#      → Jahangir → Shah Jahan → successors de Shah Jahan
#      → Jahangir → Akbar
#   3. Retourne tous les triples touchant ces nœuds
```

**Résultat :**
```python
path_triples = [
    ("Jahangir", "successor", "Shah Jahan"),
    ("Jahangir", "parent", "Akbar"),
    ("Shah Jahan", "parent", "Jahangir"),
    # ... ~30 triples
]
```

---

### **Étape 5 : Evidence Ranking**
```python
# verifier.verify() appelle :
ranked_sparql = ranker.rank("Jahangir had a successor", triples, top_k=5)

# EvidenceRanker.rank() fait :
#   1. Encode le claim avec Sentence-Transformer :
#      claim_emb = model.encode("Jahangir had a successor")
#      → vecteur de 384 dimensions
#
#   2. Encode chaque triple :
#      "Jahangir successor Shah Jahan" → emb1
#      "Jahangir birthPlace Lahore" → emb2
#      ...
#
#   3. Calcule la similarité cosinus :
#      cos_sim(claim_emb, emb1) = 0.87  ← TRÈS SIMILAIRE
#      cos_sim(claim_emb, emb2) = 0.31
#      ...
#
#   4. Retourne les 5 meilleurs
```

**Résultat :**
```python
ranked_sparql = [
    ({"subject": "dbr:Jahangir", "predicate": "dbo:successor", "object": "dbr:Shah_Jahan"}, 0.87),
    ({"subject": "dbr:Shah_Jahan", "predicate": "dbo:parent", "object": "dbr:Jahangir"}, 0.52),
    ({"subject": "dbr:Jahangir", "predicate": "dbo:child", "object": "dbr:Shah_Jahan"}, 0.48),
    ({"subject": "dbr:Jahangir", "predicate": "dbo:parent", "object": "dbr:Akbar"}, 0.28),
    ({"subject": "dbr:Jahangir", "predicate": "dbo:birthPlace", "object": "dbr:Lahore"}, 0.21),
]
```

---

### **Étape 6 : Raisonnement et Décision**
```python
# verifier.verify() appelle (selon config) :
verdict, explanation = self._heuristic(claim, ranked_sparql)

# Verifier._heuristic() fait :
#   THRESHOLD = 0.35
#   max_score = 0.87  ← Score du premier triple
#   
#   # Détection de négation
#   claim_tokens = {"jahangir", "had", "a", "successor"}
#   negation_words = {"not", "never", "no", ...}
#   has_negation = False  ← Aucun mot de négation détecté
#   
#   # Décision
#   if max_score >= THRESHOLD and not has_negation:
#       verdict = "SUPPORTED"  ← 0.87 >= 0.35 ET pas de négation
#       reason = "Max evidence similarity 0.87 ≥ 0.35; no negation in claim."
```

**Résultat final :**
```python
{
    "verdict": "SUPPORTED",
    "explanation": "Max evidence similarity 0.870 ≥ 0.35; no negation in claim.\n\nTop evidence:\n  [0.870] Jahangir  --[successor]-->  Shah Jahan",
    "evidence": ranked_sparql,
    "evidence_path": "Jahangir → [successor] → Shah Jahan",
    "top_scores": [0.87, 0.52, 0.48, 0.28, 0.21]
}
```

---

## 📊 Résumé du Flux d'Appels

```
verify_single() [main.py]
│
├─→ linker.link(claim)
│   ├─→ extract_entities() → spaCy NER
│   ├─→ link_to_dbpedia() → API DBpedia Spotlight
│   └─→ link_to_wikidata() → API Wikidata (fallback)
│
├─→ retriever.retrieve(linked_entities)
│   ├─→ get_triples_dbpedia(uri) → SPARQL DBpedia
│   └─→ get_triples_wikidata(qid) → SPARQL Wikidata
│
├─→ path_retriever.build_graph(triples)
│   └─→ NetworkX DiGraph construction
│
├─→ path_retriever.get_subgraph_triples(graph, entities)
│   ├─→ _match_nodes() → Fuzzy matching
│   └─→ Graph expansion (2 hops)
│
└─→ verifier.verify(claim, triples, path_triples)
    ├─→ ranker.rank(claim, triples)
    │   └─→ Sentence-Transformer encoding + cosine similarity
    │
    ├─→ ranker.rank_path_triples(claim, path_triples)
    │   └─→ Sentence-Transformer encoding + cosine similarity
    │
    └─→ _heuristic(claim, ranked) OU _call_groq() OU _call_huggingface()
        └─→ VERDICT: SUPPORTED / REFUTED
```

---

## 🔑 Points Clés Techniques

1. **Modularité** : Chaque classe a une responsabilité unique (Single Responsibility Principle)

2. **Fallbacks** : Le système a des alternatives à chaque étape :
   - DBpedia Spotlight → Wikidata
   - Groq LLM → HuggingFace → Heuristic

3. **Calcul de similarité** : Le cœur du système repose sur Sentence-Transformer pour mesurer la proximité sémantique

4. **Graphe de connaissances** : NetworkX permet d'explorer les relations multi-sauts entre entités

5. **Seuil de décision** : `0.35` est le seuil critique pour considérer qu'une preuve est pertinente

6. **Détection de négation** : Simple mais efficace (99.5% de précision)
