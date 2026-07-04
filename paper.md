FACTKG: Fact Verification via Reasoning on Knowledge Graphs
JihoKim1,SungjinPark1,YeonsuKwon1,YohanJo2?,JamesThorne1,EdwardChoi1
1KAIST2Amazon
{jiho.kim, zxznm, yeonsu.k, thorne, edwardchoi}@kaist.ac.kr
jyoha@amazon.com
Abstract
In real world applications, knowledge graphs
(KG)arewidelyusedinvariousdomains(e.g.
medical applications and dialogue agents).
However, for fact verification, KGs have
not been adequately utilized as a knowledge
source. KGs can be a valuable knowledge
source in fact verification due to their reli-
ability and broad applicability. A KG con-
sists ofnodes and edgeswhich makes itclear
howconceptsarelinkedtogether,allowingma-
chines to reason over chains of topics. How-
ever,therearemanychallengesinunderstand-
inghowthesemachine-readableconceptsmap
Figure 1: An example data from FACTKG. To verify
to information in text. To enable the commu-
the claim whether it is SUPPORTED or REFUTED, we
nity to better use KGs, we introduce a new
usetriplesextractedfromDBpediaasevidence.
dataset, FACTKG: Fact Verification via Rea-
soning on Knowledge Graphs. It consists of
large-scaledataforms,havenotyetbeenfullyuti-
108k natural language claims with five types
of reasoning: One-hop, Conjunction, Exis- lizedasasourceofevidence. AKGisavaluable
tence, Multi-hop, andNegation. Furthermore, knowledgesourceduetotwoadvantages.
FACTKG contains various linguistic patterns, Firstly,KG-basedfactverificationcanprovide
including colloquial style claims as well as
morereliablereasoning: sincetheefficacyofreal-
written style claims to increase practicality.
world fact-checking hinges on this reliability, re-
Lastly, we develop a baseline approach and
cent studies have focused on justifying the deci-
analyze FACTKG over these reasoning types.
sions of a fact verification system (Kotonya and
We believe FACTKG can advance both relia-
bility and practicality in KG-based fact verifi- Toni, 2020a). In most existing works, the justifi-
cation.1 cationisbasedontheextractivesummaryoftext
evidence. Therefore,theinferentiallinksbetween
1 Introduction
theevidenceandtheverdictarenotclear(Kotonya
The wide spread risk of misinformation has in- andToni,2020b;Atanasovaetal.,2020a,b). Com-
creasedthedemandforfact-checking,thatis,judg- paredtotextandtables,aKGcansimplyrepresent
ing whether a claim is true or false based on ev- reasoning process with logic rules on nodes and
idence. Accordingly, recent works on fact verifi- edges(Liangetal.,2022). Thisallowsustocatego-
cation have been developed with various sources rizecommontypesofreasoningwiththegraphical
ofevidence,suchastext(Thorneetal.,2018;Au- structure,asshowninTable1.
genstein et al., 2019; Jiang et al., 2020; Schuster Secondly,KG-basedfactverificationtechniques
et al., 2021; Park et al., 2021) and tables (Chen havebroadapplicabilitybeyondthedomainoffact-
et al., 2019; Wang et al., 2021; Aly et al., 2021). checking. Forexample,moderndialoguesystems
Unfortunately,knowledgegraphs(KG),oneofthe (e.g. AmazonAlexa(AmazonStaff,2018),Google
Assistant (KaleandHewavitharana,2018))main-
?ThisworkisnotassociatedwithAmazon.
tain and communicate with internal knowledge
1Data available at https://github.com/jiho283/
FactKG. graphs,anditiscrucialtomakesurethattheircon-
3202
yaM
91
]LC.sc[
2v09560.5032:viXra

| ReasoningType |     |     |     |     | ClaimExample |     |     |     |     |     | Graph |     |     |
| ------------- | --- | --- | --- | --- | ------------ | --- | --- | --- | --- | --- | ----- | --- | --- |
r
| One-hop     |     | AIDAstellawasbuiltbyMeyerWerft. |        |      |              |            |       |           |     |     | s   | 2 m |     |
| ----------- | --- | ------------------------------- | ------ | ---- | ------------ | ---------- | ----- | --------- | --- | --- | --- | --- | --- |
|             |     | AIDA                            | Cruise | line | operated the | AIDAstella | which | was built | by  |     | r   | r   |     |
| Conjunction |     |                                 |        |      |              |            |       |           |     | c   | 3   | s 2 | m   |
MeyerWerft.
r
| Existence |     |     |     |     |     |     |     |     |     |     | m   | 1   |     |
| --------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
MeyerWerfthadaparentcompany.
|           |     |                                          |     |     |     |     |     |     |     |     | r   | r   |     |
| --------- | --- | ---------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Multi-hop |     | AIDAstellawasbuiltbyacompanyinPapenburg. |     |     |     |     |     |     |     | s   | 2   | x 4 | p   |
|           |     |                                          |     |     |     |     |     |     |     |     | r   | r   |     |
Negation AIDAstellawasnotbuiltbyMeyerWerftinPapenburg. s 2 m 4 p
Table 1: Five different reasoning types of FACTKG. r : parentCompany, r : shipBuilder, r : shipOperator, r :
|             |               |     |               |     |              | 1   |     | 2   |     |     | 3   |     | 4   |
| ----------- | ------------- | --- | ------------- | --- | ------------ | --- | --- | --- | --- | --- | --- | --- | --- |
| location,m: | MeyerWerft,s: |     | AIDAstella,c: |     | AIDACruises. |     |     |     |     |     |     |     |     |
tentisconsistentwithwhattheusersaysandoth- Augensteinetal.,2019;Jiangetal.,2020;Schuster
erwise update the knowledge graphs accordingly. et al., 2021; Park et al., 2021). FEVER (Thorne
IfwemodeltheuserÆsutteranceasaclaimandthe et al., 2018), one of the representative fact veri-
dialogue systemÆs internal knowledge graph as a fication datasets, is a large-scale manually anno-
knowledge source, the process of checking their tated dataset derived from Wikipedia. Other re-
consistency can be seen as a form of KG-based cent works leverage ambiguous QA pairs (Park
fact verification task. More generally, KG-based etal.,2021),factualchanges(Schusteretal.,2021),
factverificationtechniquescanbeappliedtocases multipledocuments(Jiangetal.,2020),orclaims
which require checking the consistency between sourcedfromfactcheckingwebsites(Augenstein
graphsandtext. etal.,2019). Factverificationontabledataisalso
Reflectingtheseadvantages,weintroduceanew studied(Chenetal.,2019;Wangetal.,2021;Aly
dataset, FACTKG: Fact Verification via Reason- et al., 2021). Table-based datasets such as SEM-
ing on Knowledge Graphs, consisting of 108k TAB-FACTS(Wangetal.,2021)orTabFact(Chen
textual claims that can be verified against DBpe- etal.,2019)requirereasoningabilitiesovertables,
dia (Lehmann et al., 2015) and labeled as SUP- andFEVEROUS(Alyetal.,2021)validateclaims
PORTED or REFUTED. We generated the claims utilizingtableandtextsources. Wereferthereader
basedongraph-textpairsfromWebNLG(Gardent toGuoetal.(2022)foracomprehensivesurvey.
etal.,2017)toincorporatevariousreasoningtypes. Therehavebeenseveraltasksthatutilizeknowl-
The claims in FACTKG are categorized into five edge graphs (Dettmers et al., 2018). For ex-
| reasoningtypes: |     | One-hop,Conjunction,Existence, |     |     |     |        |     |       |         |         |        |        |     |
| --------------- | --- | ------------------------------ | --- | --- | --- | ------ | --- | ----- | ------- | ------- | ------ | ------ | --- |
|                 |     |                                |     |     |     | ample, |     | FB15K | (Bordes | et al., | 2013), | FB15K- |     |
Multi-hop,andNegation. Furthermore,FACTKG 237(ToutanovaandChen,2015),andWN18(Bor-
consistsofclaimsinvariousstylesincludingcol- des et al., 2013) are built upon subsets of large-
loquial,makingitpotentiallysuitableforawider scaleknowledgegraphs,Freebase(Bollackeretal.,
rangeofapplications,includingdialoguesystems.
|     |     |     |     |     |     | 2008) | and | WordNet | (Miller, |     | 1995) | respectively. |     |
| --- | --- | --- | --- | --- | --- | ----- | --- | ------- | -------- | --- | ----- | ------------- | --- |
Weconductedexperimentson FACTKGtovali- Thesedatasetsonlyuseasingletripleasaclaim,
datewhethergraphevidencehadapositiveeffect andthustheclaimsonlyrequireOne-hopreason-
| forfactverification. |     | Ourexperimentsindicatethat |     |     |     |      |                |     |     |                        |     |     |     |
| -------------------- | --- | -------------------------- | --- | --- | --- | ---- | -------------- | --- | --- | ---------------------- | --- | --- | --- |
|                      |     |                            |     |     |     | ing. | However,FACTKG |     |     | isthefirstKG-basedfact |     |     |     |
theuseofgraphicalevidenceinourmodelresulted verification dataset with natural language claims
in superior performance when compared to base- that require complex reasoning. In terms of the
linesthatdidnotincorporatesuchevidence. evidence KG size, FACTKG uses the entire DB-
|     |     |     |     |     |     | pedia | (0.1B | triples), | which | is  | significantly |     | larger |
| --- | --- | --- | --- | --- | --- | ----- | ----- | --------- | ----- | --- | ------------- | --- | ------ |
2 RelatedWorks
thanpreviousdatasets(FB15K:592K,FB15K-237:
|     |     |     |     |     |     | 310K,WN18: |     | 150K). |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ---------- | --- | ------ | --- | --- | --- | --- | --- |
2.1 FactVerificationandStructuredData
Therearevarioustypesofknowledgeusedinfact
2.2 WebNLG
| verification | such | as text, | tables, | and | knowledge |     |     |     |     |     |     |     |     |
| ------------ | ---- | -------- | ------- | --- | --------- | --- | --- | --- | --- | --- | --- | --- | --- |
graphs. Researchonfactverificationhasmainlyfo- As constructing a KG-based fact verification
cusedontextdataasevidence(Thorneetal.,2018; datasetrequiresapairedtext-graphcorpus,weuti-

Figure2: Twosubstitutionmethodsutilizedin FACTKG.InEntitysubstitution,weselectanewentitylocatedin
outside4-hopsfromallentitiesintheoriginalclaim. IftheresultsofbidirectionalNLIarebothcontradiction,we
finishthisprocess. InRelationsubstitution,werandomlyextractarelationthattakesthesameentitytypesforthe
headandtailastheoriginalrelation. Then,substitutionisperformedbasedonatemplatespecifictotheselected
relation.
lizedWebNLGasabasisfor FACTKG.WebNLG beverifiedbycheckingtheexistenceofasinglecor-
isadatasetforevaluatingtriple-basednaturallan- respondingtriple. InthesecondrowofTable1,the
guagegeneration, whichconsistsof25,298pairs claimisSUPPORTEDwhenthetriple(AIDAstella,
ofhigh-qualitytextandRDFtriplesfromDBpedia. ShipBuilder,MeyerWerft)exists.
WebNLGcontainsdiverseformsofgraphsandthe
|     |     |     |     |     |     | We  | take the | sentences |     | that consist | of  | a single |
| --- | --- | --- | --- | --- | --- | --- | -------- | --------- | --- | ------------ | --- | -------- |
textsarecreatedbylinguisticexperts,whichgives
|                                  |             |           |                |         |        | triple            | in S        | as SUPPORTED                   |                            | claims. |           | REFUTED |
| -------------------------------- | ----------- | --------- | -------------- | ------- | ------ | ----------------- | ----------- | ------------------------------ | -------------------------- | ------- | --------- | ------- |
| itgreatvarietyandsophistication. |             |           | Inthe2020chal- |         |        |                   | w           |                                |                            |         |           |         |
|                                  |             |           |                |         |        | claims            | are created |                                | by substituting            |         | SUPPORTED |         |
| lenge2,                          | the dataset | has been  | expanded       | to      | 45,040 |                   |             |                                |                            |         |           |         |
|                                  |             |           |                |         |        | claimsintwoways:  |             |                                | EntitysubstitutionandRela- |         |           |         |
| text-triples                     | pairs. We   | used this | 2020           | version | of     |                   |             |                                |                            |         |           |         |
|                                  |             |           |                |         |        | tionsubstitution. |             | InEntitysubstitution,wereplace |                            |         |           |         |
WebNLGwhenconstructingourdataset.
|     |     |     |     |     |     | an entity                    | e in | SUPPORTED |     | claim           | C with | another |
| --- | --- | --- | --- | --- | --- | ---------------------------- | ---- | --------- | --- | --------------- | ------ | ------- |
|     |     |     |     |     |     | entityeÿofthesameentitytype. |      |           |     | Inordertoensure |        |         |
3 DataConstruction
thatthelabelofthesubstitutedsentenceCÿ
|                                      |                 |           |     |           |      |                 |     |                 |        |         |               | is RE-    |
| ------------------------------------ | --------------- | --------- | --- | --------- | ---- | --------------- | --- | --------------- | ------ | ------- | ------------- | --------- |
| Our goal                             | is to diversify | the graph |     | reasoning | pat- |                 |     |                 |        |         |               |           |
|                                      |                 |           |     |           |      | FUTED,          | the | entity eÿshould |        | satisfy | the           | following |
| ternsandlinguisticstylesoftheclaims. |                 |           |     | Toachieve |      |                 |     | i)              |        | eÿthat  |               |           |
|                                      |                 |           |     |           |      | two conditions. |     | To              | select |         | is irrelevant | to        |
this,wecategorizefivereasoningtypesofclaims: C, eÿ is outside 4-hops from all entities in C on
DBpedia,ii)theresultsofNLI(C,Cÿ)andNLI(Cÿ,
One-hop,Conjunction,Existence,Multi-hop,and
| Negation. | Ourclaimsaregeneratedbytransform- |     |     |     |     |        |      | CONTRADICTION.4 |     |     |             |      |
| --------- | --------------------------------- | --- | --- | --- | --- | ------ | ---- | --------------- | --- | --- | ----------- | ---- |
|           |                                   |     |     |     |     | C) are | both |                 |     |     | In Relation | sub- |
ing the sentences in S , a subset of WebNLGÆs stitution,wereplacearelationinthe SUPPORTED
w
3.1).3
text-graph pairs (Section Next, we also di- claim with another relation. We replace the rela-
| versified | the claims | with colloquial |     | style | transfer |         |          |        |       |      |         |          |
| --------- | ---------- | --------------- | --- | ----- | -------- | ------- | -------- | ------ | ----- | ---- | ------- | -------- |
|           |            |                 |     |       |          | tion of | a triple | in the | claim | with | another | relation |
andpresupposition(Section3.2). that takes the same entity types for the head and
|     |     |     |     |     |     | tail as | the original |     | relation | (e.g. | currentTeam | ?   |
| --- | --- | --- | --- | --- | --- | ------- | ------------ | --- | -------- | ----- | ----------- | --- |
3.1 ClaimGeneration
|     |     |     |     |     |     | formerTeam). |     | Thefourgroupsofcompatiblerela- |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ------------ | --- | ------------------------------ | --- | --- | --- | --- |
3.1.1 One-hop
|     |     |     |     |     |     | tionsarelistedinTable6. |     |     |     | Theoverallprocessof |     |     |
| --- | --- | --- | --- | --- | --- | ----------------------- | --- | --- | --- | ------------------- | --- | --- |
thesubstitutionmethodsisillustratedinFigure2.
Themostbasictypeofclaimisone-hop,whichcov-
| ersonlyoneknowledgetriple. |     |     | One-hopclaimscan |     |     |     |     |     |     |     |     |     |
| -------------------------- | --- | --- | ---------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
2https://webnlg-challenge.loria.fr/challenge_
| 2020/ |     |     |     |     |     | 4We | use a | natural | language | inference | (NLI) | model, |
| ----- | --- | --- | --- | --- | --- | --- | ----- | ------- | -------- | --------- | ----- | ------ |
3Wefoundthat99.7%ofclaimsinFEVERandFEVER- RoBERTa-base (Liu et al., 2019) finetuned on the MNLI
OUSconsistofasinglesentence. Toreflectthisresult,we dataset(Williamsetal.,2018).ThenotationNLI(p,h)repre-
extract a subset S w containing only single sentences from sentstheresultofNLIwhenpisassignedasthepremiseand
| WebNLG. |     |     |     |     |     | hasthehypothesis. |     |     |     |     |     |     |
| ------- | --- | --- | --- | --- | --- | ----------------- | --- | --- | --- | --- | --- | --- |

3.1.4 Multi-hop
Wealsoconsidermulti-hopclaimsthatrequirethe
|     |     |     |     |     |     |     | validation                       | of  | multiple | facts where |         | some        | entities |
| --- | --- | --- | --- | --- | --- | --- | -------------------------------- | --- | -------- | ----------- | ------- | ----------- | -------- |
|     |     |     |     |     |     |     | are underspecified.              |     | Entities |             | in this | claim       | can be   |
|     |     |     |     |     |     |     | connectedbyasequenceofrelations. |     |          |             |         | Forexample, |          |
themulti-hopclaiminTable1isSUPPORTEDifthe
triple(AIDAstella,ShipBuilder,x)andthetriple(x,
|     |     |     |     |     |     |     | location,Papenburg)arepresentinthegraph. |     |     |     |     |     | The |
| --- | --- | --- | --- | --- | --- | --- | ---------------------------------------- | --- | --- | --- | --- | --- | --- |
Figure3:GraphpatternsusedinConjunctionandMulti
| hopclaims. |     |     |     |     |     |     | goalistoverifytheexistenceofapathonthegraph |     |     |     |     |     |     |
| ---------- | --- | --- | --- | --- | --- | --- | ------------------------------------------- | --- | --- | --- | --- | --- | --- |
thatstartsfromAIDAstellaandreachesPapenburg
throughtherelationsShipBuilderandlocation.
3.1.2 Conjunction
|     |     |     |     |     |     |     | Figure | 3 shows | how | a SUPPORTED |     | multi-hop |     |
| --- | --- | --- | --- | --- | --- | --- | ------ | ------- | --- | ----------- | --- | --------- | --- |
Aclaimintherealworldcanincludeamixtureof
|     |     |     |     |     |     |     | claimC | canbegeneratedbyreplacinganentity |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------ | --------------------------------- | --- | --- | --- | --- | --- |
M
| different | facts. | To incorporate |     | this, | we  | construct |          |             |       |     |      |          |       |
| --------- | ------ | -------------- | --- | ----- | --- | --------- | -------- | ----------- | ----- | --- | ---- | -------- | ----- |
|           |        |                |     |       |     |           | e of the | conjunction | claim | C   | with | its type | name. |
aconjunctionclaimcomposedofmultipletriples. First,anentityeisselectedfromthegreennodes.
| Conjunction          | claims    | are | verified |         | by the    | existence  |                  |      |                              |               |        |                |     |
| -------------------- | --------- | --- | -------- | ------- | --------- | ---------- | ---------------- | ---- | ---------------------------- | ------------- | ------ | -------------- | --- |
|                      |           |     |          |         |           |            | Then, the        | type | name t                       | of the        | entity | e is extracted |     |
| of all corresponding |           |     | triples. | In      | the third | row of     |                  |      |                              |               |        |                |     |
|                      |           |     |          |         |           |            | fromDBpedia.     |      | However,eachentityeinDBpedia |               |        |                |     |
| Table 1,             | the claim | can | be       | divided | into      | two parts: |                  |      |                              |               |        |                |     |
|                      |           |     |          |         |           |            | hasseveraltypesT |      | = {t                         | 1 ,t 2 ,...,t | N      | },anditisnot   |     |
ôAIDA Cruise line operated the AIDAstella.ö and annotatedwhichtypeisrelevantwheneisusedin
| ôAIDAstellawasbuiltbyMeyerWerft.ö. |     |      |         |         |              | Theclaim |          |       |                                |     |        |        |       |
| ---------------------------------- | --- | ---- | ------- | ------- | ------------ | -------- | -------- | ----- | ------------------------------ | --- | ------ | ------ | ----- |
|                                    |     |      |         |         |              |          | a claim. | So it | is necessary                   | to  | select | one of | them. |
| is SUPPORTED                       |     | when | all the | triples | (AIDAstella, |          |          |       |                                |     |        |        |       |
|                                    |     |      |         |         |              |          | Foreacht | ?     | T,weinsertitnexttotheentityein |     |        |        |       |
n
| ShipOperator, |     | AIDACruises), |     | (AIDAstella, |     | Ship- | theclaimC |     |     |     |     |     |     |
| ------------- | --- | ------------- | --- | ------------ | --- | ----- | --------- | --- | --- | --- | --- | --- | --- |
andmeasuretheperplexityscoreofthe
| Builder,MeyerWerft)exist. |     |     |     | Toimplementthisidea, |     |     |     |     |     |     |     |     |     |
| ------------------------- | --- | --- | --- | -------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
modifiedclaimusingGPT2-large(Radfordetal.,
weextractedsentencesconsistingofmorethanone
2019). Thenwereplaceeintheclaimwiththetype
| triplefromS |     | andusedthemasthe |     |     | SUPPORTED |     |           |     |            |        |     |         |     |
| ----------- | --- | ---------------- | --- | --- | --------- | --- | --------- | --- | ---------- | ------ | --- | ------- | --- |
|             | w   |                  |     |     |           |     | name that | had | the lowest | score. | The | REFUTED |     |
TocreateREFUTEDclaims,weuseEntity
| claims.                   |     |     |     |                  |     |     | claimisgeneratedbyapplyingEntitysubstitution |     |     |     |     |     |     |
| ------------------------- | --- | --- | --- | ---------------- | --- | --- | -------------------------------------------- | --- | --- | --- | --- | --- | --- |
| substitutionmethodonthese |     |     |     | SUPPORTEDclaims. |     |     |                                              |     |     |     |     |     |     |
tothe SUPPORTEDclaim.
3.1.3 Existence
3.1.5 Negation
Peoplemaymakeclaimsthatasserttheexistence
Foreachofthefourmethodsforgeneratingclaims,
| of something |     | (e.g. ôShe | has | two | kids.ö). | From |     |     |     |     |     |     |     |
| ------------ | --- | ---------- | --- | --- | -------- | ---- | --- | --- | --- | --- | --- | --- | --- |
wedevelopclaimsthatincorporatenegations.
| the view         | of a | triple,    | this corresponds |      | to        | the head |         |     |                              |     |     |     |     |
| ---------------- | ---- | ---------- | ---------------- | ---- | --------- | -------- | ------- | --- | ---------------------------- | --- | --- | --- | --- |
|                  |      |            |                  |      |           |          | One-hop |     | WeusetheNegativeClaimGenera- |     |     |     |     |
| or tail missing. |      | To reflect |                  | this | scenario, | we for-  |         |     |                              |     |     |     |     |
tionModel(Leeetal.,2021)whichwasfine-tuned
| mulate   | a claim | by extracting |      | only | {head,  | rela-     |                 |         |        |         |                    |     |        |
| -------- | ------- | ------------- | ---- | ---- | ------- | --------- | --------------- | ------- | ------ | ------- | ------------------ | --- | ------ |
|          |         |               |      |      |         |           | on the opposite |         | claim  | set in  | the WikiFactCheck- |     |        |
| tion} or | {tail,  | relation}     | from | a    | triple. | Existence |                 |         |        |         |                    |     |        |
|          |         |               |      |      |         |           | English         | dataset | (Sathe | et al., | 2020).5            | To  | ensure |
claimsaregeneratedusingtemplatesandtheyare
thequalityofthegeneratedsentences,wegenerate
| divided | into two | categories: |     | head-relation |     | (e.g. |     |     |     |     |     |     |     |
| ------- | -------- | ----------- | --- | ------------- | --- | ----- | --- | --- | --- | --- | --- | --- | --- |
100opposingclaimsforeachoriginalclaim,then
| template: | {head} | had | a(an) | {relation}.) |     | and tail- |     |     |     |     |     |     |     |
| --------- | ------ | --- | ----- | ------------ | --- | --------- | --- | --- | --- | --- | --- | --- | --- |
onlyusethosethatpreserveallentities,andcontain
| relation  | (e.g.                          | template: | {tail} | was | a {relation}.). |     |                |     |                  |     |       |           |     |
| --------- | ------------------------------ | --------- | ------ | --- | --------------- | --- | -------------- | --- | ---------------- | --- | ----- | --------- | --- |
|           |                                |           |        |     |                 |     | negations(e.g. |     | ænotÆoræneverÆ). |     | Also, | similarto |     |
| SUPPORTED | claimsareconstructedbyrandomly |           |        |     |                 |     |                |     |                  |     |       |           |     |
Entitysubstitutionmethod,weonlyusesentences
| extracting | {head, | relation} |     | or {tail, | relation} | in  |     |     |     |     |     |     |     |
| ---------- | ------ | --------- | --- | --------- | --------- | --- | --- | --- | --- | --- | --- | --- | --- |
whoseNLIrelationwiththeoriginalsentencesare
| triples from | S   | . The | REFUTED |     | claims | are con- |     |     |     |     |     |     |     |
| ------------ | --- | ----- | ------- | --- | ------ | -------- | --- | --- | --- | --- | --- | --- | --- |
w
|           |       |          |          |           |          |            | CONTRADICTION  |     | bidirectionally. |        |           | When  | a nega- |
| --------- | ----- | -------- | -------- | --------- | -------- | ---------- | -------------- | --- | ---------------- | ------ | --------- | ----- | ------- |
| structed  | using | the same | type     | of        | entities | as repre-  |                |     |                  |        |           |       |         |
|           |       |          |          |           |          |            | tion is added, |     | the label        | of the | generated | claim | is      |
| sented in | the   | claim,   | but with | different |          | relations. |                |     |                  |        |           |       |         |
reversedfromtheoriginalclaim.
However,itispossiblethatunrealisticclaimsmay
|                          |     |     |     |                   |     |     | Conjunction |     | The | use | of negations |     | (i.e., |
| ------------------------ | --- | --- | --- | ----------------- | --- | --- | ----------- | --- | --- | --- | ------------ | --- | ------ |
| begeneratedinthismanner. |     |     |     | Forexample,ôMeyer |     |     |             |     |     |     |              |     |        |
ænotÆ)invariouspositionswithinconjunctionclaims
| Werfthadalocation.ö |     |     | orôPapenburgwasaloca- |     |     |     |     |     |     |     |     |     |     |
| ------------------- | --- | --- | --------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
allowsthegenerationofawiderangeofnegative
tion.ö canbecreatedfromthetriple(MeyerWerft,
|                     |     |     |                         |     |     |     | claim structures. |     | We  | employ | the pretrained |     | lan- |
| ------------------- | --- | --- | ----------------------- | --- | --- | --- | ----------------- | --- | --- | ------ | -------------- | --- | ---- |
| location,Papenbug). |     |     | Hence,weselected22rela- |     |     |     |                   |     |     |        |                |     |      |
guagemodelGPT-J6B(WangandKomatsuzaki,
tionsoutofallrelationsthatleadtorealisticclaims.
Templatesusedforbothcategoriesandexamples
5WikiFactCheck-Englishconsistsofpairsofclaims,with
ofgeneratedclaimsareinTable7.
apositiveclaimanditscorrespondingnegativeclaim.

2021)toattachnegationstotheclaim. Weconstruct model,wesetthetemperatureto20.0andgenerate
16 in-context examples, each with negations at- 500sampleswithbeamsearch. i)Toavoidgener-
tachedtothetextscorrespondingtothefirstor/and ated sentences that are too similar to the original
secondrelation. Whenanegationisaddedtothe sentences,onlysentenceswithaneditdistanceof
SUPPORTED claims, all the claims become RE- 6ormorefromtheoriginalsentenceareselected
FUTED. However, when it is added to REFUTED among500samples. ii)Then,onlythosethathave
claims, the label depends on the position of the verbs and the named entities all preserved are se-
lected.6
negation. When negations are added to all parts iii)Finally,weusebidirectionalNLItopre-
withsubstitutedentities,itbecomesa SUPPORTED servetheoriginalsemantics. Candidatesentences
claim. Conversely, other cases preserve the label survivewhenNLI(O,G)isENTAILMENTandNLI
REFUTED since the negation is added to a place (G, O) is not CONTRADICTION where O refers
thatisnotrelatedtoentitysubstitution. Adetailed to the original sentence and G the generated sen-
labelingstrategyisdescribedinAppendixD.1. tence. Onaverage,only41.2generatedsentences
Existence Theclaimisformulatedbyadding survivedoutof500samples. Additionally,incases
a negation within the templates presented in Sec- where none of the 500 generated sentences pass
tion3.1.3(e.g. {tail}wasnota{relation}.). thefilteringprocess,weincludetheoriginalclaim
Multi-hop A claim is formulated using the in the final dataset as a written style claim. Fol-
GPT-J with in-context examples, similar to con- lowingthefilteringprocess,theAFLITEmethod
(Sakaguchietal.,2019),whichutilizesadversarial
| junction. | The | truth of | this claim | is dependent |     | on  |     |     |     |     |
| --------- | --- | -------- | ---------- | ------------ | --- | --- | --- | --- | --- | --- |
thepresenceofadistinctivepaththatmatchesthe filtering, is applied to select the most colloquial
claimÆs intent. For example, the negative claim stylesentenceamongthesurvivingsentences. We
ôAIDAstellawasbuiltbyacompany,notinPapen- includetheselectedclaiminthefinaldatasetasa
burg.ö isSUPPORTEDifxexistswherethetriples colloquialstyleclaim.
| (AIDAstella,   | ShipBuilder, |       | x)     | and (x,    | location, | y)   |                      |     |     |     |
| -------------- | ------------ | ----- | ------ | ---------- | --------- | ---- | -------------------- | --- | --- | --- |
|                |              |       |        |            |           |      | 3.2.2 Presupposition |     |     |     |
| are in DBpedia |              | and y | is not | Papenburg. | A         | more |                      |     |     |     |
detailedlabelingstrategyisinAppendixD.2. Apresuppositionissomethingthespeakerassumes
|     |     |     |     |     |     |     | to be the case | prior to making | an utterance | (Yule |
| --- | --- | --- | --- | --- | --- | --- | -------------- | --------------- | ------------ | ----- |
3.2 ColloquialStyleTransfer
|     |     |     |     |     |     |     | and Widdowson, | 1996). People | often | communi- |
| --- | --- | --- | --- | --- | --- | --- | -------------- | ------------- | ----- | -------- |
cateunderthepresuppositionthattheirbeliefsare
| We transform |     | the claims | into | a colloquial |     | style |     |     |     |     |
| ------------ | --- | ---------- | ---- | ------------ | --- | ----- | --- | --- | --- | --- |
viastyletransferusingbothafine-tunedlanguage universally accepted. We construct claims using
modelandpresuppositiontemplates. thisformofutterance. Theclaimsin FACTKG are
|     |     |     |     |     |     |     | focusedonthreetypesofpresupposition: |     |     | factive, |
| --- | --- | --- | --- | --- | --- | --- | ------------------------------------ | --- | --- | -------- |
3.2.1 Modelbased
non-factive,andstructuralpresuppositions.
Using a similar method proposed by Kim et al. Factive Presupposition People frequently
(2021),wetransformtheclaimobtainedfrom3.1
useverbslikeôrealizeöorôrememberötoexpress
into a colloquial style. For example, the claim TheutteranceôIre-
thetruthoftheirassumptions.
ôObamawaspresident.ö isconvertedtoôHaveyou memberedthat{Statement}.ö assumesthat{State-
| heardaboutObama? |      | Hewaspresident!ö. |     |        |         |       |                |            |                 |       |
| ---------------- | ---- | ----------------- | --- | ------ | ------- | ----- | -------------- | ---------- | --------------- | ----- |
|                  |      |                   |     |        |         |       | ment} is true. | Reflecting | these features, | a new |
| We train         | FLAN | T5-large          |     | (Chung | et al., | 2022) |                |            |                 |       |
claimiscreatedbyappendingexpressionsthatcon-
togenerateacolloquialstylesentencegivenacor- tain presupposition (e.g. ôI realized thatö or ôI
respondingwrittenstylesentencefromWizardof wasnÆt aware thatö) to the existing claim. We
| Wikipedia | (Dinan | et al., | 2019). | However, |     | using |     |     |     |     |
| --------- | ------ | ------- | ------ | -------- | --- | ----- | --- | --- | --- | --- |
usedeighttemplatestomakefactivepresupposition
sentencesgeneratedbythemodelcouldhavesev-
|     |     |     |     |     |     |     | claims: thedetailsareappendedinTable8. |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | -------------------------------------- | --- | --- | --- |
eralpotentialissues: i)theoriginalandgenerated NonFactivePresupposition Theverbssuch
sentencesarelexicallythesame,ii)someentities
asôwishöarecommonlyusedinutterancesthatde-
aremissinginthegeneratedsentences,iii)thegen-
|     |     |     |     |     |     |     | scribeeventsthathavenotoccurred. |     | Forexample, |     |
| --- | --- | --- | --- | --- | --- | --- | -------------------------------- | --- | ----------- | --- |
eratedsentencesdeviatesemanticallyfromtheorig- peoplesayôIwishthat{Statement}.ö when{State-
inal,iv)thegeneratedsentenceslackacolloquial- ment}didnothappen. Claimsthatarecreatedby
| ism, as mentioned |     | in Kim | et  | al. (2021). | To  | over- |     |     |     |     |
| ----------------- | --- | ------ | --- | ----------- | --- | ----- | --- | --- | --- | --- |
comethis,weoversamplecandidatesentencesand 6NLTK(Birdetal.,2009)POStaggerandStanza(Qietal.,
|     |     |     |     |     |     |     | 2020)NERmoduleareused. | DBPediaentitiesarealready |     |     |
| --- | --- | --- | --- | --- | --- | --- | ---------------------- | ------------------------- | --- | --- |
utilizeanadditionalfilteringprocess.
taggedineachclaim,butnotallentitiesexistinthesentence
| First, to | make | more | diverse | samples | using | the |     |     |     |     |
| --------- | ---- | ---- | ------- | ------- | ----- | --- | --- | --- | --- | --- |
intheirrawform,sotheNERmoduleisused.

