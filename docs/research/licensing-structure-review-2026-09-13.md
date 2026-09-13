> **Archived research, not an executed agreement or current policy.** Published
> 13 September 2026 from user-supplied research. The Dutch report is preserved
> below; see the [English assessment and decision](../core-rights-decision-2026-09-13.md).
> Private source repository references, Git history and raw conversations are not
> included. An illustrative account handle was replaced where present. Unresolvable
> ChatGPT citation markers were removed because their source mapping was not supplied;
> this edition does not claim that every original citation or repository observation
> was independently verified. Original repository observations are a historical snapshot.
>
> **Legal correction:** statements below equating the formal requirements for
> assignment and an exclusive licence are outdated. Since 1 January 2026 the
> agreement must be in writing for either; delivery of an assignment still requires
> a deed. See [the amendment, Article I.A](https://zoek.officielebekendmakingen.nl/stb-2025-352.html)
> and [commencement](https://zoek.officielebekendmakingen.nl/stb-2025-392.html).
> The original wording remains for auditability; apply this correction when reading it.
>
> **Decision difference:** the report recommends retained contributor copyright
> with supplemental licensing rights. DAIA instead selects assignment of accepted
> new Core contributions to the qualified foundation as its ownership target.
> That target transfers no existing rights and cannot operate without valid instruments.

# Juridisch robuuste contributor- en dual-licensingstructuur voor DAIA

## Executive conclusie en kernadvies

De beoogde architectuur is **juridisch plausibel en praktisch goed uitvoerbaar**, mits zij op enkele belangrijke punten scherper wordt gemaakt.

Het fundamentele model — contributors behouden hun auteursrecht, DAIA blijft volledig onder AGPL-3.0-or-later beschikbaar en een onafhankelijke Nederlandse stichting krijgt daarnaast voldoende aanvullende rechten om commerciële/proprietary licenties te verstrekken — sluit aan bij gevestigde contributor-agreementmodellen waarbij auteursrecht niet wordt overgedragen maar aanvullende ruime licentierechten worden verleend. Apache, Harmony, Qt, Eclipse en Python gebruiken ieder varianten van zo’n constructie.

Onder Nederlands auteursrecht kan een rechthebbende zijn auteursrecht geheel of gedeeltelijk overdragen en kan hij voor het geheel of een gedeelte van het exploitatierecht een licentie verlenen. Voor overdracht en voor een **exclusieve** licentie gelden schriftelijkheids-/aktevereisten en een restrictieve uitleg van de overgedragen bevoegdheden. Dat is een belangrijke reden om DAIA's supplemental commercial grant in beginsel **niet-exclusief** te maken.

De belangrijkste correctie op de doelarchitectuur is daarom:

> **Maak de stichting de enige officiële commerciële licensor van het samengestelde DAIA-project, maar probeer niet alle contributors exclusief te verbieden hun eigen oorspronkelijke werk elders te exploiteren.**

Een niet-exclusieve grant geeft de Foundation alle benodigde rechten om DAIA commercieel te relicentiëren, maar laat een contributor juridisch eigenaar en vrij om zijn eigen werk zelf te gebruiken. Een absolute bepaling dat alleen de Foundation ooit de contribution mag exploiteren, zou feitelijk richting een exclusieve licentie of andere exclusiviteitsverbintenis gaan en veroorzaakt méér formaliteiten, meer Nederlands auteurscontractenrechtelijk risico en meer weerstand bij contributors. Een organisatorische exclusiviteit — alleen de Foundation mag een **officiële commerciële DAIA-licentie** afgeven — is voor het projectdoel vrijwel altijd genoeg.

De voorgestelde *interim stewardship*-fase kan eveneens worden gerealiseerd, maar **een eenvoudige licentie aan de oprichter plus een belofte dat hij die later zal overdragen is niet robuust genoeg**. Nederlands vermogens- en contractenrecht biedt een beter mechanisme: de contributor verleent nu de supplemental positie aan een geïdentificeerde interimhouder, geeft tegelijk vooraf zijn medewerking/toestemming voor toekomstige **contractsoverneming** door een objectief gedefinieerde stichting, en er wordt bij voorkeur een tweede, directe fallback voor de toekomstige stichting ingebouwd. BW 6:159 regelt contractsoverneming; BW 6:156 maakt vooraf verleende toestemming mogelijk en Nederlandse rechtspraak accepteert dat medewerking vooraf kan worden verleend, waarna de latere overgang door de vereiste handelingen en kennisgeving wordt geëffectueerd.

De grootste juridische risico's zijn niet de AGPL of het dual-licensingconcept zelf. Zij zijn:

| Risico | Beoordeling |
|---|---|
| Onduidelijke provenance van de bestaande, sterk AI-assisted codebase | **Hoogste huidige risico** |
| Interimrecht dat bij overlijden/faillissement van de oprichter in diens persoonlijke juridische sfeer blijft hangen | **Hoog zonder speciale fallback** |
| Een CLA die te algemeen zegt “commercial relicensing” zonder exacte exploitatierechten | **Hoog** |
| Founder die na oprichting parallel contributorcode zou kunnen relicentiëren | **Moet contractueel worden uitgesloten** |
| Automatische beëindiging van commerciële rechten waardoor bestaande klanten hun licentie verliezen | **Commercieel onwenselijk; vermijdbaar** |
| Een “irrevocable” grant zonder afdwingbare open-core covenant | **Governance-risico** |
| Gebruik van een DCO/PR-checkbox alsof dit een proprietary relicensing grant is | **Onvoldoende** |
| Nederlandse auteurscontractenrechtelijke regels rond royalty-free exploitatierechten van natuurlijke personen | **Specifiek advocaatpunt** |
| Veronderstellen dat AI-output of Git-authorship founder-ownership bewijst | **Niet verdedigbaar** |

PR #21 zit inhoudelijk al opvallend dicht bij de juiste richting. De concepttekst erkent bijvoorbeeld zelf dat de interimconstructie nog niet juridisch is uitgevoerd, dat een “custodial” label geen afgescheiden vermogen creëert en dat een simpele verplichting om later over te dragen de overdracht zelf nog niet tot stand brengt. Dat is juridisch de juiste voorzichtigheid.

De PR maakt eveneens terecht duidelijk dat de huidige bijdragevoorwaarden **geen stille aanvullende commerciële relicensing grant** opleveren en dat bijdragen zonder definitieve supplemental agreement voorlopig AGPL-only blijven.  De huidige `LICENSE-STATUS.md` is nog explicieter: contributors behouden hun eigen auteursrecht, bijdragen zijn AGPL-3.0-or-later en de maintainer krijgt daardoor niet automatisch bredere proprietary/commercial relicensingrechten.

**Mijn eindadvies is daarom:** houd het project nu publiek onder AGPL; laat PR #21 voorlopig beleids-/ontwerpdocumentatie blijven; merge geen eerste externe auteursrechtelijk relevante code, tests of substantiële documentatie totdat een advocaat-gevalideerde Interim Contributor Commercial License Agreement operationeel is; daarna kunnen externe contributions veilig worden geaccepteerd zonder op oprichting van de stichting te hoeven wachten.

## Aanbevolen juridische architectuur

### De rechtenketen

De aanbevolen structuur ziet er als volgt uit:

```text
                         PUBLIEKE LICENTIEKETEN

Contributor
    │
    ├── behoudt copyright
    │
    └── DAIA Contribution ── AGPL-3.0-or-later ──► iedereen
                                      │
                                      ├─ commercieel gebruik toegestaan
                                      ├─ intern gebruik toegestaan
                                      ├─ distributie onder AGPL-voorwaarden
                                      └─ §13 bij relevante gewijzigde
                                         netwerksoftware


                       SUPPLEMENTAL LICENTIEKETEN

Contributor
    │
    │  niet-exclusieve supplemental commercial grant
    ▼
Named Interim DAIA Rights Holder
    │
    │  GEEN bevoegdheid om eindklanten commerciële
    │  DAIA-licenties te verstrekken
    │
    │  uitsluitend administratie + verplichte overgang
    │
    │  vooraf geautoriseerde contractsoverneming
    │  + directe fallback voor Qualified Foundation
    ▼
Qualified DAIA Foundation
    │
    ├── enige officiële commercial DAIA licensor
    │
    ├── proprietary/commercial sublicenses aan klanten
    │
    ├── DAIA Core blijft AGPL-3.0-or-later
    │
    ├── projectgebonden inkomsten
    │
    └── overdracht uitsluitend aan Qualified Successor
              │
              ▼
       Qualified Successor
       met dezelfde mission lock
```

Het is verstandig de term **“custodian”** juridisch niet centraal te stellen. Nederlands recht kent hierdoor niet vanzelf een trustachtige, van het privévermogen van de oprichter afgescheiden rechtenboedel. PR #21 signaleert dat probleem zelf terecht.  Gebruik in de overeenkomst bijvoorbeeld:

> **Interim DAIA Supplemental Rights Holder**

of:

> **Interim Contract Holder**

en definieer vervolgens exact wat hij wel en niet mag doen.

### Vergelijking van de interimconstructies

| Constructie | Sterkte | Zwakte | Advies |
|---|---|---|---|
| Licentie aan oprichter + belofte later over te dragen | Eenvoudig | Afhankelijk van latere medewerking; slechte death/refusal/insolvency-resilience | **Niet voldoende** |
| Licentie + vooraf geautoriseerde contractsoverneming | Duidelijke Nederlandse wettelijke basis | Vereist correcte latere overnameakte/kennisgeving en goede kwalificatieprocedure | **Prima primaire laag** |
| Rechtstreekse conditionele grant aan toekomstige stichting | Vermijdt blijvende founderpositie | Future unidentified entity en acceptatie/formaliteiten verdienen specifiek juridisch onderzoek | **Goede fallback, niet enige laag** |
| Derdenbeding voor toekomstige stichting | Stichting kan na acceptatie zelfstandig rechten ontlenen aan beding | Lost niet automatisch alle contractuele verplichtingen/positie op | **Goede extra bescherming** |
| Copyright assignment aan founder | Sterke gecentraliseerde rechten | Tegen contributor-copyright-retention in; te breed en veel founder-risk | **Afwijzen** |
| Licentie + contractsoverneming + directe springing fallback | Redundantie tegen founder failure | Juridisch iets complexer | **Aanbevolen** |

BW 6:253 maakt een derdenbeding mogelijk waarbij een derde na aanvaarding een eigen recht uit de overeenkomst kan krijgen. BW 3:38 laat rechtshandelingen in beginsel bovendien onder een voorwaarde of tijdsbepaling toe. Dat maakt een “springing” fallback conceptueel goed verdedigbaar, al moet de precieze combinatie met auteursrechtelijke licentieformaliteiten en een nog niet bestaande rechtspersoon vóór gebruik door een Nederlandse IE-jurist worden gevalideerd.

Mijn voorkeursformule is daarom **belt-and-suspenders**:

**Primaire route.** Contributor sluit een overeenkomst met de geïdentificeerde interimholder en verleent daarin nu de supplemental grant. Tegelijk verleent hij vooraf en, voor zover rechtens toegestaan, onherroepelijk medewerking aan contractsoverneming door de eerste Qualified DAIA Foundation. De interimholder is contractueel verplicht de overname te effectueren zodra de objectieve voorwaarden zijn vervuld. BW 6:159 en de verwijzing daarin naar de regels van BW 6:156 bieden hiervoor een veel duidelijker basis dan een losse “we zullen later assignen”-belofte.

**Fallback.** Dezelfde overeenkomst bevat een derdenbeding/voorwaardelijke rechtstreekse grant waardoor de Qualified Foundation na ontstaan, kwalificatie en schriftelijke aanvaarding rechtstreeks de supplemental rechten kan verkrijgen wanneer contractsoverneming door overlijden, weigering, faillissement of een ander obstakel niet tijdig wordt voltooid.

**Confirmatie.** Na oprichting tekenen Foundation en interimholder een `Foundation Assumption and Transfer Agreement`; die akte is niet de enige bron van zekerheid, maar legt vast dat kwalificatie heeft plaatsgevonden, alle verplichtingen zijn aanvaard, het register is overgedragen en de founderpositie is beëindigd.

### Failure modes tijdens de interimperiode

**Overlijden.** Contractuele vermogensposities kunnen in beginsel in een nalatenschap terechtkomen; de CLA moet daarom niet afhankelijk zijn van de persoonlijke bereidheid van erfgenamen. De interimholder krijgt al tijdens leven **geen** commerciële exploitatiebevoegdheid voor eigen gebruik. Bij overlijden wordt iedere resterende discretionaire bevoegdheid automatisch geschorst, terwijl alleen uitvoering van de overgang naar de Qualified Foundation overblijft. De directe fallback moet beogen de Foundation buiten medewerking van de nalatenschap om een recht te geven. De precieze erfrechtelijke werking moet door Nederlandse counsel worden bevestigd.

**Handelingsonbekwaamheid/incapaciteit.** Hetzelfde principe: geen persoonlijke commerciële bevoegdheid, automatische suspension en een onafhankelijk mechanisme waarmee de Foundation kwalificeert zonder dat alleen de founder hierover beslist.

**Weigering om over te dragen.** Maak overdracht een concrete opeisbare verbintenis, met een korte uitvoeringstermijn — bijvoorbeeld tien werkdagen nadat objectieve kwalificatie is vastgesteld — en geef Foundation/contributor recht op nakoming en voorlopige voorzieningen. Een onafhankelijke Qualification Verifier moet kunnen vaststellen dat aan de criteria is voldaan.

**Faillissement.** Hier zit de moeilijkste interimkwestie. Een contractueel woord als “custody” maakt de supplemental positie niet vanzelf bankruptcy-remote. De Faillissementswet kent eigen regels voor wederkerige overeenkomsten en de curator; daarom moet niet worden beweerd dat contributorrechten buiten de failliete boedel vallen zolang een gespecialiseerde insolventie-/IE-jurist die conclusie niet heeft onderbouwd.  Het ontwerp reduceert dit risico doordat de interimhouder de grant nooit aan klanten mag exploiteren of verpanden en de toekomstige stichting een direct fallbackrecht krijgt, maar **dit punt verdient expliciete Nederlandse insolventierechtelijke validatie**.

**De stichting wordt nooit opgericht.** Laat de interimpositie niet eeuwig bestaan. Mijn aanbeveling is een **long-stop van circa drie jaar** na de CLA, eventueel éénmalig verlengbaar met expliciete contributorconsent. Als binnen die periode geen Qualified Foundation bestaat:

* vervalt de interim supplemental grant automatisch;
* vervalt uiteraard niets van de AGPL-licentie;
* de contributor houdt zijn copyright;
* voor commerciële clearing zal later opnieuw toestemming moeten worden verkregen.

Dat is beter dan een slapend commercieel recht permanent in het privévermogen van de founder te laten bestaan.

### Wat de interimholder expliciet niet mag

De overeenkomst moet de interimholder verbieden:

1. commercial/proprietary sublicenses voor DAIA aan klanten, zijn eigen onderneming of gelieerde ondernemingen af te geven;
2. de grant te verkopen, verpanden of als zekerheid te geven;
3. hem vrij over te dragen aan een bedrijf of willekeurige rechtspersoon;
4. er persoonlijk licentie-inkomsten uit te trekken;
5. zichzelf tot Qualified Foundation te verklaren via een gecontroleerde commerciële entiteit;
6. de grant breder uit te leggen dan de Contribution Schedule;
7. zijn positie te gebruiken om de AGPL-communityversie in te trekken of te beperken.

De huidige PR #21 neemt een groot deel van deze grenzen al als ontwerpprincipe op.

## Qualified DAIA Foundation, governance en geldstromen

### Exacte kwalificatievoorwaarden

Voor de eerste Foundation zou ik **geen ruim “functionally equivalent nonprofit” criterium als primaire route gebruiken**. Maak een Nederlandse stichting de normale route. Een functioneel gelijkwaardige buitenlandse/non-profitopvolger kan worden toegestaan als `Qualified Successor`, maar alleen wanneer een onafhankelijke Nederlandse jurist schriftelijk bevestigt dat de relevante mission-locks en non-distributionregels materieel gelijkwaardig zijn.

Een Nederlandse stichting is een rechtspersoon zonder leden, met een statutair doel dat met behulp van vermogen wordt verwezenlijkt. De wettelijke stichtingsregeling beperkt uitkeringen aan oprichters en orgaanleden, terwijl het bestuur de stichting bestuurt; het huidige Nederlandse recht bevat bovendien een conflict-of-interestregel waardoor een bestuurder met een direct of indirect persoonlijk tegenstrijdig belang niet aan de betreffende beraadslaging en besluitvorming deelneemt.  Een stichting wordt via een notariële akte opgericht en in het Handelsregister geregistreerd.

De `Qualified DAIA Foundation` moet contractueel minimaal aan de volgende objectief controleerbare voorwaarden voldoen:

| Vereiste | Waar vastleggen | Kwalificatietest |
|---|---|---|
| Nederlandse stichting | Statuten + CLA | Notariële oprichtingsakte en KVK-inschrijving |
| DAIA-missiedoel | Statuten én CLA | Statuten bevatten ontwikkeling, veiligheid, beschikbaarheid en duurzaamheid van DAIA |
| Permanente open Core | Statuten/policy én supplemental agreements | Gedefinieerde officiële DAIA Core blijft AGPL-3.0-or-later |
| Projectgebonden commerciële inkomsten | Statuten + financieel beleid + CLA | Geen private winstuitkering; gelden uitsluitend voor Foundation Purpose |
| Commerciële sublicensing toegestaan | CLA | Foundation mag end-customer/OEM/hosting licenses geven |
| Geen verkoop van verzamelde grants aan gewone onderneming | CLA én statuten | Alleen Qualified Successor |
| Onafhankelijk bestuur | Statuten | Minimaal drie bestuurders; meerderheid onafhankelijk |
| Founder-control begrensd | Statuten | Founder maximaal minderheid; geen casting vote of unilaterale benoemings-/ontslagmacht |
| Conflictregel | Statuten + policy | Geconflicteerde bestuurder onthoudt zich |
| Geen self-approved compensation | Statuten/policy | Founder stemt noch beraadslaagt over eigen beloning |
| Successor lock | Statuten + CLA | Zelfde open-core, nonprofit en governancevoorwaarden |
| Ontbindingsbestemming | Statuten | DAIA-assets naar missiegebonden vergelijkbare non-profit |
| Formele acceptatie van contributorverplichtingen | Foundation resolution | Bestuursbesluit + Assumption Agreement |
| Openbaar bewijs van kwalificatie | Governance-documentatie | Statuten, board composition, policies en qualification statement |

Hierbij zou ik **“independent” daadwerkelijk definiëren**. Bijvoorbeeld: iemand is niet onafhankelijk wanneer hij de founder is, diens partner/nauwe verwant is, een door de founder gecontroleerde onderneming vertegenwoordigt, een commerciële licensee controleert of een materieel financieel belang heeft dat redelijkerwijs zijn oordeel kan beïnvloeden.

Een praktische governance-eis is:

> minimaal drie bestuurders, waarvan op ieder moment een meerderheid Independent Directors is; de founder mag niet alleen een bestuursmeerderheid kunnen benoemen of ontslaan.

De exacte benoemingssystematiek is belangrijker dan alleen “drie mensen”. Drie zetels waarvan de founder de andere twee naar believen kan ontslaan zijn niet werkelijk onafhankelijk.

### Statuten versus contributorcontract

De mission lock hoort **dubbel** te worden vastgelegd.

Statuten moeten in ieder geval de institutionele kant vastleggen: Foundation Purpose, governance, benoeming/ontslag, belangenconflicten, belangrijke besluitvorming, ontbinding, bestemming van het liquidatiesaldo en successorprincipes.

De contributor agreement moet de rechtenkant vastleggen: waarvoor de supplemental grant geldt, welke open-corevoorwaarde eraan zit, naar wie de licentiepositie mag worden overgedragen, wat een Qualified Successor is, welke remedies de contributor heeft en wat bij ontbinding/disqualification met bestaande sublicenties gebeurt.

Dat is belangrijk omdat alleen een mooi statutaire doelomschrijving niet vanzelf iedere contributor een contractuele remedie verschaft wanneer het bestuur later afwijkt.

### Inkomsten, reserves en founder compensation

Een Nederlandse stichting is niet beperkt tot het ontvangen van giften. Zij kan economische activiteiten uitvoeren; winst maken is niet als zodanig verboden, mits de middelen ten dienste van het stichtingsdoel staan en de stichting geen verboden winstuitkeringsvehikel wordt. KVK beschrijft eveneens dat een stichting inkomsten kan genereren en medewerkers kan betalen terwijl het vermogen voor het doel van de stichting wordt ingezet.

Daarmee kan de DAIA Foundation naar mijn oordeel statutair en contractueel ruimte krijgen voor:

* infrastructuur en hosting;
* softwareontwikkeling;
* security reviews en onafhankelijke audits;
* juridisch en financieel advies;
* contributor bounties en grants;
* personeel;
* onafhankelijke contractors;
* een redelijke buffer/reserve voor meerjarige continuïteit;
* een marktconforme maintainer-/ontwikkelaarsvergoeding voor de oprichter.

De essentiële grens is dat vergoeding wordt betaald **voor daadwerkelijk werk of een echte functie**, niet omdat iemand oprichter of rechthebbende was.

De founder kan daarom prima werknemer of opdrachtnemer zijn. Bij iedere beslissing over zijn arbeidsvoorwaarden, facturen, bonus of fee moet hij volledig buiten de beraadslaging en besluitvorming blijven. De Nederlandse wettelijke belangenconflictregel vormt hiervoor al een bodem; DAIA zou er contractueel/statutair een strengere governancebovenlaag op zetten.

Een geschikte regel is bijvoorbeeld:

> Founder-Related Compensation requires approval by a majority of the disinterested Independent Directors, based on documented market comparables. The affected person shall receive the decision but shall not participate in deliberation, recommendation, approval or amendment of that compensation.

Bij grotere bedragen hoort bovendien een periodieke benchmark en notulen waarin aard van het werk, omvang, marktvergelijking en belangenconflict worden vastgelegd.

### Belastingen

De rechtsvorm stichting betekent niet automatisch belastingvrijstelling. De Belastingdienst beoordeelt onder meer of een stichting een onderneming drijft of concurreert met ondernemers; dan kan vennootschapsbelasting spelen. Wanneer zij btw-ondernemer is, kunnen eveneens btw-verplichtingen ontstaan en bij personeel loonheffingen.  Er bestaan specifieke Vpb-vrijstellingsdrempels voor bepaalde stichtingen/verenigingen, maar een Foundation die structureel commerciële softwarelicenties verkoopt moet daar **niet vooraf op vertrouwen**.

ANBI-status is evenmin noodzakelijk voor dit model. Een operationele softwarestichting met commerciële licenties en betaalde ontwikkelaars moet ANBI pas nastreven nadat een fiscalist heeft beoordeeld of doel, feitelijke activiteiten, bestedingen en beloningsbeleid ermee verenigbaar zijn. De ANBI-regels kennen aanvullende beperkingen voor bestuurdersbeloningen.

### Fiscal host

Een fiscal host kan nuttig zijn voor:

**vóór de stichting:** donaties ontvangen, projectkosten betalen, eventueel grants administreren;

**na oprichting:** payment processing, grant administration, boekhoudkundige ondersteuning of het tijdelijk administreren van geoormerkte projectgelden.

Maar drie verschillende juridische rollen moeten consequent gescheiden blijven:

```text
Geld beheren     ≠     contractspartij van softwareklant
                ≠
           IP-rechthebbende/licensor
```

De host moet **geen IP-licensing authority** krijgen doordat in een algemene fiscal-hostovereenkomst toevallig brede agency- of IP-voorwaarden staan.

Voor commerciële DAIA-licenties behoort de licensor uiteindelijk de Qualified DAIA Foundation te zijn. Een payment/fiscal host kan desnoods geld als agent ontvangen, maar het klantcontract moet duidelijk maken wie de softwarelicentie verleent.

Tijdens de interimfase is een fiscal host géén oplossing voor het ontbreken van de Foundation: de interimholder mag volgens dit ontwerp juist geen commerciële customer licenses uit contributorrechten verstrekken.

## Supplemental contributor grant, community guarantee en patenten

### De minimale copyrightgrant

De supplemental grant moet niet abstracter zeggen:

> “You allow commercial licensing.”

Dat laat te veel discussie over het daadwerkelijke bereik van de toestemming.

De Foundation heeft voor een proprietary softwarelicentie minimaal toestemming nodig voor de gebruikelijke auteursrechtelijke exploitatiehandelingen. Apache en Harmony gebruiken om deze reden brede maar concrete opsommingen van onder meer reproduceren, afgeleide werken maken, distribueren en sublicentiëren.

Voor DAIA adviseer ik materieel deze grant:

> **Contributor retains all copyright and other rights not expressly granted. Subject to this Agreement, Contributor grants the Qualified DAIA Foundation a worldwide, non-exclusive, royalty-free license, for the duration of the applicable copyright, to reproduce, use, modify, adapt, prepare derivative works of, combine, compile, distribute, communicate and make available the Covered Contribution, and to sublicense those rights, solely as part of or in connection with DAIA and DAIA-derived software, products and services, including under commercial or proprietary license terms.**

Daar moeten nog enkele precieze beperkingen bij:

**Covered Contribution.** Niet “alles wat contributor ooit maakt”, maar een objectief identificeerbare contribution: PR, commit SHA's, blob hashes of een master CLA waaronder iedere later door dezelfde identiteit ingediende en geregistreerde DAIA contribution valt.

**Worldwide.** Ja.

**Duur.** Voor de duur van de relevante IE-rechten, behoudens de contractueel gedefinieerde termination/remedyrules. Vermijd een ongedefinieerd “forever” als de wettelijke rechten eerder expireren.

**Non-exclusive.** Sterk aanbevolen.

**Royalty-free.** OSS-CLA-praktijk en praktisch nodig voor schaalbaarheid; Apache/Harmony gebruiken royalty-free grants.  Omdat Nederlands auteurscontractenrecht tegenwoordig sterkere regels over exploitatievergoedingen kent, moet een Nederlandse advocaat wel expliciet bevestigen hoe een gratis supplemental grant van een natuurlijke-persoonsauteur voor een projectstichting zich tot die dwingendrechtelijke bepalingen verhoudt. Dat is één van de belangrijkste nog te valideren Nederlandse punten.

**Sublicensable.** Ja, anders kan de Foundation klanten geen zelfstandige proprietary licentie geven.

**Transferable.** Alleen naar een `Qualified Successor`.

**Field limitation.** Alleen DAIA en DAIA-derived producten/diensten. Geen algemeen recht voor de Foundation om een bijdrage buiten de DAIA-context als willekeurige proprietary code te vermarkten.

**Trademarks.** Niet inbegrepen tenzij afzonderlijk geregeld.

**Moral rights.** Geen generieke “waiver of all moral rights”. Nederlands persoonlijkheidsrecht heeft eigen wettelijke grenzen. Hooguit toestemming voor normale technische modificatie/integratie en een nauw geformuleerde non-assertion voor zover rechtens toegestaan; dit moet Nederlandsrechtelijk worden gedraft.

### Waarom non-exclusive voldoende is

Een contributor die copyright behoudt kan bij een non-exclusive license ook zelf dezelfde contribution exploiteren. Dat doet **niet** af aan de mogelijkheid voor de Foundation om een samengestelde DAIA-release proprietary te licentiëren, zolang zij voor elk relevant onderdeel voldoende rechten heeft.

DAIA moet daarom publiek zeggen:

> “The DAIA Foundation is the exclusive official issuer of alternative commercial licenses for official DAIA releases.”

Niet:

> “The Foundation is the only person who can ever license any contributor's code.”

Dat tweede is niet nodig voor het bedrijfsmodel.

Voor de founder zelf kan een aanvullende **contractuele covenant** worden gebruikt dat hij na Foundation Assumption geen concurrerende officiële DAIA-commercial licenses buiten de Foundation om uitgeeft. Daardoor blijft contributorcode buiten zijn persoonlijke licentiebevoegdheid zonder dat iedere contributor zijn volledige economische vrijheid hoeft op te geven.

### Community guarantee

Hier moet een balans worden gevonden tussen twee vormen van zekerheid:

* contributors moeten weten dat hun contribution niet de basis wordt van een gesloten DAIA;
* zakelijke klanten moeten weten dat hun reeds betaalde licentie niet plotseling verdwijnt door een intern governancegeschil.

Daarom adviseer ik **geen absoluut herroepbare grant** en ook geen volledig onvoorwaardelijke “irrevocable no matter what”-grant.

Gebruik dit model:

> de grant is niet opzegbaar naar believen; de bevoegdheid van de Foundation om **nieuwe** commercial licenses te verstrekken kan echter worden beëindigd of geschorst na een gedefinieerde, materiële en niet herstelde schending van de Open-Core Covenant.

De `Open-Core Covenant` moet bepalen dat voor iedere DAIA Core-versie die door de Foundation proprietary wordt aangeboden:

1. dezelfde Covered DAIA Core-source beschikbaar blijft onder AGPL-3.0-or-later;
2. Foundation-owned wijzigingen aan diezelfde Core eveneens AGPL-3.0-or-later worden gepubliceerd;
3. contributor-owned covered changes niet uit de openbare Core worden verwijderd enkel om ze exclusief commercieel te maken;
4. private customer modifications die eigendom van die customer zijn, niet vanzelf aan de community hoeven te worden overgedragen.

AGPL-rechten die al rechtsgeldig zijn verleend, worden door een latere commerciële licentie niet teruggenomen. AGPL bevat zelf termination/reinstatementregels bij schending en beschermt compliant downstream recipients tegen een simpele retroactieve intrekking van hun rechten.

Een werkbare remedie:

```text
Material breach
      │
      ▼
schriftelijke notice
      │
      ▼
60 dagen cure
(korter bij verboden IP transfer)
      │
      ├──── cure ───► grant blijft volledig bruikbaar
      │
      ▼
uncured material breach
      │
      ├── geen nieuwe proprietary sublicenses
      ├── contributor / Qualified Successor kan nakoming vorderen
      ├── overgang naar Qualified Successor mogelijk
      └── bestaande geldige customer sublicenses blijven bestaan
```

Bij opzettelijke verkoop/verpanding aan een niet-gekwalificeerde commerciële onderneming mag onmiddellijke voorlopige rechtsbescherming mogelijk zijn en kan de cure-periode korter zijn.

### Bestaande commerciële klanten

Een customer sublicense die rechtmatig is afgegeven **vóór** een latere termination van Foundation authority moet in beginsel voor de afgesproken duur en scope blijven bestaan, mits de customer zelf zijn contract naleeft.

Anders wordt iedere klant blootgesteld aan governancegeschillen tussen contributor en Foundation, wat commerciële licenties moeilijk financierbaar en verzekerbaar maakt.

Wel moet anti-circumvention worden opgenomen. De Foundation mag bijvoorbeeld niet vlak vóór disqualification één eeuwigdurende, wereldwijde sublicentie aan een bevriende commerciële dochter geven om de successor lock te omzeilen.

### Patenten

AGPLv3 bevat eigen patentregels, maar DAIA's proprietary klantlicentie is een **afzonderlijke licentiegrondslag**. Het is daarom te riskant te veronderstellen dat een patentpermission die iemand als AGPL-gebruiker geniet automatisch in exact dezelfde vorm een customer onder een geheel andere proprietary overeenkomst beschermt.

Apache en Harmony gebruiken om die reden expliciete contributor patent grants, beperkt tot patentclaims die de contributor daadwerkelijk kan licentiëren en die door de contribution of de combinatie daarvan zoals ingediend noodzakelijk worden geraakt.  Qt combineert eveneens copyright- en patentlicentierechten zonder van de contributor een alomvattende patent-noninfringementgarantie te eisen.

Ik zou DAIA daarom een **smalle expliciete patent grant** laten opnemen:

> Contributor grants the Foundation and recipients of authorized DAIA commercial sublicenses a worldwide, non-exclusive, royalty-free patent license under those patent claims that Contributor has the right to license and that are necessarily infringed by the Covered Contribution alone or by its combination with DAIA as submitted.

Niet vragen om:

* assignment van patenten;
* een licentie op het volledige patentportfolio;
* patentonderzoek door vrijwilligers;
* garantie dat geen enkel patent van derden wordt geraakt;
* brede indemnities.

Een defensieve terminationclause voor een licentienemer die patent litigation over DAIA begint is verdedigbaar, maar voor een jong project secundair.

### Contributor ownership, employer en AI

Een goede CLA moet een **authority warranty** bevatten, geen fictie dat iedere GitHub-gebruiker automatisch auteursrechthebbende is.

Bij werknemers is dat extra belangrijk. De Nederlandse Auteurswet kent een werknemersregeling waarbij onder bepaalde omstandigheden de werkgever als maker geldt wanneer het vervaardigen van het betrokken werk tot de werkzaamheden in dienstverband behoort, tenzij anders is overeengekomen.

Daarom:

| Situatie | DAIA-procedure |
|---|---|
| Privépersoon, eigen code | Individual CLA |
| Werknemer, contribution mogelijk onderdeel werk | Werkgeverstoestemming of Corporate CLA |
| Contractor | Onderliggende overeenkomst controleren; juiste rechtsholder tekent |
| Meerdere auteurs | Alle relevante rechtsholders moeten toestemming geven |
| Minderjarige | Bij voorkeur geen commercial-cleared code zonder ouder/voogd; Harmony kent hiervoor een guardian-model.  |
| AI-assisted bijdrage | Disclosure + provider/provenance review, maar geen fictie dat AI zelf contributor is |
| Third-party snippet | Bron/licentie expliciet aangeven en afzonderlijk clearen |
| Dependency | Buiten supplemental grant; eigen upstreamlicentie blijft gelden |

Apache's actuele guidance over generative tooling onderstreept precies dit probleem: een contributoragreement lost niet op of AI-output oorspronkelijk, auteursrechtelijk beschermd of vrij van rechten van derden is, en provider-outputvoorwaarden moeten afzonderlijk worden bekeken.

De contributor zou naar mijn oordeel alleen redelijkerwijs moeten verklaren:

> hij heeft bevoegdheid om de rechten die de CLA noemt te verlenen;

> voor zover hij weet en na redelijke controle bevat de contribution geen niet-gemelde third-party code, vertrouwelijke informatie of rechtenbeperkingen die de gevraagde licensing onmogelijk maken;

> third-party materiaal wordt gemeld met bron en licentie;

> relevante employer/contractor toestemming is verkregen;

> relevante AI-assisted provenance wordt volgens het DAIA-beleid gemeld.

Hij moet **niet** verklaren:

> “alles is uitsluitend door mij persoonlijk geschreven”;

> “AI-output is gegarandeerd auteursrechtelijk beschermd”;

> “geen patent ter wereld wordt geraakt”;

> “ik vrijwaar DAIA voor alle claims”.

Dat laatste zou voor vrijwilligers disproportioneel zijn en contributorparticipatie onnodig riskant maken.

## CLA-acceptatie, private identiteit en rights register

### Wat voldoende bewijs geeft

Omdat DAIA méér wil verkrijgen dan de gewone AGPL-contribution rights, is een gewone PR-submission of `Signed-off-by` niet de juiste basis.

Een DCO-achtige sign-off bewijst in wezen dat iemand stelt bevoegd te zijn om de bijdrage onder de relevante open-sourcevoorwaarden aan te leveren. Dat is iets anders dan het verlenen van een expliciet recht om dezelfde code onder proprietary klantvoorwaarden te sublicentiëren.

Apache laat contributor agreements daadwerkelijk tekenen en houdt identificerende informatie administratief bij; Eclipse ondersteunt expliciete elektronische acceptatie, en Qt gebruikt voor individuele contributors een Gerrit-flow met een duidelijke `I AGREE`-handeling. Python gebruikt eveneens contributor agreements om bredere relicensingmogelijkheden te behouden.

Nederlandse wetgeving erkent elektronische contractsvorm en elektronische handtekeningen wanneer onder meer inhoud, identiteit, authenticiteit en tijdstip voldoende betrouwbaar kunnen worden vastgesteld. Ook onder eIDAS kan een elektronische handtekening niet enkel wegens haar elektronische vorm juridische werking of bewijswaarde worden ontzegd; een gekwalificeerde elektronische handtekening is gelijkgesteld aan een handgeschreven handtekening.

### Aanbevolen GitHub-flow

Een goede DAIA-flow is:

```text
GitHub PR geopend
      │
      ▼
CLA bot zoekt GitHub numeric user ID
      │
      ├── geen geldige CLA ──► private CLA webflow
      │                            │
      │                            ├─ legal identity
      │                            ├─ verified email
      │                            ├─ employer declaration
      │                            ├─ CLA version + complete text
      │                            ├─ explicit "I agree"
      │                            └─ electronic signature evidence
      │
      ▼
Rights backend geeft Clearance ID
      │
      ▼
bot controleert PR/commit coverage
      │
      ▼
provenance / dependency / AI checks
      │
      ▼
"commercial-rights-cleared" status
      │
      ▼
merge toegestaan
```

De juridische identiteit hoeft **niet publiek op GitHub te staan**.

Het publieke profiel kan bijvoorbeeld blijven:

```text
GitHub: [example contributor pseudonym]
CLA status: accepted
CLA version: DAIA-SCGA-1.0
Clearance ID: DAIA-C-0042
Effective date: 2026-...
Covered PRs: #...
```

Privé wordt bewaard:

```text
legal name
contact email
country/jurisdiction
GitHub numeric account ID
signed agreement/version/hash
timestamp + acceptance evidence
employer declaration
employer authorization, if required
```

Daardoor kan iemand publiek onder een pseudoniem bijdragen terwijl DAIA voldoende bewijs heeft wie de contractspartij werkelijk was.

De GitHub-username alleen is onvoldoende omdat die kan wijzigen; gebruik daarnaast het onveranderlijkere GitHub numeric account ID.

### Sterkte van verschillende acceptatiemethoden

| Methode | Voor DAIA |
|---|---|
| Losse PR-checkbox | Te zwak als enige methode |
| `Signed-off-by` / DCO | Nuttig voor provenance, **niet** genoeg voor proprietary relicensing |
| CLA-bot zonder achterliggende overeenkomst | Niet genoeg |
| CLA-bot gekoppeld aan expliciete webacceptatie | **Goed** |
| Getekende PDF/e-sign | **Zeer goed** |
| Advanced/qualified e-sign | Hoogste bewijswaarde, voor vrijwilligers waarschijnlijk overkill |
| PGP-signature | Goed technisch bewijs, maar operationeel zwaarder |

Apache accepteert onder meer digitale signingmethoden zoals PGP en elektronische ondertekening; het praktische OSS-landschap vereist dus niet overal natte inkt.

Voor DAIA zou ik **dedicated web acceptance + duurzame auditlog** kiezen. Voor corporate contributors of substantiële ondernemingsbijdragen kan afzonderlijke Corporate CLA/e-sign worden verlangd.

### Rights register

Het register moet niet alleen personen noemen. De belangrijkste eigenschap is **traceability per release**.

Minimaal:

| Veld | Voorbeeld |
|---|---|
| Component/file | `src/daia/foo.py` |
| Blob/commit | SHA |
| Rightsholder category | founder / contributor / third party / uncertain |
| AGPL status | yes |
| Supplemental commercial status | cleared / not cleared |
| Grant ID | DAIA-C-0042 |
| CLA version | SCGA-1.0 |
| Patent grant | yes/no/n.a. |
| Third-party exclusions | exact dependency/snippet |
| AI provenance flag | reviewed / requires review |
| Commercial release eligibility | yes/no |

Het uiteindelijke commercial-buildproces zou alleen code mogen opnemen waarvan het register `commercial-cleared` of `separately-compatible-third-party` zegt.

## AGPL, dual licensing, founder rights en opvolging

### Wat AGPL nu al toestaat en beschermt

DAIA's huidige `LICENSE-STATUS.md` vermeldt AGPL-3.0-or-later als projectlicentie en zegt dat contributors hun copyright behouden.

AGPL is een vrije-softwarelicentie die commercieel gebruik niet verbiedt. Zij staat onder haar voorwaarden onder meer kopiëren, wijzigen en verspreiden toe; de licentie maakt expliciet mogelijk geld voor kopieën/support te vragen.

Daarom moet DAIA **nooit** marketing gebruiken zoals:

> “Commercial use requires a commercial license.”

Dat zou misleidend zijn.

Juister:

> “DAIA may be used commercially under AGPL-3.0-or-later. A separate commercial license is available as an alternative for organizations that need rights or terms different from the AGPL.”

### Interne toepassing en verschillende deploymentmodellen

GNU's officiële GPL FAQ maakt het belangrijke onderscheid dat gebruik en kopiëren binnen één organisatie in beginsel intern kan zijn, terwijl het verstrekken van kopieën aan een andere organisatie of persoon een distributie/conveyancevraag oproept.

Voor DAIA is de praktische matrix:

| Scenario | Betaalde DAIA-licentie automatisch nodig? | Belangrijkste AGPL-vraag |
|---|---:|---|
| Intern gebruik door één rechtspersoon | **Nee** | Gewoon intern gebruik op zichzelf vereist geen commerciële DAIA-licentie |
| Gebruik door andere concernvennootschap | **Nee, maar overdracht kan AGPL-verplichtingen activeren** | Andere rechtspersoon kan recipient zijn |
| Externe contractor | **Niet automatisch** | Verstrekking aan contractor kan conveyance zijn; feiten/contractstructuur tellen |
| SaaS met ongewijzigde DAIA | **Niet automatisch** | Network interaction moet tegen AGPL §13 worden beoordeeld |
| SaaS met gewijzigde network-interactive DAIA | **Niet automatisch betaald, maar §13 is essentieel** | Modified version moet relevante Corresponding Source aan remotely interacting users aanbieden |
| Binary/softwaredistributie | **Nee, zolang AGPL wordt nageleefd** | Source/licence/conveying obligations |
| OEM/embedded proprietary product | **Vaak commercieel aantrekkelijk om alternatief te licentiëren, maar niet per definitie verplicht** | AGPL-distributie/combinatieanalyse |
| Klant wil geen AGPL-verplichtingen voor DAIA-derivative | **Dan kan alternative commercial license nodig zijn** | Foundation moet voldoende supplemental rights hebben |

AGPL §13 is specifiek geschreven voor gewijzigde versies waarmee gebruikers via een netwerk interacteren. Het is dus onjuist om “SaaS = commercieel abonnement verplicht” als licentiebeleid te hanteren.

### Waarom dual licensing juridisch kan

Dezelfde rechthebbende kan niet-exclusief rechten onder verschillende voorwaarden verstrekken. De eerdere AGPL-grant verdwijnt daardoor niet. Een toekomstige Foundation kan dus:

```text
zelfde Foundation-cleared DAIA Core
              │
       ┌──────┴──────┐
       ▼             ▼
AGPL-3.0-or-later   Commercial DAIA License
community route     alternative proprietary terms
```

maar alleen voor onderdelen waarvoor zij werkelijk de aanvullende rechten heeft.

Daarom is de `rights/provenance register` niet administratieve luxe; hij bepaalt welke release daadwerkelijk dual-licenseable is.

### Founder-to-Foundation instrument

De founder moet **niet** simpelweg verklaren “I own all DAIA code”. Gezien de AI-assisted ontwikkelgeschiedenis zou dat juist een te sterke representation zijn.

Het founderinstrument moet een schedule bevatten met:

```text
Founder-cleared:
    bestanden / commits / blobs
    rechten die founder aantoonbaar bezit

Uncertain / excluded:
    AI-output met onduidelijke menselijke auteursbijdrage
    third-party material
    dependencies
    generated artifacts
    materiaal waarvan provenance nog niet is bevestigd
```

Voor de aantoonbaar founder-owned code adviseer ik hetzelfde basisrecht als contributors:

> een worldwide, non-exclusive, sublicensable supplemental commercial copyright license aan de Qualified Foundation voor DAIA-commercial licensing.

Daarnaast is bij de founder gerechtvaardigd:

> een persoonlijke covenant dat hij na Foundation Assumption geen parallelle **officiële DAIA proprietary licensing operation** begint en contributorrechten die hij interim heeft gehouden niet langer bezit of uitoefent.

Zijn eigen standalone copyright kan hij behouden.

Een echte copyrightoverdracht door founder aan Foundation kan later worden overwogen, maar is niet noodzakelijk. Als die route wordt gekozen gelden voor auteursrechtoverdracht de Nederlandse akte-/schriftelijkheidsregels en moet de omvang uitdrukkelijk worden beschreven.

### Successor en ontbinding

Een geschikt contributorcontract zou materieel bepalen:

> `Qualified Successor` is uitsluitend een rechtspersoon die alle materiële Qualified Foundation Requirements vervult, de Open-Core Covenant en alle contributor obligations schriftelijk aanvaardt en geen gewone for-profit onderneming is.

De Foundation mag:

* klantensublicenties verstrekken;
* administratieve agents/fiscal hosts inschakelen;
* projectcontractors inschakelen;

maar mag de **onderliggende verzamelde contributor grants** niet vrij verkopen, verpanden of overdragen.

Bij ontbinding:

```text
bestaande AGPL grants
        └── blijven bestaan volgens AGPL

bestaande geldige commercial customer sublicenses
        └── blijven bestaan binnen bestaande scope

recht om NIEUWE commercial licenses uit te geven
        └── alleen naar Qualified Successor

Foundation-owned DAIA assets
        └── statutaire bestemming: vergelijkbare
            missiegebonden non-profit

geen Qualified Successor
        └── geen nieuwe sublicensing authority
```

Dit is veel veiliger dan rechten automatisch naar “de verkrijger van de activa” te laten gaan. Anders zou een curator/liquidator of bestuur via asset sale de hele mission lock kunnen uithollen.

## Huidige DAIA-repository, PR #21 en provenance-audit

### Wat de huidige Git-data daadwerkelijk bewijzen

Op basis van de onderzochte huidige repository, de hoofdbranch, het door de connector teruggegeven commitverleden, de PR-data en PR #21 heb ik **geen externe menselijke copyright holder kunnen identificeren**.

Dat is bewust smaller geformuleerd dan:

> “de founder is bewezen de enige copyright owner.”

De beschikbare commitdata laten een vrijwel geheel `joindaia`/`DAIA`-gedreven geschiedenis zien. Bij veel commits staat de auteursnaam `DAIA`, terwijl de GitHub author identity naar het `joindaia`-account verwijst. Daarnaast zijn er expliciete botcommits van Dependabot voor onder meer updates van `actions/setup-python`, `actions/checkout` en `actions/setup-node`.

Maar Gitmetadata bewijst niet wie de creatieve keuzes heeft gemaakt, of de uploader de auteursrechten bezit, of een werkgever rechthebbende is, of materiaal uit externe bronnen afkomstig is.

`AGENTS.md` laat bovendien zien dat agent/delegation tooling structureel onderdeel is van de projectworkflow. Dat ondersteunt de door jou gegeven waarschuwing dat DAIA sterk AI-/agent-assisted is, maar het document is op zichzelf geen auteursrechtelijke provenanceadministratie.

De juridisch correcte huidige conclusie is daarom:

> **Er is in de onderzochte publieke repositorydata geen externe menselijke contributor/rechthebbende geïdentificeerd, maar uit Gitgegevens kan niet positief worden bewezen dat alle bestaande auteursrechtelijk relevante DAIA-code uitsluitend founder-owned is.**

Een juridisch-evidentiële verklaring dat de **volledige** Git-history en ieder ooit bereikbaar Git-object/reflog/ref cryptografisch is geaudit, kan ik op basis van de connectorweergave niet afgeven. De onderstaande provenance review blijft dus noodzakelijk vóór een eerste daadwerkelijke proprietary DAIA-release.

### Welke bestanden moeten worden gereviewd

De huidige tree bevat first-party Python-source, tests, scripts, documentatie, websitecode, build/configuration files en dependency manifests.

Voor commercial clearance zou ik niet alleen `src/` bekijken. De audit moet omvatten:

| Categorie | Review |
|---|---|
| `src/daia/**` | Human contribution, AI assistance, copied snippets, provider provenance |
| tests | Zelfde; tests kunnen zelf auteursrechtelijk relevante code zijn |
| scripts/tools | Zelfde |
| website source en teksten | Code én creatieve tekst/assets |
| documentatie | Overgenomen passages, voorbeelden en diagrams |
| GitHub workflows/config templates | Herkomst van gekopieerde templates/snippets |
| lockfiles | Als generated classificeren; inputs + dependencies vastleggen |
| schemas/snapshots/generated output | Generator en inputlicentie vastleggen |
| fixtures/test certificates/data | Eigen/generate/third-party classificeren |
| eventuele images/fonts/assets | Aparte licentie/provenance |
| dependencies | Niet als DAIA-owned classificeren |

DAIA heeft al een nuttig `docs/dependency-licenses.md` waarin onder meer PyYAML, Redis client, SQLAlchemy en optionele/transitieve packages met hun upstreamlicenties worden bijgehouden. Dat is goed voor compliance, maar zulke dependencies zijn daardoor uiteraard nog niet eigendom van DAIA en worden ook niet door een contributor CLA proprietary relicensed.

De beste operationalisering is een release manifest:

```text
FOUNDATION-OWNED
FOUNDER-SUPPLEMENTAL-CLEARED
CONTRIBUTOR-SUPPLEMENTAL-CLEARED
THIRD-PARTY-SEPARATELY-LICENSED
AGPL-ONLY
GENERATED
PROVENANCE-UNKNOWN
```

Een commerciële build mag geen `AGPL-ONLY` of `PROVENANCE-UNKNOWN` materiaal gebruiken waar de proprietary licentie aanvullende toestemming nodig heeft.

### AI-provenance

Voor bestaande AI-assisted files moet per relevante development workflow minstens worden geregistreerd:

* welke provider/tool waarschijnlijk is gebruikt;
* welke outputvoorwaarden op dat moment golden, voor zover reconstructeerbaar;
* of substantiële menselijke selectie, herformulering, architectuur en editing aantoonbaar zijn;
* of output herkenbare/copy-like third-party code bevat;
* of code scanners of handmatige review verdachte overeenkomsten vinden.

Het doel is niet kunstmatig te bewijzen dat ieder AI-token copyright van de founder is. Het doel is precies het tegenovergestelde: **de commercial license verkoopt alleen rechten waarvan de Foundation redelijkerwijs kan onderbouwen dat zij ze heeft**.

Apache's actuele generative-toolingbeleid is op dit punt een goede OSS-benchmark: een CLA-originalityrepresentatie ontslaat het project niet van analyse van third-party materiaal, toolvoorwaarden en de vraag of output überhaupt beschermbare menselijke auteursbijdrage bevat.

### Benodigde wijzigingen aan PR #21

PR #21 moet conceptueel worden behouden, maar vóór juridische activering zou ik de volgende wijzigingen eisen.

**`docs/interim-rights-custody-proposal.md`.** Vervang “custody” waar het afgescheiden vermogen suggereert door `Interim Supplemental Rights Holder`; voeg contractsoverneming met advance consent toe; voeg springing fallback/derdenbeding toe; maak long-stop, death/incapacity/insolvency, objective qualification en confirmatory transfer expliciet. De bestaande tekst benoemt veel van deze open vragen al correct.

**`docs/contributor-commercial-grant.md`.** Van policy skeleton naar daadwerkelijk te ondertekenen overeenkomst met: partijen, governing law, forum, definitions, exact rights, contribution coverage, patentgrant, employer authority, AI/third-party representations, Open-Core Covenant, cure/termination, customer survival, Qualified Successor, contract takeover, long-stop en e-signature/evidence.

**`CONTRIBUTING.md`.** Maak duidelijk dat copyright-relevant contributions pas worden gemerged na `commercial-rights-cleared`. Normale AGPL-submission zonder supplemental grant mag niet ongemerkt onderdeel worden van de dual-licenseable core. De huidige conceptdiff erkent al dat AGPL alleen geen supplemental commercial authority oplevert.

**`docs/licensing-rights-register.md`.** Voeg exacte commit/blob coverage, grant version, public/private contributor identifiers, AI status, third-party exclusions, patentstatus en commercial-release eligibility toe.

**`docs/commercial-licensing.md` en website.** Vermeld expliciet dat AGPL commercieel gebruik toestaat, dat normaal intern gebruik niet betaald hoeft te worden en dat de commercial license een **alternatief licentiemodel** is. Voorkom “commercial use requires a license”. AGPL zelf en GNU's eigen guidance ondersteunen dit onderscheid.

**Foundation documentation.** Definieer `DAIA Core`, `Qualified DAIA Foundation`, `Independent Director`, `Qualified Successor`, `Foundation Purpose` en `Open-Core Covenant` één keer normatief en laat andere documenten daarnaar verwijzen.

## Concreet implementatiepakket vóór de eerste externe codebijdrage

### Voorstel voor de definitieve agreement

De uiteindelijke **DAIA Supplemental Contributor Commercial Grant Agreement** hoeft geen copyright assignment te zijn. De inhoudelijke term sheet moet minstens dit bevatten:

**Partijen en identiteit**

`Contributor` / `Rightsholder`; geïdentificeerde `Interim DAIA Supplemental Rights Holder`; later `Qualified DAIA Foundation`.

**Copyright retention**

> Contributor retains ownership of the Contribution. Nothing in this Agreement assigns Contributor's copyright.

**AGPL independence**

> Contributions accepted into the official DAIA Community repository remain available under AGPL-3.0-or-later. This Agreement neither terminates nor restricts rights previously or subsequently granted under that license.

**Supplemental copyright grant**

Niet-exclusief, worldwide, royalty-free, voor duur van auteursrecht, reproduce/modify/adapt/derive/combine/compile/distribute/make available en commercial/proprietary sublicense, alleen voor DAIA-context.

**Interim restriction**

> The Interim Holder shall not exercise the Supplemental License to issue or authorize a commercial or proprietary end-user license.

Alleen administratie, rights verification en overdracht.

**Transfer**

Vooraf verleende medewerking aan contractsoverneming naar eerste Qualified Foundation; verplicht confirmatory instrument; notice aan contributor.

**Fallback**

Derdenbeding/conditionele directe grant in geval primaire transfer faalt, onder voorbehoud van advocaatvalidatie.

**Qualified Foundation**

Objectieve schedule met alle hierboven genoemde voorwaarden.

**Open-Core Covenant**

De commercial-cleared officiële DAIA Core en Foundation-owned verbeteringen daarvan blijven AGPL-3.0-or-later beschikbaar.

**Breach**

Material breach, notice, cure, injunctive relief, suspension van nieuwe licensing authority en successor mechanism.

**Existing customers**

Valid pre-termination commercial sublicenses survive binnen bestaande scope.

**Patent grant**

Smalle necessarily-infringed-claims grant.

**Representations**

Authority, employer approval waar relevant, disclosure third-party/AI/confidential material, geen absolute non-infringement warranty en geen algemene indemnity.

**Successor**

Alleen Qualified Successor.

**Long-stop**

Interimconstructie eindigt als Foundation niet binnen vastgestelde termijn bestaat, bijvoorbeeld drie jaar.

**Evidence**

CLA version/hash, tijdstip, electronic acceptance, private identity mapping, GitHub numeric ID en Covered Contributions.

**Governing law**

Nederlands recht en vooraf gekozen bevoegde Nederlandse rechter, tenzij counsel om internationale contributorredenen een andere dispute-clause adviseert.

### Founder-to-Foundation document

Een apart `Founder Supplemental Rights and Foundation Commitment Agreement` moet vervolgens bevatten:

1. schedules met alleen aantoonbaar founder-held copyrights;
2. expliciete provenance exclusions;
3. dezelfde supplemental Foundation license;
4. eventueel overdracht van specifieke founder-owned IP, alleen waar afzonderlijk gewenst;
5. covenant dat founder na Foundation assumption geen parallelle officiële commercial DAIA licensing uitvoert;
6. overdracht/beëindiging van alle interim contributorposities;
7. geen claim op contributor copyrights;
8. afzonderlijke regeling voor trademarks/domain/project assets indien relevant;
9. volledige scheiding tussen IP-grant en founder compensation.

Daarna mag de founder dus nog steeds zijn eigen auteursrecht houden, maar niet de Foundation omzeilen om contributorcode persoonlijk proprietary te licentiëren.

### Foundation Assumption-document

Bij oprichting:

```text
FOUNDATION ASSUMPTION AND TRANSFER AGREEMENT

Foundation:
✓ is rechtsgeldig opgericht
✓ voldoet aan Qualified Foundation Schedule
✓ accepteert Open-Core Covenant
✓ accepteert alle contributor obligations
✓ accepteert successor/transfer restrictions
✓ ontvangt rights register + contract records
✓ wordt commercial licensor

Interim Holder:
✓ levert/voltooit contractsoverneming
✓ levert registers en bewijs
✓ behoudt geen customer sublicensing authority
✓ kan contributorrechten niet later heractiveren
```

### “Safe to accept external code contributions”

DAIA is vóór oprichting van de stichting **niet verplicht het openbare project stil te leggen**.

Het veilige onderscheid is:

- [x] **AGPL-repository openbaar houden.** Ja. De bestaande openbare AGPL-rechten blijven intact.
- [x] **Issues aannemen.** Ja; ideeën en feitelijke bugmeldingen kunnen gewoon worden aangenomen.
- [x] **Researchlinks en feitelijke onderzoeksresultaten aannemen.** Ja, met normale third-party/contentcontrole.
- [x] **Logs, reproduceerstappen en puur feitelijke testresultaten aannemen.** In beginsel ja.
- [!] **Tests als code automatisch uitzonderen.** Nee. Substantiële testcode kan auteursrechtelijk beschermd zijn.
- [!] **Documentatiepatches automatisch uitzonderen.** Nee. Substantiële creatieve tekst kan auteursrechtelijk beschermd zijn.
- [ ] **Externe auteursrechtelijk relevante code nú mergen zonder supplemental agreement.** Niet doen wanneer die code later door de Foundation proprietary relicensed moet kunnen worden.
- [x] **Externe code mergen nadat de interim CLA operationeel is.** Ja, mits de contributor/rightsholder correct is geïdentificeerd, de CLA effectief is, employer/third-party/provenancecontrole is afgerond en het rights register wordt bijgewerkt.
- [x] **Wachten tot de stichting daadwerkelijk bestaat.** Niet noodzakelijk wanneer het interimmechanisme juridisch goed is geïmplementeerd.

De huidige repositorypolicy maakt die tijdelijke stop op external commercial-cleared code zelfs bijzonder verstandig: `LICENSE-STATUS.md` zegt nu expliciet dat bijdragen geen bredere proprietary/commercial relicensingrechten verschaffen.

### Vóór de eerste externe copyright-relevante merge

De minimale concrete go-livechecklist is daarom:

- [ ] Nederlandse IE-/softwareadvocaat heeft de ICCLA definitief beoordeeld.
- [ ] Contractsoverneming + advance consent is correct gedraft.
- [ ] Springing/derdenbedingfallback is rechtsgeldig bevonden.
- [ ] Death/incapacity/faillissementsscenario is gevalideerd.
- [ ] Qualified Foundation Schedule ligt vast.
- [ ] Interimholder is met volledige juridische identiteit genoemd.
- [ ] Interimholder kan geen commerciële klantlicenties verstrekken.
- [ ] Driejaars-long-stop of vergelijkbaar mechanisme ligt vast.
- [ ] Supplemental copyrightrechten zijn expliciet opgesomd.
- [ ] Patentgrant is opgenomen of bewust na advocaatadvies weggelaten.
- [ ] Open-Core Covenant + breach/cure/customer survival zijn vastgelegd.
- [ ] Employer/corporate contributor route bestaat.
- [ ] AI- en third-party-disclosureprocedure bestaat.
- [ ] Private CLA datastore + publiek pseudoniem register bestaat.
- [ ] CLA-bot/statuscheck blokkeert merge wanneer clearance ontbreekt.
- [ ] Branch protection vereist de clearance-status.
- [ ] Baseline provenance-audit van bestaande `main` is uitgevoerd.
- [ ] Commercial release manifest onderscheidt cleared en excluded materiaal.
- [ ] Founder Rights Grant-template ligt gereed.
- [ ] Foundation Assumption-template ligt gereed.
- [ ] PR #21 blijft tot die tijd expliciet non-effective policy/draft.

### Punten die de Nederlandse IE-/softwarejurist móét valideren

Dit zijn geen algemene voorbehouden maar de concrete punten waarop ik **niet** zou livegaan zonder specialistische Nederlandse review:

**Contractsoverneming.** Bevestigen dat de gekozen combinatie van BW 6:159/6:156 de volledige supplemental licensepositie en bijbehorende plichten zonder nieuwe contributorhandtekening kan laten overgaan en welke akte/kennisgeving exact vereist is.

**Future-foundation fallback.** Bevestigen dat het derdenbeding/voorwaardelijke directe grant aan de nog niet bestaande maar objectief bepaalbare eerste Qualified Foundation voldoende bepaalbaar is en welke aanvaarding nodig is.

**Faillissementsbestendigheid.** Specifiek beoordelen wat een curator kan doen met de interim contract-/licentiepositie en of aanvullende structurering nodig is. Geen “custody = afgescheiden vermogen” claim gebruiken zonder die analyse.

**Overlijden en handelingsonbekwaamheid.** Bevestigen dat de direct-grantfallback en automatische suspension daadwerkelijk voorkomen dat commercial licensing authority afhankelijk wordt van erfgenamen/bewindvoerder.

**Auteurscontractenrecht.** Beoordelen of de royalty-free supplemental commerciële exploitatiegrant van een natuurlijke-persoonsauteur onder de Nederlandse dwingendrechtelijke auteurscontractenregels valt en of term, vergoeding, transparantie of beëindigingsregels aangepast moeten worden.

**Licentieduur en “irrevocable”.** Exact formuleren wat onopzegbaar is, wat conditional is en welke rechten na material breach worden geschorst/beëindigd.

**Persoonlijkheidsrechten.** Een beperkte technische consent/non-assertion formuleren zonder ongeldige blanket waiver.

**Patentclausule.** Scope, defensive termination en sublicensing naar proprietary klanten valideren.

**Customer survival.** Bevestigen dat bestaande customer sublicenses contractueel blijven bestaan wanneer de Foundation haar bevoegdheid om nieuwe licenties uit te geven verliest.

**Qualified Successor.** Zorgen dat klantensublicensing niet per ongeluk onder het verbod op overdracht van de onderliggende contributorrechten valt.

**Statuten.** Mission lock, bestuursbenoeming, founder-invloed, conflicts, compensatie, statutenwijziging, ontbinding en opvolger correct in notariële statuten vertalen.

**Founder compensation.** Opzet van arbeids-/opdrachtovereenkomst, conflictrecusal en marktconformiteitsdocumentatie beoordelen.

**Fiscaliteit.** Vpb, btw, loonheffing, eventuele ANBI-ambitie en behandeling van commerciële licentieopbrengsten met fiscalist/accountant uitwerken. Belastingplicht van een stichting hangt van feitelijke activiteiten af en volgt niet simpelweg uit haar rechtsvorm.

**Privacy/CLA-administratie.** AVG-grondslag, bewaartermijn en toegang voor legal-name/employer records vastleggen; het publieke register moet in beginsel niet méér persoonsgegevens tonen dan nodig.

**Founder provenance.** Per relevant bestaand bestand vaststellen welke rechten werkelijk bij founder liggen; geen algemene ownershiprepresentation voor AI-assisted of onbekend materiaal.

**AI-providerterms.** Historische voorwaarden van de daadwerkelijk gebruikte providers/tools onderzoeken voor zover die commerciële outputrechten of gebruiksrestricties kunnen beïnvloeden.

De kern is daarmee vrij scherp: **DAIA hoeft niet te kiezen tussen duurzaam open source en een financierbare commerciële licentiestructuur.** De AGPL-laag kan permanent publiek blijven; contributors kunnen hun copyright behouden; en een onafhankelijke stichting kan voldoende aanvullende rechten verzamelen om alternative proprietary licenses te verstrekken. Het juridisch zwakke punt is niet dat model zelf, maar iedere poging om de tussenfase informeel te laten rusten op “de founder bewaart de rechten wel even”. Maak die tussenfase een formele, zeer beperkte contractpositie met vooraf geautoriseerde overgang, onafhankelijke kwalificatie, een directe fallback, een long-stop en een strikt verbod op persoonlijke commercialisering. Daarmee wordt PR #21 van een verstandig beleidsvoorstel om te bouwen tot een structuur die zowel contributorvertrouwen als toekomstige commerciële licentiezekerheid kan dragen.