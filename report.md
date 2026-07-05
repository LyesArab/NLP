# Rapport de Projet : Système de Vérification de Faits (Fact-Checking)

## 1. Introduction

Ce document décrit l'architecture et le fonctionnement d'un système automatisé de vérification de faits. L'objectif principal de ce projet est de déterminer la véracité d'une affirmation donnée (un "claim") en la comparant aux informations stockées dans un graphe de connaissances (Knowledge Graph). Le système analyse l'affirmation, extrait les faits pertinents d'une base de données structurée (comme DBpedia ou Wikidata), puis rend un verdict final : `SUPPORTED` (soutenu) ou `REFUTED` (réfuté), en fournissant les preuves qui justifient sa décision.

## 2. Architecture du Système

Le système est conçu comme un pipeline modulaire où chaque étape traite la sortie de la précédente pour progressivement arriver à une conclusion. Le flux de travail est le suivant :

```mermaid
graph TD
    A[1. Réception de l'Affirmation] --> B[2. Reconnaissance d'Entités Nommées (NER)];
    B --> C[3. Liaison d'Entités (Entity Linking)];
    C --> D[4. Récupération de Faits du Knowledge Graph];
    D --> E[5. Classement des Preuves (Evidence Ranking)];
    E --> F[6. Raisonnement et Vérification];
    F --> G[7. Décision Finale];
```

## 3. Description Détaillée des Étapes

### 3.1. Réception de l'Affirmation
Le processus commence lorsqu'un utilisateur fournit une affirmation en langage naturel.
- **Exemple d'affirmation** : "Jahangir had a successor in place of him."

### 3.2. Reconnaissance d'Entités Nommées (NER)
La première étape consiste à identifier les entités clés (personnes, lieux, organisations, etc.) dans le texte de l'affirmation. Cette tâche est réalisée à l'aide de la bibliothèque **spaCy**, un outil puissant pour le traitement du langage naturel.
- **Fichier clé** : `entity_linking.py` (contient probablement la logique d'extraction)
- **Exemple** : Pour l'affirmation "Jahangir had a successor...", NER identifie "Jahangir" comme une entité de type `PERSON`.

### 3.3. Liaison d'Entités (Entity Linking)
Une fois les entités textuelles extraites, il est crucial de les lier à leurs identifiants uniques dans le graphe de connaissances. Ce processus, appelé "Entity Linking", résout les ambiguïtés (par exemple, distinguer "Apple" l'entreprise de "apple" le fruit). Des services comme **DBpedia Spotlight** ou des API pour **Wikidata** sont utilisés pour trouver l'entité correspondante dans la base de données.
- **Fichier clé** : `entity_linking.py`
- **Exemple** : Le texte "Jahangir" est lié à l'entité `dbr:Jahangir` dans DBpedia.

### 3.4. Récupération de Faits du Knowledge Graph
Avec les entités identifiées, le système interroge le graphe de connaissances pour récupérer les faits qui leur sont associés. Des requêtes **SPARQL** sont envoyées à des points d'accès publics (endpoints) pour extraire des sous-graphes pertinents. Ces sous-graphes contiennent des triplets (sujet, prédicat, objet) qui décrivent les relations de l'entité. La bibliothèque **NetworkX** peut ensuite être utilisée pour représenter et explorer ces chemins de faits.
- **Fichiers clés** : `sparql_retriever.py`, `path_retrieval.py`
- **Exemple** : Pour `dbr:Jahangir`, le système pourrait récupérer des faits comme `(dbr:Jahangir, dbo:successor, dbr:Shah_Jahan)`.

### 3.5. Classement des Preuves (Evidence Ranking)
Souvent, un grand nombre de faits sont récupérés. Pour se concentrer sur les plus pertinents, un modèle de **Sentence Transformer** est utilisé pour calculer la similarité sémantique entre l'affirmation originale et chaque fait (ou chemin de faits) récupéré. Les faits les plus similaires sont considérés comme les preuves les plus probantes.
- **Fichier clé** : `evidence_ranker.py`
- **Exemple** : Le fait `(Jahangir, successor, Shah Jahan)` aura une similarité sémantique très élevée avec l'affirmation "Jahangir had a successor".

### 3.6. Raisonnement et Vérification
Cette étape cruciale consiste à évaluer si les preuves les mieux classées soutiennent ou contredisent l'affirmation. La logique de vérification est la suivante :
1.  **Seuil de similarité** : Si la similarité maximale entre l'affirmation et les preuves est supérieure à un certain seuil (par exemple, 0.35), le système considère que des preuves pertinentes ont été trouvées.
2.  **Détection de négation** : Le système vérifie la présence de mots de négation (comme "no", "not", "never") dans l'affirmation.
3.  **Décision** :
    *   Si des preuves pertinentes sont trouvées ET qu'il n'y a pas de négation, l'affirmation est considérée comme **SUPPORTED**.
    *   Si des preuves pertinentes sont trouvées MAIS qu'une négation est détectée, l'affirmation est considérée comme **REFUTED**.
    *   Si aucune preuve pertinente n'est trouvée (similarité trop faible), le verdict est également **REFUTED**.
- **Fichier clé** : `verifier.py`

### 3.7. Décision Finale
Le système produit le verdict final (`SUPPORTED` ou `REFUTED`) et, pour la transparence, fournit le chemin de preuves qui a conduit à cette décision.
- **Exemple de sortie** :
    - **Verdict** : `SUPPORTED`
    - **Chemin de preuve** : `Jahangir → [successor] → Shah Jahan`

## 4. Résultats et Travaux Futurs

Les tests menés sur un ensemble de 200 affirmations ont montré une performance exceptionnelle, avec une **précision de 99.5%** et un **score F1 de 0.9975**.

L'unique erreur a mis en lumière une faiblesse dans la gestion de la négation. L'affirmation "No but Olaudah Equiano had a child" a été incorrectement classée comme `REFUTED` car le modèle a traité "No" comme une négation logique plutôt que comme un marqueur conversationnel.

**Travaux Futurs** : Une amélioration future consistera à affiner le module de raisonnement pour mieux distinguer les contextes de négation, permettant ainsi une compréhension plus nuancée du langage naturel.