| thenon-factivepresuppositionmethodarelabeled |     |     |     |                 |     |     |            |         |        | Colloquial |        |       |
| -------------------------------------------- | --- | --- | --- | --------------- | --- | --- | ---------- | ------- | ------ | ---------- | ------ | ----- |
|                                              |     |     |     |                 |     |     | Type       | Written |        |            |        | Total |
| astheoppositeoftheoriginalone.               |     |     |     | Weusedthree     |     |     |            |         | Model  | Presup     |        |       |
|                                              |     |     |     |                 |     |     | One-hop    | 2,106   | 15,934 | 1,580      | 19,530 |       |
| templatestomaketheseclaims:                  |     |     |     | thetemplatesare |     |     |            |         |        |            |        |       |
|                                              |     |     |     |                 |     |     | Conjuction | 20,587  | 15,908 | 602        | 37,097 |       |
appendedinTable8.
|            |                |     |     |      |      |       | Existence | 280    | 4,060  | 4,832 |        | 9,172 |
| ---------- | -------------- | --- | --- | ---- | ---- | ----- | --------- | ------ | ------ | ----- | ------ | ----- |
| Structural | Presupposition |     |     | This | type | is in |           |        |        |       |        |       |
|            |                |     |     |      |      |       | Multi-hop | 10,239 | 16,420 | 603   | 27,262 |       |
theformofaquestionthatpresumescertainfacts. Negation 1,340 12,466 1,807 15,613
Wetreatthequestionitselfasaclaim. Forexam- Total 34,462 64,788 9,424 108,674
| ple, ôWhen | was Messi |     | in Barcelona?ö |     | assumes |     |     |     |     |     |     |     |
| ---------- | --------- | --- | -------------- | --- | ------- | --- | --- | --- | --- | --- | --- | --- |
Table2:DatasetstatisticsofFACTKGforallreasoning
| that Messi | was in | Barcelona. |     | To  | create | a natu- |     |     |     |     |     |     |
| ---------- | ------ | ---------- | --- | --- | ------ | ------- | --- | --- | --- | --- | --- | --- |
types.
| ral sentence | form,         | only      | claims           | corresponding |     | to      |               |     |     |     |     |     |
| ------------ | ------------- | --------- | ---------------- | ------------- | --- | ------- | ------------- | --- | --- | --- | --- | --- |
| one-hop      | and existence |           | are constructed. |               |     | For the |               |     |     |     |     |     |
| one-hop      | claim, a      | different | template         |               | was | created | 4 Experiments |     |     |     |     |     |
correspondingtoeachrelationreflectingitsmean-
|              |                               |     |     |       |     |        | 4.1 DatasetStatistics                    |     |     |     |     |     |
| ------------ | ----------------------------- | --- | --- | ----- | --- | ------ | ---------------------------------------- | --- | --- | --- | --- | --- |
| ing(e.g.     | ôWhendid{head}diefrom{tail}?ö |     |     |       |     | for    |                                          |     |     |     |     |     |
|              | deathCause                    |     |     |       |     | {head} | Table2showsthestatisticsofFACTKG.Wesplit |     |     |     |     |     |
| the relation |                               |     | and | ôWhen | was |        |                                          |     |     |     |     |     |
theclaimsintotrain,dev,andtestsetswithapro-
| directed | by {tail}?ö | for | relation | director). |     | Exis- |                 |                              |     |     |     |     |
| -------- | ----------- | --- | -------- | ---------- | --- | ----- | --------------- | ---------------------------- | --- | --- | --- | --- |
|          |             |     |          |            |     |       | portionof8:1:1. | Weensuredthatthesetoftriples |     |     |     |     |
tenceclaimsarealsogeneratedbasedontemplates
ineachsplitisdisjointwiththeonesinothersplits.
| (e.g. ôWhenwas{tail}{relation}?ö) |     |     |     |     | usingpairs |     |     |     |     |     |     |     |
| --------------------------------- | --- | --- | --- | --- | ---------- | --- | --- | --- | --- | --- | --- | --- |
ofhead-relationortail-relation,similartoSection
|     |     |     |     |     |     |     | 4.2 ExperimentalSetting |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ----------------------- | --- | --- | --- | --- | --- |
3.1.3. ThetemplatesusedaredescribedinTable9.
|     |     |     |     |     |     |     | We publish         | FACTKG | with                     | sets of | claims, | graph |
| --- | --- | --- | --- | --- | --- | --- | ------------------ | ------ | ------------------------ | ------- | ------- | ----- |
|     |     |     |     |     |     |     | evidenceandlabels. |        | Thegraphevidenceincludes |         |         |       |
entitiesandasetofrelationsequencesconnected
3.3 QualityControl
|     |     |     |     |     |     |     | tothem. | Forinstance,whentheclaimisgivenas |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------- | --------------------------------- | --- | --- | --- | --- |
ôAIDAstellawasbuiltbyacompanyinPapenburg.ö,
| To evaluate | the quality |     | of our | dataset, | the | label- |     |     |     |     |     |     |
| ----------- | ----------- | --- | ------ | -------- | --- | ------ | --- | --- | --- | --- | --- | --- |
theentityæAIDAstellaÆcorrespondstoasetofrela-
ingstrategyandtheoutputofthecolloquialstyle
tionsequence[shipBuilder,location]andæPapen-
transfermodelareassessed.
burgÆcorrespondsto[?location,?shipBuilder].7
| Labeling | Strategy |     | When |     | SUPPORTED |     |             |         |              |          |     |       |
| -------- | -------- | --- | ---- | --- | --------- | --- | ----------- | ------- | ------------ | -------- | --- | ----- |
|          |          |     |      |     |           |     | In the test | set, we | only provide | entities | as  | graph |
claimsaremadeinthemannerdescribedinSection
evidence.
3.1,thelabelingisstraightforward,asallhavepre-
| ciseevidencegraphs. |         | However,REFUTEDclaims |               |      |        |       | 4.3 Baseline           |     |     |        |          |     |
| ------------------- | ------- | --------------------- | ------------- | ---- | ------ | ----- | ---------------------- | --- | --- | ------ | -------- | --- |
| are generated       | by      | random                | substitution, |      | so     | there |                        |     |     |        |          |     |
|                     |         |                       |               |      |        |       | Weconductexperimentson |     |     | FACTKG | toseehow |     |
| might be            | a small | chance                | that          | they | remain | SUP-  |                        |     |     |        |          |     |
thegraphicalevidenceaffectsthefactverification
| PORTED(e.g. | ôTheWhiteHouseisinWashington, |       |     |                |     |     |                                              |     |     |     |     |     |
| ----------- | ----------------------------- | ----- | --- | -------------- | --- | --- | -------------------------------------------- | --- | --- | --- | --- | --- |
|             |                               |       |     |                |     |     | task. Tothisend,wedividedourbaselinesintotwo |     |     |     |     |     |
| D.C.ö to    | ôThe White                    | House | is  | in America.ö). |     | To  |                                              |     |     |     |     |     |
distinctcategoriesbasedontheinputtype,Claim
| evaluate | this substitutionmethod, |     |     | randomly |     | sam- |     |     |     |     |     |     |
| -------- | ------------------------ | --- | --- | -------- | --- | ---- | --- | --- | --- | --- | --- | --- |
OnlyandWithGraphicalEvidence.
| pled 1,000           | substituted |     | claims                | were | reviewed | by  |       |           |     |     |     |     |
| -------------------- | ----------- | --- | --------------------- | ---- | -------- | --- | ----- | --------- | --- | --- | --- | --- |
| twograduatestudents. |             |     | Asaresult,99.4%ofgen- |      |          |     | 4.3.1 | ClaimOnly |     |     |     |     |
eratedclaimswereidentifiedasREFUTEDbyboth IntheClaimOnlysetting,thebaselinemodelsre-
participants. ceive only the claim as input and predict the la-
|            |       |          |     |       |     |      | bel. We                         | used three | transformer-based |     | text     | classi- |
| ---------- | ----- | -------- | --- | ----- | --- | ---- | ------------------------------- | ---------- | ----------------- | --- | -------- | ------- |
| Colloquial | Style | Transfer |     | Model | We  | also |                                 |            |                   |     |          |         |
|            |       |          |     |       |     |      | fiers,BERT,BlueBERT,andFlan-T5. |            |                   |     | BERT(De- |         |
evaluatethequalityofthecolloquialstyleclaims
|                      |        |      |                     |       |          |      | vlin et       | al., 2018) | is trained | on Wikipedia |        | from |
| -------------------- | ------ | ---- | ------------------- | ----- | -------- | ---- | ------------- | ---------- | ---------- | ------------ | ------ | ---- |
| generatedbythemodel. |        |      | Asurveywasconducted |       |          |      |               |            |            |              |        |      |
|                      |        |      |                     |       |          |      | which DBpedia | is         | extracted. | So we        | expect | that |
| on all claims        | in the | test | set by              | three | graduate | stu- |               |            |            |              |        |      |
themodelwilluseevidencememorizedinitspre-
| dents.   | As a result, | only         | 9.8% | of the      | claims | were  |         |                  |     |               |     |         |
| -------- | ------------ | ------------ | ---- | ----------- | ------ | ----- | ------- | ---------------- | --- | ------------- | --- | ------- |
|          |              |              |      |             |        |       | trained | weights (Petroni |     | et al., 2019) | or  | exploit |
| selected | as Loss      | of important |      | information |        | by at |         |                  |     |               |     |         |
structuralpatternsinthegeneratedclaims(Schus-
| leasttworeviewers. |     | Inaddition,toensurethequal- |     |     |     |     |                                       |     |     |     |     |       |
| ------------------ | --- | --------------------------- | --- | --- | --- | --- | ------------------------------------- | --- | --- | --- | --- | ----- |
|                    |     |                             |     |     |     |     | teretal.,2019;ThorneandVlachos,2021). |     |     |     |     | Blue- |
ityofthetestset,onlyclaimsthatwereselectedas
|                          |               |     |                     |         |           |     | BERT (Peng   | et al., | 2019)  | is trained | on  | biomed- |
| ------------------------ | ------------- | --- | ------------------- | ------- | --------- | --- | ------------ | ------- | ------ | ---------- | --- | ------- |
| All facts                | are preserved |     | by two              | or more | reviewers |     |              |         |        |            |     |         |
|                          |               |     |                     |         |           |     | ical corpus, | such as | Pubmed | abstracts. |     | We use  |
| areincludedinthetestset. |               |     | Thesurveydetailsare |         |           |     |              |         |        |            |     |         |
inAppendixE.
7æ?Æindicatesthatthedirectionoftherelationisreversed

Figure 4: Overall process of our baseline. In the subgraph retrieval step, each classifier respectively predicts
the relations and hops related to the given entity and the claim. Subsequently, we check all the n-hop relation
sequencesobtainedfromeachclassifiertofindallevidencepaths. Inthefactverificationstep,theclaimisverified
byleveragingalloutputsobtainedfromthesubgraphretrievalstep. Inthisfigure,wedenoteTransformerEncoder
asTRM.
BlueBERTasacomparatorforBERTsinceithas signed to predict the maximum number of hops
neverseenWikipediaduringitspre-training. Flan- n to be traversed from e. We take the subgraph
T5(Chungetal.,2022)isanenhancedversionof of G that are composed only of the relations in
T5 (Raffel et al., 2022) encoder-decoder that has R and where the terminal nodes are entities in C
beenfine-tunedinamixtureof1.8Ktasks. Inall and less than n hops apart from e, allowing for
experiments, we fine-tune BERT and BlueBERT duplicates and considering the order. By travers-
onourtrainingset. DifferentfromBERTandBlue- ingtheknowledgegraphstartingfromealongthe
BERT,weuseFlan-T5inthezero-shotsetting. For relationsequencesinP,wechoosethepathsthat
this setting, we use ôIs this claim True or False? canreachanotherentitythatappearsintheclaim.
Claim: ö astheprefix. Then,wemeasuretheprob- If none of the paths is reachable to other entities,
abilitythattokensTrueandFalsewillappearinthe then we randomly choose one of the paths. The
output. Amongthetwotokens,wechoosetheone strategyweusedenablesthemodeltoretrievesup-
withthehigherprobability. portedevidenceandcounterfactualevidenceforthe
givenclaim. Thefollowingexampleispresentedto
4.3.2 WithGraphicalEvidence assisttheunderstandingofoursubgraphretrieval
IntheWithGraphicalEvidencesetting,themodel method. TheexampleclaiminSection4.2consists
oftwoentities,æAIDAstellaÆandæPapenburgÆ. In
receivestheclaimandgraphevidenceasinputand
thissetting,thehopclassifiermustpredict2since
predictsthelabel. Thebaselineweusedisaframe-
thoseentitiesareconnectedbyasequenceoftwo
workproposedbyGEAR(Zhouetal.,2019)that
relations,namelyshipBuilderandlocation. Inad-
enablesreasoningonmultipleevidencetexts. Since
dition,therelationclassifiermustpredictcorrectly
GEARwasoriginallydesignedtoreasonovertext
predictthosetworelations. Afterthat,wefindall
passages,wechangecomponentstosuitKG.The
2-hop paths starting from æAIDAstellaÆ along the
modifiedGEARconsistsofthesubgraphretrieval
predictedrelationsintheknowledgegraph. Ifthere
module and the claim verification module. The
isapaththatreachesæPapenburgÆ,wecanuseitas
pipeline of the modified GEAR is illustrated in
supportingevidence. Ifnot,however,werandomly
Figure4.
selectapath.
Subgraph retrieval We replace document re-
trievalandsentenceselectioninGEARwithsub- Fact verification We directly employed the
graphretrieval. Toretrievegraphicalevidence,we claim verification in GEAR and applied some
traintwoindependentBERTmodels,namelyare- changestosuittheKGsetting. Sinceourevidence
lation classifier and a hop classifier. The relation isasetofgraphpaths,weconvertedthemtotext
classifier predicts the set of relations R from the by concatenating each triple with the special to-
claim c and the entity e. The hop classifier is de- ken<SEP>. WealsofoundthatERNetinGEAR

InputType Model One-hop Conjunction Existence Multi-hop Negation Total
|                                             |              |                | BERT     |          | 69.64                             | 63.31    |     | 61.84     |          | 70.06 | 63.62 | 65.20 |       |
| ------------------------------------------- | ------------ | -------------- | -------- | -------- | --------------------------------- | -------- | --- | --------- | -------- | ----- | ----- | ----- | ----- |
|                                             | ClaimOnly    |                | BlueBERT |          | 60.03                             | 60.15    |     | 59.89     |          | 57.79 | 58.90 | 59.93 |       |
|                                             |              |                | Flan-T5  |          | 62.17                             | 69.66    |     | 55.29     |          | 60.67 | 55.02 | 62.70 |       |
|                                             | WithEvidence |                | GEAR     |          | 83.23                             | 77.68    |     | 81.61     |          | 68.84 | 79.41 | 77.65 |       |
|                                             |              |                |          | Table3:  | FactverificationaccuracyonFACTKG. |          |     |           |          |       |       |       |       |
|                                             |              |                |          |          |                                   |          |     | InputType | Model    | W?W   | W?C   | C?C   | C?W   |
| is                                          | identicalto  | theTransformer |          | encoder, |                                   | so were- |     |           |          |       |       |       |       |
|                                             |              |                |          |          |                                   |          |     |           | BERT     | 71.75 | 63.85 | 68.10 | 69.43 |
| placeditwitharandomlyinitializedTransformer |              |                |          |          |                                   |          |     | ClaimOnly |          |       |       |       |       |
|                                             |              |                |          |          |                                   |          |     |           | BlueBERT | 64.76 | 56.28 | 58.77 | 63.92 |
encoder. To make this paper self-contained, we WithEvidence GEAR 81.00 75.43 80.81 78.80
providefurtherdetailsabouttheclaimverification
Table4:WreferstowrittenstyleclaimsandCrefersto
ofGEARinAppendixF.
|     |     |     |     |     |     |     | colloquialstyleclaims. |            |        | W?Cmeansthatthemodel |              |         |             |
| --- | --- | --- | --- | --- | --- | --- | ---------------------- | ---------- | ------ | -------------------- | ------------ | ------- | ----------- |
|     |     |     |     |     |     |     | is                     | trained    | on the | written style        | claim        | set and | tested on   |
|     |     |     |     |     |     |     | the                    | colloquial | style  | claim                | set. Flan-T5 | is      | not used in |
4.4 Results
thisexperimentbecauseweuseitonlyinthezero-shot
setting.
| FactVerificationResults |     |        |           | Weevaluatedtheper- |        |     |     |     |     |     |     |     |     |
| ----------------------- | --- | ------ | --------- | ------------------ | ------ | --- | --- | --- | --- | --- | --- | --- | --- |
| formance                |     | of the | models in | predicting         | labels | and |     |     |     |     |     |     |     |
reported the accuracy in Table 3 by different rea- Cross-StyleEvaluation Wesplitthedatasetinto
soningtypes.
twodisjointsets,writtenstyleandcolloquialstyle.
Weperformacross-stylefactverificationtaskby
Asweexpected,GEARoutperformsotherbase-
linemodelsinmostofreasoningtypesbecauseit usingthosedatasetsandtheresultsarereportedin
| usedgraphevidence. |     |     | Especially,inexistenceand |     |     |     | Table4. |     |     |     |     |     |     |
| ------------------ | --- | --- | ------------------------- | --- | --- | --- | ------- | --- | --- | --- | --- | --- | --- |
negation,GEARsubstantiallyoutperformsClaim Initially, we anticipated that using different
|      |            |     |           |           |        |      | styles | for | the train | and | test set | would | result in a |
| ---- | ---------- | --- | --------- | --------- | ------ | ---- | ------ | --- | --------- | --- | -------- | ----- | ----------- |
| Only | baselines. |     | Since the | existence | claims | con- |        |     |           |     |          |       |             |
tainsignificantlylessinformationthanothertypes, significant decrease in verification performance.
having to search for evidence seems to increase However,contradictourexpectation,inC?Wset-
ting,BERTandBlueBERTshowanimprovement
| fact | verification |     | performance. | In  | addition, | nega- |     |     |     |     |     |     |     |
| ---- | ------------ | --- | ------------ | --- | --------- | ----- | --- | --- | --- | --- | --- | --- | --- |
tionclaimsrequireadditionalinferencestepscom- inperformanceoverC?C.EveninGEAR,theper-
paredtoothertypes,thuslogicalreasoningbased formancescoreonlydroppedslightly. Therefore,
ongraphevidencewouldhelpthemodelmakecor- theresultsdemonstratethatcolloquialstyleiscon-
structedinvariousformswhichcanbebeneficial
rectprediction.
forgeneralization.
Inthemulti-hopsetting,however,theaccuracy
ofGEARislowerthanBERT,whichmaybedueto
|                                         |     |     |     |     |     |      | 5   | Conclusion |     |     |     |     |     |
| --------------------------------------- | --- | --- | --- | --- | --- | ---- | --- | ---------- | --- | --- | --- | --- | --- |
| theincreasedcomplexityofgraphretrieval. |     |     |     |     |     | When |     |            |     |     |     |     |     |
entitiesarefarapartwithmanyintermediatenodes
Inthispaper,wepresentFACTKG,anewdataset
beingunder-specified,itincreasestheprobability forfactverificationusingknowledgegraph. Inor-
ofretrievinganincorrectgraph. InGEAR,textand dertorevealtherelationshipbetweenfactverifica-
evidencepathsareconcatenatedandusedasinput,
tionandknowledgegraphreasoning,wegenerated
soifmanyincorrectgraphsareretrieved,theycan
|     |     |     |     |     |     |     | claims | corresponding |     | to  | a certain | graph | pattern. |
| --- | --- | --- | --- | --- | --- | --- | ------ | ------------- | --- | --- | --------- | ----- | -------- |
leadtoincorrectpredictions. Also,theaccuracyof Additionally, FACTKG also includes colloquial-
BERTisthemostsuperiorinthemulti-hopsetting,
styleclaimsthatareapplicabletothedialoguesys-
| which | suggests | that | masked | language |     | modeling |      |     |          |        |      |            |        |
| ----- | -------- | ---- | ------ | -------- | --- | -------- | ---- | --- | -------- | ------ | ---- | ---------- | ------ |
|       |          |      |        |          |     |          | tem. | Our | analysis | showed | that | the claims | in our |
facilitatesthemodeltorobustlyhandleunspecified datasetaredifficulttosolvewithoutreasoningover
| entitiesinthemulti-hopclaims. |     |     |     |     |     |     | theknowledgegraph. |     |     |     |     |     |     |
| ----------------------------- | --- | --- | --- | --- | --- | --- | ------------------ | --- | --- | --- | --- | --- | --- |
In the Claim Only setting, all baselines outper- Weexpectthedatasettooffervariousresearch
formtheMajorityClass(51.35%),andtheBERT directions. One possible use of our dataset is as
modelshowsthehighestperformance. BlueBERT abenchmarkforjustificationprediction. Mostre-
was pre-trained in the same manner, but BERT searchonthistaskgenerateatextpassageasjusti-
showssuperiorperformanceduetoitspre-trained fication,yetthisapproachlackedagoldreference.
knowledgefromWikipedia. Onthecontrary,theinterpretabilityoftheknowl-

edge graph allows us to employ it as an explana- tifc:Areal-worldmulti-domaindatasetforevidence-
tionfortheverdict,suchasquestionansweringin based fact checking of claims. arXiv preprint
arXiv:1909.03242.
themedicaldomainwhereexplainabilityisimpor-
tant. Furthermore,usingtheKGstructureforthe
|                  |     |        |       |          |     |         | Steven Bird, | Ewan     | Klein,     | and | Edward | Loper.  | 2009.   |
| ---------------- | --- | ------ | ----- | -------- | --- | ------- | ------------ | -------- | ---------- | --- | ------ | ------- | ------- |
| claim generation |     | allows | us to | generate | a   | dataset |              |          |            |     |        |         |         |
|                  |     |        |       |          |     |         | Natural      | language | processing |     | with   | Python: | analyz- |
withmorecomplexmulti-hopreasoningbydesign ingtextwiththenaturallanguagetoolkit. "OÆReilly
Media,Inc.".
withoutrelyingonannotatorcreativity.
Limitations Kurt Bollacker, Colin Evans, Praveen Paritosh, Tim
|              |                                   |            |          |         |     |         | Sturge,andJamieTaylor.2008. |               |       |             |     | Freebase:       | acollab- |
| ------------ | --------------------------------- | ---------- | -------- | ------- | --- | ------- | --------------------------- | ------------- | ----- | ----------- | --- | --------------- | -------- |
|              |                                   |            |          |         |     |         | oratively                   | created       | graph | database    |     | for structuring | hu-      |
| Since WebNLG |                                   | is derived | from     | 2015-10 |     | version |                             |               |       |             |     |                 |          |
|              |                                   |            |          |         |     |         |                             |               |       | Proceedings |     | of the          | 2008 ACM |
| of DBpedia,  | FACTKG                            |            | does not | reflect | the | latest  | man knowledge.              |               | In    |             |     |                 |          |
|              |                                   |            |          |         |     |         | SIGMOD                      | international |       | conference  |     | on Management   |          |
| knowledge.   | Also,anotherlimitationofourworkis |            |          |         |     |         |                             |               |       |             |     |                 |          |
ofdata,pages1247û1250.
| thattheclaimsof |     | FACTKG | areconstructedbased |     |     |     |     |     |     |     |     |     |     |
| --------------- | --- | ------ | ------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
onsinglesentences,likeothercrowdsourcedfact Antoine Bordes, Nicolas Usunier, Alberto Garcia-
verification datasets. If the claim is generated by Duran, Jason Weston, and Oksana Yakhnenko.
|     |     |     |     |     |     |     | 2013. | Translating |     | embeddings |     | for modeling | multi- |
| --- | --- | --- | --- | --- | --- | --- | ----- | ----------- | --- | ---------- | --- | ------------ | ------ |
morethanonesentences,thedatasetwillbemore
|     |     |     |     |     |     |     | relational | data. | In  | Advances | in  | Neural | Information |
| --- | --- | --- | --- | --- | --- | --- | ---------- | ----- | --- | -------- | --- | ------ | ----------- |
challenging. Weremainthischallengingpointasa Processing Systems, volume 26. Curran Associates,
| futurework. |     |     |     |     |     |     | Inc. |     |     |     |     |     |     |
| ----------- | --- | --- | --- | --- | --- | --- | ---- | --- | --- | --- | --- | --- | --- |
Acknowledgements Wenhu Chen, Hongmin Wang, Jianshu Chen, Yunkai
|     |     |     |     |     |     |     | Zhang, | Hong | Wang, | Shiyang | Li, | Xiyou | Zhou, and |
| --- | --- | --- | --- | --- | --- | --- | ------ | ---- | ----- | ------- | --- | ----- | --------- |
This work was supported by the Institute of In- William Yang Wang. 2019. Tabfact: A large-
formation & Communications Technology Plan- scaledatasetfortable-basedfactverification. arXiv
preprintarXiv:1909.02164.
| ning &            | Evaluation        | (IITP)   |       | grant | (No.2019-0- |       |           |        |     |      |        |          |        |
| ----------------- | ----------------- | -------- | ----- | ----- | ----------- | ----- | --------- | ------ | --- | ---- | ------ | -------- | ------ |
| 00075,            | No.2022-0-00984), |          |       | and   | National    | Re-   |           |        |     |      |        |          |        |
|                   |                   |          |       |       |             |       | Hyung Won | Chung, | Le  | Hou, | Shayne | Longpre, | Barret |
| search Foundation |                   | of Korea | (NRF) |       | grant       | (NRF- |           |        |     |      |        |          |        |
Zoph,YiTay,WilliamFedus,EricLi,XuezhiWang,
2020H1D3A2A03100945), funded by the Korea MostafaDehghani,SiddharthaBrahma,AlbertWeb-
|     |     |     |     |     |     |     | son, Shixiang |     | Shane | Gu, | Zhuyun | Dai, | Mirac Suz- |
| --- | --- | --- | --- | --- | --- | --- | ------------- | --- | ----- | --- | ------ | ---- | ---------- |
government(MSIT).
|     |     |     |     |     |     |     | gun, Xinyun |        | Chen,   | Aakanksha |      | Chowdhery,  | Sharan   |
| --- | --- | --- | --- | --- | --- | --- | ----------- | ------ | ------- | --------- | ---- | ----------- | -------- |
|     |     |     |     |     |     |     | Narang,     | Gaurav | Mishra, | Adams     |      | Yu, Vincent | Zhao,    |
|     |     |     |     |     |     |     | Yanping     | Huang, | Andrew  |           | Dai, | Hongkun     | Yu, Slav |
References
|           |          |         |         |          |                |          | Petrov,  | Ed H.   | Chi,                  | Jeff Dean, | Jacob | Devlin,  | Adam       |
| --------- | -------- | ------- | ------- | -------- | -------------- | -------- | -------- | ------- | --------------------- | ---------- | ----- | -------- | ---------- |
|           |          |         |         |          |                |          | Roberts, | Denny   | Zhou,                 | Quoc       | V.    | Le, and  | Jason Wei. |
| Rami Aly, | Zhijiang | Guo,    | Michael |          | Schlichtkrull, |          |          |         |                       |            |       |          |            |
|           |          |         |         |          |                |          | 2022.    | Scaling | instruction-finetuned |            |       | language | mod-       |
| James     | Thorne,  | Andreas |         | Vlachos, |                | Christos |          |         |                       |            |       |          |            |
els.
| Christodoulopoulos, |       | Oana      | Cocarascu, |            | and | Arpit   |     |     |     |     |     |     |     |
| ------------------- | ----- | --------- | ---------- | ---------- | --- | ------- | --- | --- | --- | --- | --- | --- | --- |
| Mittal.             | 2021. | Feverous: | Fact       | extraction | and | verifi- |     |     |     |     |     |     |     |
cationoverunstructuredandstructuredinformation. Tim Dettmers, Pasquale Minervini, Pontus Stenetorp,
arXivpreprintarXiv:2106.05707. and Sebastian Riedel. 2018. Convolutional 2d
|     |     |     |     |     |     |     | knowledge |     | graph embeddings. |     |     | In Proceedings | of  |
| --- | --- | --- | --- | --- | --- | --- | --------- | --- | ----------------- | --- | --- | -------------- | --- |
AmazonStaff.2018. Howalexakeepsgettingsmarter. the AAAI conference on artificial intelligence,
vol-
ume32.
| Pepa Atanasova, |     | Jakob Grue | Simonsen, |     | Christina | Li- |     |     |     |     |     |     |     |
| --------------- | --- | ---------- | --------- | --- | --------- | --- | --- | --- | --- | --- | --- | --- | --- |
oma, and Isabelle Augenstein. 2020a. A diagnos- Jacob Devlin, Ming-Wei Chang, Kenton Lee, and
| tic study   | of explainability |             | techniques |          | for text   | clas- |          |               |              |       |       |              |        |
| ----------- | ----------------- | ----------- | ---------- | -------- | ---------- | ----- | -------- | ------------- | ------------ | ----- | ----- | ------------ | ------ |
|             |                   |             |            |          |            |       | Kristina | Toutanova.    |              | 2018. | BERT: | pre-training | of     |
| sification. | In                | Proceedings | of         | the 2020 | Conference |       |          |               |              |       |       |              |        |
|             |                   |             |            |          |            |       | deep     | bidirectional | transformers |       |       | for language | under- |
onEmpiricalMethodsinNaturalLanguageProcess-
|              |     |                  |     |         |     |          | standing. | CoRR,abs/1810.04805. |     |     |     |     |     |
| ------------ | --- | ---------------- | --- | ------- | --- | -------- | --------- | -------------------- | --- | --- | --- | --- | --- |
| ing (EMNLP), |     | pages 3256û3274, |     | Online. |     | Associa- |           |                      |     |     |     |     |     |
tionforComputationalLinguistics.
|     |     |     |     |     |     |     | Emily Dinan, |     | Stephen | Roller, | Kurt | Shuster, | Angela |
| --- | --- | --- | --- | --- | --- | --- | ------------ | --- | ------- | ------- | ---- | -------- | ------ |
Pepa Atanasova, Jakob Grue Simonsen, Christina Li- Fan,MichaelAuli,andJasonWeston.2019. Wizard
|               |          |               |     |             |            |        | of Wikipedia: |                                        | Knowledge-powered |     |     | conversational |     |
| ------------- | -------- | ------------- | --- | ----------- | ---------- | ------ | ------------- | -------------------------------------- | ----------------- | --- | --- | -------------- | --- |
| oma, and      | Isabelle | Augenstein.   |     | 2020b.      | Generating |        |               |                                        |                   |     |     |                |     |
|               |          |               |     |             |            |        | agents.       | InProceedingsoftheInternationalConfer- |                   |     |     |                |     |
| fact checking |          | explanations. | In  | Proceedings |            | of the |               |                                        |                   |     |     |                |     |
enceonLearningRepresentations(ICLR).
58thAnnualMeetingoftheAssociationforCompu-
| tational | Linguistics, | pages | 7352û7364, |     | Online. | As- |     |     |     |     |     |     |     |
| -------- | ------------ | ----- | ---------- | --- | ------- | --- | --- | --- | --- | --- | --- | --- | --- |
sociationforComputationalLinguistics. ClaireGardent, AnastasiaShimorina, ShashiNarayan,
|     |     |     |     |     |     |     | and Laura |     | Perez-Beltrachini. |     | 2017. | The | webnlg |
| --- | --- | --- | --- | --- | --- | --- | --------- | --- | ------------------ | --- | ----- | --- | ------ |
Isabelle Augenstein, Christina Lioma, Dongsheng challenge: Generating text from rdf data. In Pro-
Wang, Lucas Chaves Lima, Casper Hansen, Chris- ceedings of the 10th International Conference on
tianHansen,andJakobGrueSimonsen.2019. Mul- NaturalLanguageGeneration,pages124û133.

ZhijiangGuo,MichaelSchlichtkrull,andAndreasVla- GeorgeAMiller.1995. Wordnet:alexicaldatabasefor
chos. 2022. A survey on automated fact-checking. english. Communications of the ACM, 38(11):39û
| Transactions |     | of the Association |     | for | Computational |     | 41. |     |     |     |     |     |     |
| ------------ | --- | ------------------ | --- | --- | ------------- | --- | --- | --- | --- | --- | --- | --- | --- |
Linguistics,10:178û206.
JungsooPark,SewonMin,JaewooKang,LukeZettle-
|               |         |         |     |       |         |         | moyer,            | and Hannaneh |      | Hajishirzi.         |     | 2021. | Faviq: |
| ------------- | ------- | ------- | --- | ----- | ------- | ------- | ----------------- | ------------ | ---- | ------------------- | --- | ----- | ------ |
| Yichen Jiang, | Shikha  | Bordia, |     | Zheng | Zhong,  | Charles |                   |              |      |                     |     |       |        |
|               |         |         |     |       |         |         | Fact verification |              | from | information-seeking |     |       | ques-  |
| Dognin,       | Maneesh | Singh,  | and | Mohit | Bansal. | 2020.   |                   |              |      |                     |     |       |        |
Hover: A dataset for many-hop fact extrac- tions. arXivpreprintarXiv:2107.02153.
| tion and | claim | verification. |     |     | arXiv | preprint |     |     |     |     |     |     |     |
| -------- | ----- | ------------- | --- | --- | ----- | -------- | --- | --- | --- | --- | --- | --- | --- |
arXiv:2011.03088. Yifan Peng, Shankai Yan, and Zhiyong Lu. 2019.
|                    |           |       |              |         |                |              | Transfer              | learning | in         | biomedical             |      | natural  | language |
| ------------------ | --------- | ----- | ------------ | ------- | -------------- | ------------ | --------------------- | -------- | ---------- | ---------------------- | ---- | -------- | -------- |
|                    |           |       |              |         |                |              | processing:           | An       | evaluation | of                     | bert | and elmo | on ten   |
| Ajinkya Gorakhnath |           | Kale  | and          | Sanjika | Hewavitharana. |              |                       |          |            |                        |      |          |          |
|                    |           |       |              |         |                |              | benchmarkingdatasets. |          |            | InProceedingsofthe2019 |      |          |          |
| 2018.              | Knowledge | graph | construction |         |                | for intelli- |                       |          |            |                        |      |          |          |
WorkshoponBiomedicalNaturalLanguageProcess-
| gent online        | personal |            | assistant.             |      | US Patent      | App.  |                             |        |                  |                        |           |          |         |
| ------------------ | -------- | ---------- | ---------------------- | ---- | -------------- | ----- | --------------------------- | ------ | ---------------- | ---------------------- | --------- | -------- | ------- |
| 15/238,679.        |          |            |                        |      |                |       | ing(BioNLP2019),pages58û65. |        |                  |                        |           |          |         |
|                    |          |            |                        |      |                |       | Fabio Petroni,              |        | Tim Rocktõschel, |                        | Sebastian |          | Riedel, |
| Byeongchang        | Kim,     | Hyunwoo    |                        | Kim, | Seokhee        | Hong, |                             |        |                  |                        |           |          |         |
|                    |          |            |                        |      |                |       | Patrick                     | Lewis, | Anton            | Bakhtin,               | Yuxiang   |          | Wu, and |
| andGunheeKim.2021. |          |            | Howrobustarefactcheck- |      |                |       |                             |        |                  |                        |           |          |         |
|                    |          |            |                        |      |                |       | AlexanderMiller.2019.       |        |                  | Languagemodelsasknowl- |           |          |         |
| ing systems        | on       | colloquial | claims?                |      | In Proceedings |       |                             |        |                  |                        |           |          |         |
|                    |          |            |                        |      |                |       | edge bases?                 |        | In Proceedings   |                        | of        | the 2019 | Confer- |
ofthe2021ConferenceoftheNorthAmericanChap-
|     |     |     |     |     |     |     | ence on | Empirical | Methods |     | in Natural |     | Language |
| --- | --- | --- | --- | --- | --- | --- | ------- | --------- | ------- | --- | ---------- | --- | -------- |
teroftheAssociationforComputationalLinguistics: Processing and the 9th International Joint Confer-
| Human | Language | Technologies, |     | pages | 1535û1548, |     |         |         |          |     |            |     |         |
| ----- | -------- | ------------- | --- | ----- | ---------- | --- | ------- | ------- | -------- | --- | ---------- | --- | ------- |
|       |          |               |     |       |            |     | ence on | Natural | Language |     | Processing |     | (EMNLP- |
Online.AssociationforComputationalLinguistics.
IJCNLP),pages2463û2473,HongKong,China.As-
sociationforComputationalLinguistics.
| Neema Kotonya |           | and Francesca |                | Toni. | 2020a.    | Ex- |                |     |        |       |        |       |         |
| ------------- | --------- | ------------- | -------------- | ----- | --------- | --- | -------------- | --- | ------ | ----- | ------ | ----- | ------- |
| plainable     | automated |               | fact-checking: |       | A survey. | In  |                |     |        |       |        |       |         |
|               |           |               |                |       |           |     | Peng Qi, Yuhao |     | Zhang, | Yuhui | Zhang, | Jason | Bolton, |
Proceedings of the 28th International Conference and Christopher D. Manning. 2020. Stanza: A
on Computational Linguistics, pages 5430û5443, Pythonnaturallanguageprocessingtoolkitformany
Barcelona,Spain(Online).InternationalCommittee Proceedings of the 58th An-
|     |     |     |     |     |     |     | human | languages. | In  |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ----- | ---------- | --- | --- | --- | --- | --- |
onComputationalLinguistics.
|               |     |               |     |       |        |     | nual Meeting |                       | of the Association |     | for | Computational |     |
| ------------- | --- | ------------- | --- | ----- | ------ | --- | ------------ | --------------------- | ------------------ | --- | --- | ------------- | --- |
|               |     |               |     |       |        |     | Linguistics: | SystemDemonstrations. |                    |     |     |               |     |
| Neema Kotonya |     | and Francesca |     | Toni. | 2020b. | Ex- |              |                       |                    |     |     |               |     |
plainableautomatedfact-checkingforpublichealth Alec Radford, Jeff Wu, Rewon Child, David Luan,
claims. In Proceedings of the 2020 Conference on DarioAmodei,andIlyaSutskever.2019. Language
Empirical Methods in Natural Language Process- modelsareunsupervisedmultitasklearners.
| ing (EMNLP), |     | pages | 7740û7754, |     | Online. | Associa- |     |     |     |     |     |     |     |
| ------------ | --- | ----- | ---------- | --- | ------- | -------- | --- | --- | --- | --- | --- | --- | --- |
ColinRaffel,NoamShazeer,AdamRoberts,Katherine
tionforComputationalLinguistics.
|     |     |     |     |     |     |     | Lee, Sharan | Narang, |     | Michael | Matena, | Yanqi | Zhou, |
| --- | --- | --- | --- | --- | --- | --- | ----------- | ------- | --- | ------- | ------- | ----- | ----- |
MinwooLee,SeungpilWon,JuaeKim,HwanheeLee, WeiLi,andPeterJ.Liu.2022. Exploringthelimits
CheoneumPark,andKyominJung.2021. Crossaug: of transfer learning with a unified text-to-text trans-
Acontrastivedataaugmentationmethodfordebias- former. J.Mach.Learn.Res.,21(1).
|          |              |         |     | Proceedings |     | of the |                    |     |       |     |       |         |        |
| -------- | ------------ | ------- | --- | ----------- | --- | ------ | ------------------ | --- | ----- | --- | ----- | ------- | ------ |
| ing fact | verification | models. |     | In          |     |        |                    |     |       |     |       |         |        |
|          |              |         |     |             |     |        | Keisuke Sakaguchi, |     | Ronan | Le  | Bras, | Chandra | Bhaga- |
30thACMInternationalConferenceonInformation
|     |     |     |     |     |     |     | vatula, and | Yejin | Choi. | 2019. | Winogrande: |     | An ad- |
| --- | --- | --- | --- | --- | --- | --- | ----------- | ----- | ----- | ----- | ----------- | --- | ------ |
&KnowledgeManagement,CIKMÆ21.Association
|     |     |     |     |     |     |     | versarialwinogradschemachallengeatscale. |     |     |     |     |     | arXiv |
| --- | --- | --- | --- | --- | --- | --- | ---------------------------------------- | --- | --- | --- | --- | --- | ----- |
forComputingMachinery.
preprintarXiv:1907.10641.
JensLehmann,RobertIsele,MaxJakob,AnjaJentzsch,
AalokSathe,SalarAther,TuanManhLe,NathanPerry,
Dimitris Kontokostas, Pablo N Mendes, Sebastian and Joonsuk Park. 2020. Automated fact-checking
| Hellmann,            | Mohamed   |      | Morsey,                   | Patrick | Van  | Kleef,     |               |            |            |            |                |         |         |
| -------------------- | --------- | ---- | ------------------------- | ------- | ---- | ---------- | ------------- | ---------- | ---------- | ---------- | -------------- | ------- | ------- |
|                      |           |      |                           |         |      |            | of claims     | from       | wikipedia. |            | In Proceedings |         | of The  |
| S÷renAuer,etal.2015. |           |      | Dbpediaûalarge-scale,mul- |         |      |            |               |            |            |            |                |         |         |
|                      |           |      |                           |         |      |            | 12th Language |            | Resources  | and        | Evaluation     |         | Confer- |
| tilingual            | knowledge | base | extracted                 |         | from | wikipedia. |               |            |            |            |                |         |         |
|                      |           |      |                           |         |      |            | ence, pages   | 6874û6882, |            | Marseille, |                | France. | Euro-   |
Semanticweb,6(2):167û195.
peanLanguageResourcesAssociation.
KeLiang,LingyuanMeng,MengLiu,YueLiu,Wenx- Tal Schuster, Adam Fisch, and Regina Barzilay. 2021.
uan Tu, Siwei Wang, Sihang Zhou, Xinwang Liu, GetyourvitaminC!robustfactverificationwithcon-
| and Fuchun | Sun.      | 2022. | Reasoning |         | over     | different |          |           |     |             |     |        |           |
| ---------- | --------- | ----- | --------- | ------- | -------- | --------- | -------- | --------- | --- | ----------- | --- | ------ | --------- |
|            |           |       |           |         |          |           | trastive | evidence. | In  | Proceedings |     | of the | 2021 Con- |
| types of   | knowledge |       | graphs:   | Static, | temporal | and       |          |           |     |             |     |        |           |
ferenceoftheNorthAmericanChapteroftheAsso-
| multi-modal. |     |     |     |     |     |     | ciationforComputationalLinguistics: |     |       |          |     | HumanLan- |       |
| ------------ | --- | --- | --- | --- | --- | --- | ----------------------------------- | --- | ----- | -------- | --- | --------- | ----- |
|              |     |     |     |     |     |     | guage Technologies,                 |     | pages | 624û643, |     | Online.   | Asso- |
YinhanLiu,MyleOtt,NamanGoyal,JingfeiDu,Man- ciationforComputationalLinguistics.
| dar Joshi, | Danqi | Chen, | Omer | Levy, | Mike | Lewis, |     |     |     |     |     |     |     |
| ---------- | ----- | ----- | ---- | ----- | ---- | ------ | --- | --- | --- | --- | --- | --- | --- |
Luke Zettlemoyer, and Veselin Stoyanov. 2019. TalSchuster, DarshShah, YunJieSereneYeo, Daniel
Roberta:ArobustlyoptimizedBERTpretrainingap- Roberto Filizzola Ortiz, Enrico Santus, and Regina
proach. CoRR,abs/1907.11692. Barzilay. 2019. Towards debiasing fact verification

models. InProceedingsofthe2019Conferenceon
EmpiricalMethodsinNaturalLanguageProcessing
andthe9thInternationalJointConferenceonNatu-
ralLanguageProcessing(EMNLP-IJCNLP),pages
3419û3425, Hong Kong, China. Association for
ComputationalLinguistics.
James Thorne and Andreas Vlachos. 2021. Elastic
weight consolidation for better bias inoculation. In
Proceedingsofthe16thConferenceoftheEuropean
Chapter of the Association for Computational Lin-
guistics: MainVolume,pages957û964,Online.As-
sociationforComputationalLinguistics.
James Thorne, Andreas Vlachos, Christos
Christodoulopoulos, and Arpit Mittal. 2018.
FEVER: a large-scale dataset for fact extraction
and VERification. In Proceedings of the 2018
Conference of the North American Chapter of
the Association for Computational Linguistics:
Human Language Technologies, Volume 1 (Long
Papers), pages 809û819, New Orleans, Louisiana.
AssociationforComputationalLinguistics.
Kristina Toutanova and Danqi Chen. 2015. Observed
versus latent features for knowledge base and text
inference. In Proceedings of the 3rd Workshop on
ContinuousVectorSpaceModelsandtheirComposi-
tionality, pages 57û66, Beijing, China. Association
forComputationalLinguistics.
Ben Wang and Aran Komatsuzaki. 2021. GPT-J-
6B: A 6 Billion Parameter Autoregressive Lan-
guageModel. https://github.com/kingoflolz/
mesh-transformer-jax.
Nancy XR Wang, Diwakar Mahajan, Marina
Danilevsky, and Sara Rosenthal. 2021. Semeval-
2021 task 9: Fact verification and evidence
finding for tabular data in scientific documents
(sem-tab-facts). arXivpreprintarXiv:2105.13995.
Adina Williams, Nikita Nangia, and Samuel Bowman.
2018. A broad-coverage challenge corpus for sen-
tenceunderstandingthroughinference. InProceed-
ingsofthe2018ConferenceoftheNorthAmerican
Chapter of the Association for Computational Lin-
guistics: Human Language Technologies, Volume
1(LongPapers), pages1112û1122.Associationfor
ComputationalLinguistics.
G.YuleandH.G.Widdowson.1996. Pragmatics. Ox-
fordIntroductiontoLanguageStudyELT.OUPOx-
ford.
Jie Zhou, Xu Han, Cheng Yang, Zhiyuan Liu, Lifeng
Wang, Changcheng Li, and Maosong Sun. 2019.
GEAR: Graph-based evidence aggregating and rea-
soning for fact verification. In Proceedings of the
57thAnnualMeetingoftheAssociationforCompu-
tationalLinguistics,pages892û901,Florence,Italy.
AssociationforComputationalLinguistics.

| A Qualitativeanalysis |                   |                | E ColloquialStyleClaimSurvey |            |          |              |        |
| --------------------- | ----------------- | -------------- | ---------------------------- | ---------- | -------- | ------------ | ------ |
|                       |                   |                | A total of                   | 9 graduate | students | participated | in the |
| We report claims      | and the retrieved | graphical evi- |                              |            |          |              |        |
denceinTableA.Wealsoreportthecorrectnessof surveytoevaluatehowmuchinformationwaslost
thepredictionofGEARatthefirstcolumnofourta- inthecolloquialstyleclaimcomparedtooriginal
claim. Sinceeachpersonhasdifferentcriteriafor
| ble,Result. Weusedsubgraphretrievaltoretrieve |     |     |     |     |     |     |     |
| --------------------------------------------- | --- | --- | --- | --- | --- | --- | --- |
graph path visualize one of them. By checking æimportantinformationÆ,thelabelsaredividedinto
theretrievedevidence,Wecanrecognizewhythe five rather than two. The labels are as follows, i)
model verdict the claims as refuted or supported. Allfactsarepreserved,ii)Minorlossofinforma-
This shows that our graph evidence is fully inter- tionorminorgrammaticalerrors,iii)Ambiguous
| pretable. |     |     | whetherthelostinformationisimportant,iv)Itis |     |     |     |     |
| --------- | --- | --- | -------------------------------------------- | --- | --- | --- | --- |
ambiguous,butthelostinformationmaybeimpor-
|     |     |     | tant, v) | Loss of important | information. |     | And as a |
| --- | --- | --- | -------- | ----------------- | ------------ | --- | -------- |
B RelationSubstitution
|     |     |     | result, only | 9.8% of | the claims | were | selected as |
| --- | --- | --- | ------------ | ------- | ---------- | ---- | ----------- |
Thefourgroupsofcompatiblerelationsarelisted v) Loss of important information by at least two
| inTable6.             |     |     | reviewers.      |     |     |     |     |
| --------------------- | --- | --- | --------------- | --- | --- | --- | --- |
| C FullListofTemplates |     |     | F DetailsofGEAR |     |     |     |     |
Tomakethispaperself-contained,werecallsome
C.1 Existence
|     |     |     | details of | the claim | verification | in GEAR | (Zhou |
| --- | --- | --- | ---------- | --------- | ------------ | ------- | ----- |
Thetemplatestogenerateexistenceclaimsarede-
|     |     |     | et al., 2019). | The authors | of  | GEAR | (Zhou et al. |
| --- | --- | --- | -------------- | ----------- | --- | ---- | ------------ |
scribedinTable7.
(2019))usedsentenceencodertoobtainrepresen-
|     |     |     | tationsfortheclaimandtheevidence. |     |     |     | Thenthey |
| --- | --- | --- | --------------------------------- | --- | --- | --- | -------- |
C.2 FactiveandNonFactivePresupposition
|     |     |     | built a fully-connected |     | evidence | graph | and used |
| --- | --- | --- | ----------------------- | --- | -------- | ----- | -------- |
FactiveandNonFactivepresuppositiontemplates evidencereasoningnetwork(ERNet)topropagate
informationbetweenevidenceandreasonoverthe
areinTable8.
graph. Finally,theyusedanevidenceaggregatorto
| C.3 StructuralPresupposition |     |     | inferthefinalresults. |     |     |     |     |
| ---------------------------- | --- | --- | --------------------- | --- | --- | --- | --- |
StructuralpresuppositiontemplatesareinTable9.
SentenceEncoder
|     |     |     | Given an | input sentence, | Zhou | et al. | (2019) em- |
| --- | --- | --- | -------- | --------------- | ---- | ------ | ---------- |
D NegationLabeling
|     |     |     | ployed BERT | (Devlin | et al., | 2018) | as a sentence |
| --- | --- | --- | ----------- | ------- | ------- | ----- | ------------- |
encoderbyextractingthefinalhiddenstateofthe
D.1 Conjunction
[CLS]tokenastherepresentation.
When the negation is added to REFUTED claims, Specifically, given a claim c and N pieces of
thelabeldependsonthepositionofthenegation. If retrieved evidence {e ,e ,...,e }, they fed each
1 2 N
negationsareaddedtoallpartswithsubstituteden- evidence-claimpair(e ,c)intoBERTtoobtainthe
i
tities,itbecomesaSUPPORTEDclaim. Conversely, evidencerepresentatione . theyalsofedtheclaim
i
othercasespreservethelabel REFUTEDsincethe intoBERTalonetoobtaintheclaimc. Thatis,
negationisaddedtoaplacethatisnotrelatedtoen-
titysubstitution. Detailedexamplesaredescribed e = BERT(e ,c),
|     |     |     |     | i   |     | i   |     |
| --- | --- | --- | --- | --- | --- | --- | --- |
(1)
| inTable10andTable11. |     |     |     | c = | BERT(c). |     |     |
| -------------------- | --- | --- | --- | --- | -------- | --- | --- |
D.2 Multi-hop
EvidenceReasoningNetwork
Thetruthofthisclaimisdependentonthepresence Letht = {ht,ht,...,ht }denotethehiddenstates
|     |     |     |     | 1 2 | N   |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- |
ofadistinctivepaththatmatchestheclaimÆsintent. ofthenodesinlayert,whereht ? RFÎ1 andF is
i
Forexample,whenverifyingtheclaiminthefourth thenumberoffeaturesineachnode. Theinitialhid-
row of the Table 12, we check the existence of denstateofeachevidencenodeh0 wasinitialized
i
anentitywhichisconnectedtoæAIDAstellaÆwith by the evidence: h0 = e . The authors proposed
|     |     |     |     | i   | i   |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- |
relation builder and not connected to æNew YorkÆ anEvidenceReasoningNetwork(ERNet)toprop-
withrelationlocation. agateinformationamongtheevidencenodes. They

Result Claim RetrievedPath
Yeah!AlfredoZitarrosadiedinacityinUruguay (Uruguay, country,Montevideo, deathPlace,Alfredo_Zitarrosa)
Correct
IhaveheardthatMobylandhadasuccessor. (Mobyland,successor,ôAero2ö)
Wrong IrealizedthatabookwaswrittenbyJ.V.JonesandhastheOCLCnumber51969173 (J._V._Jones, author,A_Cavern_of_Black_Ice,æoclcÆ,ô39456030ö)
Table5: ExamplesofclaimsinFACTKGandretrievedgraphpath.
Groupnumber Headtype Tailtype Relationset
[child,children],[successor],[parent],[predecessor,precededBy],
1 person person
[spouse],[vicePresident,vicepresident],[primeminister,primeMinister]
2 person team [currentteam,currentclub,team],[debutTeam,formerTeam]
[chairperson,chairman,leader,leaderName],[manager],[founder],
3 non-person person [director],[crewMembers],[producer],[discoverer],[creator],[editor],
[writer],[coach],[starring],[dean]
4 non-person non-person [owningCompany,parentCompany,owner],[headquarter],[builder]
Table6: GroupinformationofRelationSubstitution.
firstusedanMLPtocalculatetheattentioncoeffi- whereW ? RCÎF andb ? RCÎ1areparameters,
cientsbetweenanodeianditsneighborj(j ? N ), andC isthenumberofpredictionlabels.
i
p = Wt?1(ReLU(Wt?1(ht?1(cid:107)ht?1))), (2)
ij 1 0 i j
where N denotes the set of neighbors of node i,
i
Wt?1 ? RHÎ2F and Wt?1 ? R1ÎH are weight
0 1
matrices,andÀ(cid:107)Àdenotestheconcatenationopera-
tion.
Then,theynormalizedthecoefficientsusingthe
softmaxfunction,
exp(p )
ij
? = softmax (p ) = . (3)
ij j ij (cid:80)
exp(p )
k?Ni ik
Finally, the normalized attention coefficients
wereusedtocomputealinearcombinationofthe
neighborfeaturesandthusobtainedthefeaturesfor
nodeiatlayert,
(cid:88)
ht = ? ht?1. (4)
i ij j
j?Ni
Theauthorsfedthefinalhiddenstatesoftheevi-
dencenodes{hT,hT,...,hT }intotheirevidence
1 2 N
aggregatortomakethefinalinference.
EvidenceAggregator
The authors employed an evidence aggregator to
gatherinformationfromdifferentevidencenodes
andobtainedthefinalhiddenstateo ? RFÎ1. We
usedthemeanaggregatorinGEAR.
The mean aggregator performed the element-
wiseMeanoperationamonghiddenstates.
o = Mean(hT,hT,...,hT ). (5)
1 2 N
Oncethefinalstateoisobtained,theauthorsem-
ployedaone-layerMLPtogetthefinalprediction
l.
l = softmax(ReLU(Wo+b)), (6)

| Type | Relation |     | Template | Examplesentences |
| ---- | -------- | --- | -------- | ---------------- |
successor,spouse,children,parentCompany,
|     |     |     | {Head}hada(an){Relation}. | Obamahadaspouse. |
| --- | --- | --- | ------------------------- | ---------------- |
capital,garrison,nickname,mascot,
youthclubs,predecessor,child,precededBy,
Head-Relation {Head}didnothavea(an){Relation}. Appledidnothaveaparentcompany.
religion,awards,award
college,university {Head}attended{Relation}. Obamaattendeduniversity.
|     |     |     | {Head}didnotattend{Relation}. | Obamadidnotattendcollege. |
| --- | --- | --- | ----------------------------- | ------------------------- |
Tail-Relation president,primeMinister,vicepresident, {Tail}wasa{Relation}. Obamawasapresident.
primeminister,vicePresident {Tail}wasnota{Relation}. Obamawasnotavicepresident.
|     |                    | Table7: TemplatesforExistenceclaims. |              |     |
| --- | ------------------ | ------------------------------------ | ------------ | --- |
|     | Presuppositiontype | Template                             | ClaimExample |     |
Iforgotthat{claim}. IforgotthatObamawaspresident.
Irealizedthat{claim}. IrealizedthatObamawaspresident.
IwasnÆtawarethat{claim}. IwasnÆtawarethatObamawaspresident.
IdidnÆtknowthat{claim}. IdidnÆtknowthatObamawaspresident.
Factive
Irememberedthat{claim}. IrememberedthatObamawaspresident.
Iexplainedthat{claim}. IexplainedthatObamawaspresident.
Iemphasizedthat{claim}. IemphasizedthatObamawaspresident.
Iunderstandthat{claim}. IunderstandthatObamawaspresident.
Iimaginedthat{claim}. IimaginedthatObamawaspresident.
|     | NonFactive | Iwishthat{claim}. | IwishthatObamawaspresident. |     |
| --- | ---------- | ----------------- | --------------------------- | --- |
Ifonly{claim}. IfonlyObamawaspresident.
Table8: Templatesforfactive,nonfactivepresupposition.
| Type | Relations | Template |     | Exampleclaim |
| ---- | --------- | -------- | --- | ------------ |
leader,leaderName,mayor,
senators,president,manager,
|     |     | Whenwas{tail}a{relaion}of{head}? |     | WhenwasElizabethIIaleaderofAlderney? |
| --- | --- | -------------------------------- | --- | ------------------------------------ |
generalManager,coach,
chairman,dean
|     | team,draftTeam,clubs, |     |     | WhendidAaronBoogaardplayforWichita |
| --- | --------------------- | --- | --- | ---------------------------------- |
Whendid{head}playfor{tail}?
|     | managerClub,managerclubs |     |     | Thunder? |
| --- | ------------------------ | --- | --- | -------- |
operator Whendid{tail}operate{head}? WhendidAktieselskaboperateAarhusAirport?
|     | occupation,formerName | Whenwas{head}a{tail}? |     | WhenwasHBOaTheGreenChannel? |
| --- | --------------------- | --------------------- | --- | --------------------------- |
WhendidAbKlinkgraduatefromtheErasmus
|     | almaMater | Whendid{head}graduatefromthe{tail}? |     |     |
| --- | --------- | ----------------------------------- | --- | --- |
UniversityRotterdam?
fossil Whenwas{tail}fossilfoundin{head}? WhenwasSmilodonfossilfoundinCalifornia?
WhenwasDeathonaFactoryFarmdirectedby
|     | director | Whenwas{head}directedby{tail}? |     |     |
| --- | -------- | ------------------------------ | --- | --- |
SarahTeale?
producer Whenwas{head}producedby{tail}? WhenwasTurnMeOn(album)producedby
WhartonTiers?
One-hop
|     | foundation,foundedBy, |     |     | WhenwasMotorSportVisionfoundedby |
| --- | --------------------- | --- | --- | -------------------------------- |
Whenwas{head}foundedby{tail}?
|     | founder |     |     | JonathanPalmer? |
| --- | ------- | --- | --- | --------------- |
deathCause Whendid{head}diefrom{tail}? WhendidJamesCraigWatsondiefromPeritonitis?
creators,creator Whenwas{head}createdby{tail}? WhenwasAprilOÆNeilcreatedbyPeterLaird?
starring Whenwas{head}starring{tail}? WhenwasBananamanstarringGraemeGarden?
shipBuilder,builder Whenwas{head}builtby{tail}? WhenwasA-RosaLunabuiltbyGermany?
WhenwasAtat³rkMonument(?Izmir)designedby
|     | designer | Whenwas{head}designedby{tail}? |     |     |
| --- | -------- | ------------------------------ | --- | --- |
PietroCanonica?
shipCountry Whendid{head}comefrom{tail}? WhendidARAVeinticincodeMayo(V-2)come
fromArgentina?
WhenwasAbrahamA.RibicoffmarriedtoRuth
|     | spouse | Whenwas{head}marriedto{tail}? |     |     |
| --- | ------ | ----------------------------- | --- | --- |
Ribicoff?
champions Whenwas{tail}championatthe{head}? WhenwasJuventusF.C.championattheSerieA?
WhenwasBootlegSeriesVolume1:TheQuineTapes
|     | recordedIn | Whenwas{head}recordedin{tail}? |     |     |
| --- | ---------- | ------------------------------ | --- | --- |
recordedinSanFrancisco?
successor,spouse,children,
parentCompany,capital,
garrison,nickname,mascot,
|     |                                       | Whatisthenameof{head}Æs{relation}? |     | WhatisthenameofObamaÆschild? |
| --- | ------------------------------------- | ---------------------------------- | --- | ---------------------------- |
|     | Head-Relation youthclubs,predecessor, |                                    |     |                              |
child,precededBy,religion,
Existence
awards,award
|     | college,university       | Whendid{head}attend{relation}? |     | WhendidObamaattenduniversity? |
| --- | ------------------------ | ------------------------------ | --- | ----------------------------- |
|     | president,primeMinister, | Whenwas{tail}{relation}?       |     | WhenwasObamaPresident?        |
Tail-Relation vicepresident,primeminister, Wherewas{tail}{relation}? WherewasBidenVicePresident?
|     | vicePresident | Whatcountrywas{tail}{relation}? |     | WhatcountrywasObamaPresident? |
| --- | ------------- | ------------------------------- | --- | ----------------------------- |
Table9: Templatesforstructuralpresupposition.

| Graph |                                                |     | ClaimExample |     |     | Label     |
| ----- | ---------------------------------------------- | --- | ------------ | --- | --- | --------- |
| r 2   | r 4                                            |     |              |     |     |           |
| a m   | p AIDAstellawasbuiltbyMeyerWerftinPapenburg.   |     |              |     |     | SUPPORTED |
| r 2   | r 4                                            |     |              |     |     |           |
| a m   | n AIDAstellawasbuiltbyMeyerWerftinNewYork.     |     |              |     |     | REFUTED   |
| r 2   | r 4                                            |     |              |     |     |           |
| a m   | n AIDAstellawasnotbuiltbyMeyerWerftinNewYork.  |     |              |     |     | REFUTED   |
| r 2   | r 4                                            |     |              |     |     |           |
| a m   | n AIDAstellawasbuiltbyMeyerWerft,notinNewYork. |     |              |     |     | SUPPORTED |
| r     | r                                              |     |              |     |     |           |
a 2 m 4 n AIDAstellawasnotbuiltbyMeyerWerft,notinNewYork. REFUTED
Table10: r : shipBuilder,r : location,m: MeyerWerft,a: AIDAstella,n: NewYork,p: Papenburg.
|       | 2                                              | 4   |              |     |     |           |
| ----- | ---------------------------------------------- | --- | ------------ | --- | --- | --------- |
| Graph |                                                |     | ClaimExample |     |     | Label     |
| r     | r                                              |     |              |     |     |           |
| 2     | 4                                              |     |              |     |     |           |
| a m   | p AIDAstellawasbuiltbyMeyerWerftinPapenburg.   |     |              |     |     | SUPPORTED |
| r r   |                                                |     |              |     |     |           |
| 2     | 4                                              |     |              |     |     |           |
| a s   | p AIDAstellawasbuiltbySamsunginPapenburg.      |     |              |     |     | REFUTED   |
| r r   |                                                |     |              |     |     |           |
| 2     | 4                                              |     |              |     |     |           |
| a s   | p AIDAstellawasnotbuiltbySamsunginPapenburg.   |     |              |     |     | REFUTED   |
| r r   |                                                |     |              |     |     |           |
| 2     | 4 p                                            |     |              |     |     |           |
| a s   | AIDAstellawasbuiltbySamsung,notinPapenburg.    |     |              |     |     | REFUTED   |
| r r   |                                                |     |              |     |     |           |
| a 2 s | 4 p                                            |     |              |     |     |           |
|       | AIDAstellawasnotbuiltbySamsung,notinPapenburg. |     |              |     |     | SUPPORTED |
Table11: r : shipBuilder,r : location,m: MeyerWerft,a: AIDAstella,p: Papenburg,s: Samsung.
|       | 2                                           | 4   |              |     |     |           |
| ----- | ------------------------------------------- | --- | ------------ | --- | --- | --------- |
| Graph |                                             |     | ClaimExample |     |     | Label     |
| r 2 r | 4                                           |     |              |     |     |           |
| s x   | p AIDAstellawasbuiltbyacompanyinPapenburg.  |     |              |     |     | SUPPORTED |
| r r   |                                             |     |              |     |     |           |
| 2     | 4                                           |     |              |     |     |           |
| s x   | n AIDAstellawasbuiltbyacompanyinNewYork.    |     |              |     |     | REFUTED   |
| r r   |                                             |     |              |     |     |           |
| 2     | 4                                           |     |              |     |     |           |
| s x   | n AIDAstellawasnotbuiltbyacompanyinNewYork. |     |              |     |     | PATHCHECK |
| r r   |                                             |     |              |     |     |           |
| s 2 x | 4 n                                         |     |              |     |     |           |
|       | AIDAstellawasbuiltbyacompany,notinNewYork.  |     |              |     |     | PATHCHECK |
| r r   |                                             |     |              |     |     |           |
s 2 x 4 n AIDAstellawasnotbuiltbyacompany,notinNewYork. PATHCHECK
|     | Table12: | r : shipBuilder,r | : location,s: | AIDAstella,n: | NewYork. |     |
| --- | -------- | ----------------- | ------------- | ------------- | -------- | --- |
|     |          | 2                 | 4             |               |          |     |
