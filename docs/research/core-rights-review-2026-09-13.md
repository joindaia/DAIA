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

# DAIA: juridisch robuuste Core-rechten, contributorstructuur en commerciële licentiëring

## Executive conclusie en aanbevolen rechtenarchitectuur

**Hoofdconclusie.** De beoogde DAIA-architectuur is juridisch plausibel, maar ik zou haar op één belangrijk punt aanscherpen: voor reguliere externe contributors verdient **copyright retention + een zeer ruim, duurzaam supplemental commercial grant** de voorkeur boven verplichte centrale auteursrechtoverdracht. Dat model kan de stichting praktisch alle rechten geven die zij voor dual licensing nodig heeft, terwijl contributors hun auteursrecht behouden. Qt is daarvoor een bijzonder relevante praktijkvergelijking: contributors behouden daar hun IP, maar geven via een verplichte Contribution Agreement voldoende auteursrechtelijke en octrooirechten om zowel open-source- als commerciële belangen te bedienen. Qt laat bovendien beëindiging van de agreement alleen prospectief werken; reeds geleverde contributions blijven onder de agreement vallen.  Harmony voorziet eveneens expliciet in een retained-copyrightmodel met een perpetual, irrevocable copyright licence en sublicensing door meerdere lagen.

**DAIA moet echter niet stellen dat zo'n licentie juridisch volledig gelijk is aan copyright assignment.** Assignment geeft een schonere centrale titel en kan handhaving en due diligence eenvoudiger maken. Een brede niet-exclusieve licence kan daarentegen commercieel vrijwel dezelfde gebruiks- en sublicentiebevoegdheid opleveren, maar laat eigendom, persoonlijkheidsrechten en mogelijk bepaalde enforcement-vragen bij de contributor. Onder Nederlands recht is auteursrecht overdraagbaar en kan een rechthebbende licenties verlenen; overdracht en een exclusieve licentie vereisen een daartoe bestemde akte en omvatten slechts de daarin genoemde of noodzakelijk daaruit voortvloeiende bevoegdheden. Persoonlijkheidsrechten blijven bovendien ook na overdracht in relevante mate bij de maker.

Er is nog een Nederlandsrechtelijk punt dat belangrijk genoeg is om vóór livegang expliciet te laten toetsen: het auteurscontractenrecht kent voor overeenkomsten die exploitatiebevoegdheid verlenen bepalingen over onder meer een contractueel te bepalen billijke vergoeding. De huidige Auteurswet sluit bepaalde makers uit artikelen 7 en 8 van delen van dit regime uit, maar dat lost de positie van natuurlijke vrijwillige contributors niet vanzelf op. Een simpele CLA-zin “royalty-free, irrevocable forever” moet daarom niet zonder Nederlandse specialistische toets worden aangenomen als onaantastbaar.

Mijn aanbevolen eindmodel is daarom:

```text
                 PRIVATE LEGAL RECORD
       ┌────────────────────────────────────┐
       │ Participant / Organization         │
       │ - verified legal party             │
       │ - ICLA or Organizational CLA       │
       │ - agreement version + evidence     │
       │ - authorized worker identities     │
       └─────────────────┬──────────────────┘
                         │ one-time agreement
                         ▼
                 Authorized DAIA Worker
                    /             \
                   /               \
        DAIA Core task             External DAIA Job
              │                           │
              ▼                           ▼
     submitted Core material       customer / other repo /
              │                    research / external project
              ▼                           │
     review + provenance                   │
              │                           │
       ACCEPTED AS CORE?                   │
          │          │                     │
         no         yes                    │
          │          │                     │
          ▼          ▼                     ▼
     no DAIA     Accepted DAIA        NOT captured by
     commercial  Core Contribution    DAIA Core CLA
     grant            │
                      ├── AGPL-3.0-or-later → everyone
                      │
                      └── Supplemental commercial grant
                                  │
                    before foundation exists
                                  ▼
                         Interim Steward
                  administrative/custodial only
                  NO personal commercial licensing
                                  │
                  direct beneficiary / accession +
                  mandatory qualified transfer path
                                  ▼
                     Qualified DAIA Foundation
                     ├─ sole official alternative licensor
                     ├─ commercial/proprietary sublicences
                     ├─ complete Official Core under AGPL
                     ├─ project-purpose licensing income
                     └─ Qualified Successor only
```

De kern moet dus niet zijn “wat een worker maakt is van DAIA”. De kern moet zijn:

> **De participant of organisatie sluit vooraf de overeenkomst; de worker is slechts een technisch middel. Alleen materiaal dat volgens een nauw omschreven procedure formeel als DAIA Core Contribution wordt geaccepteerd, valt automatisch onder de reeds overeengekomen aanvullende rechten.**

Daarmee verdwijnt in principe de noodzaak om twintig jaar later een verdwenen participant terug te vinden. Afgewezen output, experimentele output en externe DAIA Job Output blijven buiten het supplemental grant.

### Beslissing over assignment versus supplemental licence

| Vraag | Centrale assignment | Copyright retention + supplemental licence |
|---|---|---|
| Wie bezit contributorcopyright? | Centrale rechtenhouder | Contributor |
| Commerciële proprietary sublicensing | Zeer duidelijk | Eveneens goed mogelijk als uitdrukkelijk verleend |
| Centrale title/due diligence | Sterkst | Sterk met goed register, maar licence chain moet worden bewezen |
| Handhaving | Eenvoudiger vanuit eigenaar | Enforcement authorization/standing apart regelen |
| Nederlandse formaliteiten | Akte vereist | Niet-exclusieve licence is formeel minder zwaar; contractbewijs blijft essentieel |
| Persoonlijkheidsrechten | Niet volledig opgelost | Evenmin volledig opgelost |
| Internationale formaliteiten | Relatief zwaar | Gewoonlijk beter schaalbaar |
| Contributor acceptance | Potentieel afschrikkender | OSS-vriendelijker |
| AI-output zonder auteursrecht | Assignment draagt niets over wat niet bestaat | Licence verleent evenmin niet-bestaande rechten |
| Third-party code | Geen oplossing | Geen oplossing |
| Doel DAIA | Meer eigendom dan nodig | Rechten precies afstemmen op licensingbehoefte |
| Mijn advies | Niet standaard | **Aanbevolen** |

Qt bevestigt dat een project met commerciële gebruikers geen assignment nodig heeft om een centraal contribution-rightsmodel te voeren; contributors blijven daar eigenaar en een CA is verplicht vóór bijdrage. Qt ondersteunt tevens een corporate CA, patent grant en expliciete behandeling van employer-owned bijdragen.  Harmony heeft zowel assignment- als licence-opties ontwikkeld en beschrijft zijn licencevariant juist als een zeer brede licence met multiple-tier sublicensing.

**Mijn antwoord op de centrale ontwerpvraag is daarom:** voor DAIA is een perpetual supplemental commercial grant **voldoende robuust voor de primaire behoefte — toekomstige proprietary/commerciële sublicensing zonder contributor terug te hoeven vinden — mits het grant zeer nauwkeurig is ontworpen, acceptance goed wordt bewezen en de rights registry op artifactniveau wordt bijgehouden.** Assignment heeft een reëel voordeel voor central title en enforcement, maar dat voordeel weegt hier niet op tegen de grotere internationale/formele frictie, het contributor-relationsnadeel en het feit dat assignment de lastigste provenanceproblemen helemaal niet oplost.

**Kan DAIA vandaag al externe code mergen?** Op basis van de huidige situatie: **nee, niet als het doel is dat alle nieuwe DAIA Core-code later probleemloos in een alternatieve commerciële release kan zitten.** PR #21 noemt het supplemental grant en de interim custody zelf expliciet nog onuitgevoerde drafts en benadrukt dat een AGPL-bijdrage niet stilzwijgend aanvullende commerciële rechten geeft.  De draft grant zegt eveneens expliciet dat zij nog geen effectieve grant is.

DAIA kan ondertussen wel volledig AGPL-openbaar blijven. Issues, ideeën, bugreports en onderzoek kunnen doorgaan. Tests, documentatie, patches en andere mogelijk auteursrechtelijk relevante bijdragen moeten voor Core echter net zo serieus worden behandeld als programmacode. **Zodra een door Nederlandse IE-/softwarecounsel gevalideerde interim CLA, private identity flow, provenanceprocedure, rights register en merge gate operationeel zijn, is pre-foundation acceptatie juridisch plausibel. Oprichting van de stichting vóór externe Core-code blijft de juridisch schoonste optie.**

## Nederlandsrechtelijke kern, toekomstige bijdragen en de interimfase

### Vooraf rechten regelen voor toekomstige worker-contributions

**Wet/bron.** Nederlands auteursrecht staat overdracht en licentiëring toe. Bij overdracht of een exclusieve licentie is een akte nodig. Het vermogensrecht verlangt bovendien dat een over te dragen goed voldoende bepaald is; Boek 3 BW verlangt voor overdracht een geldige titel, beschikkingsbevoegdheid en voldoende bepaaldheid van het goed.

**Mijn interpretatie.** Dit ondersteunt een constructie waarin de agreement vandaag wordt gesloten en haar werking later automatisch wordt gekoppeld aan objectief herkenbare toekomstige contributions. Voor DAIA is een licentiemodel gemakkelijker dan een voorafgaande goederenrechtelijke overdracht van allerlei toekomstige werken. De agreement moet niet zeggen “alles wat jouw agents ooit voor DAIA doen”. Dat is zowel commercieel als juridisch onnodig breed.

Ik zou **Accepted DAIA Core Contribution** ongeveer functioneel als volgt definiëren:

> materiaal ten aanzien waarvan de participant of de vertegenwoordigde organisatie rechten bezit of beheerst, dat door de participant of een vooraf aan diens contributorrecord gekoppelde authorized worker wordt ingediend via een door DAIA aangewezen Core Contribution Channel, voor een component die op dat moment in de DAIA Core Scope Register staat, en dat vervolgens door een bevoegde maintainer uitdrukkelijk als DAIA Core Contribution wordt geaccepteerd en in de officiële DAIA Core-history wordt opgenomen of in een onveranderlijk acceptance record wordt geïdentificeerd.

Daarbij horen vier belangrijke negatieve begrenzingen:

**Geen acceptance, geen commercial grant.** Een PR die wordt gesloten, een experiment in een worker sandbox, een patch die alleen ter review wordt gegenereerd of een resultaat dat nooit upstream wordt gebruikt, wordt geen Covered Contribution.

**Geen Core-designation, geen commercial grant.** Een worker die toevallig een ander project helpt, draagt daardoor niets aan DAIA over.

**Geen rechten buiten de contributor.** Het grant werkt slechts “to the extent rights exist and are owned or controlled by Contributor”.

**Geen third-party-material door magie.** Dependencies, snippets of upstream code worden niet opeens commercieel relicentieerbaar omdat ze in een submission zitten.

Harmony legt vergelijkbaar sterk de nadruk op een precieze definitie van “Contribution” en maakt onderscheid tussen een submission als geheel en dat deel waarop de contributor zelf rechten bezit; mixed/third-party submissions moeten apart worden behandeld.

De beste **trigger** is naar mijn oordeel niet creation en ook niet submission, maar **formele acceptance into Official DAIA Core**. Bij submission krijgt DAIA hooguit de beperkte rechten die nodig zijn om de submission te bekijken, testen, reproduceren voor review en het auditrecord te bewaren. Het brede supplemental grant springt pas aan bij acceptance. Dat sluit precies aan bij het doel: DAIA krijgt niet onverwacht rechten over het volledige outputuniversum van een participant.

### De interimconstructies vergeleken

| Interimmodel | Sterkte | Hoofdprobleem | Advies |
|---|---|---|---|
| Assignment aan founder/custodian | Eigendom centraal en duidelijk | Founder-estate/insolventie; akte; te zwaar; personal concentration | Niet aanbevolen |
| Supplemental licence aan founder + latere overdracht | Minder invasief | Een verplichting om later over te dragen **is niet hetzelfde als de overdracht zelf** | Alleen als onderdeel van hybride model |
| Conditional direct future grant aan stichting | Vermijdt persoonlijke commercial power | Stichting bestaat nog niet; moment van verkrijging/acceptance moet juridisch werken | Goed als tweede laag |
| Derdenbeding ten gunste van Qualified Foundation | Geeft toekomstige stichting mogelijk rechtstreeks eigen contractueel recht | Exacte determinability/acceptance toekomstige rechtspersoon moet worden gevalideerd | Sterke tweede laag |
| Hybride constructie | Redundantie en minder founder-dependence | Meer draftingwerk | **Aanbevolen indien stichting nog niet bestaat** |
| Stichting eerst oprichten | Schoonste chain | Tijd/organisatie nodig | **Juridisch voorkeursmodel** |

Een Nederlands **derdenbeding** is relevant omdat art. 6:253 BW een derde na aanvaarding een eigen recht uit een overeenkomst kan geven. Contractsoverneming onder art. 6:159 BW heeft daarentegen haar eigen mechaniek en vereist niet simpelweg de mededeling “wij dragen dit later wel over”. Voor schuldoverneming kent het BW ook voorafgaande medewerking. Die concepten kunnen worden gecombineerd, maar moeten niet als onderling verwisselbaar worden behandeld.

De huidige PR #21 onderkent dit probleem al terecht: de interim-custody draft zegt expliciet dat een verplichting tot transfer de rechten niet vanzelf levert en dat de term “custodial” geen apart vermogen creëert of bescherming tegen schuldeisers of erfgenamen bewijst.

### Aanbevolen interimmechanisme

Indien DAIA de stichting werkelijk nog niet wil oprichten vóór de eerste externe contribution, zou ik niet één mechanisme kiezen, maar een **redundante vierlaagse constructie** laten uitwerken.

**Eerste laag — beperkt recht voor de Interim Steward.** De geïdentificeerde natuurlijke persoon krijgt slechts datgene wat nodig is om het systeem te administreren, rechtenrecords te bewaren en de overgang te effectueren. Hij krijgt **geen bevoegdheid om proprietary licences aan klanten uit te geven**, geen vrije assignmentbevoegdheid, geen verpandingsbevoegdheid en geen bevoegdheid om het grant aan zijn eigen onderneming of een andere commerciële onderneming te verplaatsen.

**Tweede laag — direct Foundation-benefit.** De originele participant agreement bevat tegelijk een onherroepelijk, objectief gedefinieerd derdenbeding en/of standing grant ten gunste van de eerste rechtspersoon die aan de Qualified DAIA Foundation-definitie voldoet en de obligations formeel aanvaardt. De stichting moet dus een eigen recht uit de oorspronkelijke contributor agreement kunnen verkrijgen in plaats van voor alles van een latere handtekening van de founder afhankelijk te zijn. De precieze werking voor een nog niet bestaande, maar bepaalbare rechtspersoon is een van de punten die Nederlandse counsel expliciet moet bevestigen.

**Derde laag — voorafgaande medewerking aan contractsovergang.** Contributor stemt reeds bij ondertekening in met de specifiek omschreven overgang/contractsoverneming naar een Qualified DAIA Foundation of Qualified Successor, voor zover die figuur volgens het toepasselijke recht medewerking verlangt. De latere stichting tekent een **Deed/Agreement of Accession and Transfer** waarin zij alle community-, revenue-, governance- en successorverplichtingen accepteert. De interim steward houdt daarna geen parallelle commerciële authority.

**Vierde laag — independent fail-safe.** Een tweede onafhankelijke rights guardian of escrowfunctie bewaart de uitgevoerde agreements en bewijsstukken en krijgt een nauw beperkte bevoegdheid om de geobjectiveerde overgang administratief te voltooien als de Interim Steward overlijdt, onbekwaam wordt, verdwijnt of weigert. Dit moet geen vrije licensing power worden.

**Bij overlijden of onbekwaamheid** moet het systeem daarom zo zijn ontworpen dat geen nieuwe toestemming van de founder vereist is. **Bij insolventie ligt het moeilijkste risico.** Een contractueel verbod om een recht te verkopen of verpanden is niet hetzelfde als een faillissementsbestendige afgescheiden vermogensstructuur. Juist daarom is de stichting-eerst-route juridisch duidelijk veiliger dan langdurige persoonlijke “custody”.

**Als er nooit een stichting komt**, zou ik een long-stop opnemen, bijvoorbeeld 18–24 maanden. Het interim supplemental commercial authority blijft in die periode dormant: geen proprietary customer licensing. Daarna kan het óf vervallen voor toekomstige commerciële exploitatie, óf uitsluitend naar een vooraf gedefinieerde Qualified Successor Nonprofit gaan. Wat niet moet gebeuren is: “als stichting niet lukt, mag de founder het dan zelf commercieel gebruiken.” Dat zou de hele governancegarantie uithollen.

## Definitieve contributor agreement, Core/Job-scheiding, patents en acceptatie

De definitieve overeenkomst zou ik niet “CLA” noemen zonder onderscheid, maar bijvoorbeeld **DAIA Core Contribution and Supplemental Licensing Agreement**, met een Individual-versie en Organization-versie.

### Clause-by-clause architectuur

| Clausule | Aanbevolen inhoud |
|---|---|
| Parties | Werkelijke natuurlijke persoon of organisatie; DAIA Interim Steward respectievelijk Foundation; worker is uitdrukkelijk geen partij |
| Core Scope | Official DAIA Core wordt bepaald via versieerbare Core Scope Register; repos/componenten en contribution channels moeten identificeerbaar zijn |
| External Jobs exclusion | Geen rechten op customer work, externe repos, research, andere OSS-projecten, privésoftware of output die niet als Core is geaccepteerd |
| Authorized Workers | Participant kan worker identifiers vooraf aan zijn private contributorrecord koppelen; worker kan zelf geen agreement aangaan |
| Covered Contribution | Alleen participant-owned/controlled material dat volgens de acceptance trigger daadwerkelijk onderdeel van Core wordt |
| Acceptance trigger | Merge/accepted commit of afzonderlijk cryptografisch vastgelegd acceptance record; PR openen is onvoldoende |
| Community licence | Covered Contribution blijft beschikbaar als onderdeel van Official DAIA Core onder AGPL-3.0-or-later |
| Supplemental licence | Wereldwijde commercial/proprietary rights zoals hieronder |
| Third-party exclusions | Licentie strekt zich niet uit tot geïdentificeerde third-party material, dependencies of rechten die contributor niet controleert |
| AI | Alleen rechten “to the extent they exist and are owned or controlled”; geen fictieve warranty dat AI-output auteursrechtelijk beschermd is |
| Patent | Nauw Apache/Qt-achtig patent grant |
| Employer/organization | Individuele contributor verklaart authority; OCLA voor employer-owned/organization-owned werk |
| Warranties | Authority + disclosure; geen absolute originality/non-infringement guarantee |
| Foundation qualification | Objectieve Qualified Foundation-test rechtstreeks onderdeel agreement |
| Successors | Alleen Qualified Successor, met verplicht accession |
| Community guarantee | AGPL-continuïteit + commercial-core parity + remedies |
| Termination | Prospective termination voor nieuwe contributions; oude Covered Contributions blijven gedekt |
| Customer survival | Reeds verleende bona-fide commercial sublicences blijven bestaan ondanks later governancegeschil |
| Enforcement | Nauw omschreven enforcement authorization/cooperation; geen onbeperkte POA zonder counsel |
| Evidence/privacy | Private legal identity; public pseudonymous clearance record |
| Governing law | Nederlands recht als basis, met expliciete aandacht voor dwingend lokaal auteurs-/arbeidsrecht van buitenlandse contributors |

### Minimale supplemental copyright grant

De Foundation moet niet “alle mogelijke IP-rechten” krijgen. Zij heeft functioneel nodig:

> een wereldwijde, royalty-free behoudens dwingend toepasselijk auteurscontractenrecht, niet-exclusieve, duurzame licence om een Covered Contribution te reproduceren, op te slaan, te verveelvoudigen, uit te voeren waar relevant, te wijzigen, vertalen en adapteren, daarvan afgeleide werken te maken of te doen maken, met DAIA en andere software te combineren, in bron- en objectvorm beschikbaar te stellen, openbaar te maken, te distribueren/conveyen, en die bevoegdheden rechtstreeks of via meerdere lagen te sublicentiëren onder open-source én alternatieve commerciële/proprietary voorwaarden, uitsluitend in verband met DAIA Core en daarmee samenhangende DAIA-distributies, producten en services.

Harmony ondersteunt precies de kern van dit ontwerp: retained ownership, traditional copyright rights, perpetual/irrevocable character en multiple-tier sublicensing.

**Niet nodig:** eigendom van de contributor zelf; trademarks; unrelated inventions; customer jobs; algemene rechten in alle toekomstige output; alle patenten van een contributor; datarechten in unrelated datasets; exclusiviteit over de standalone contribution buiten DAIA.

De licence aan contributors zou **niet-exclusief** moeten blijven. Dat betekent dat iemand zijn eigen standalone library of snippet later elders kan gebruiken of licentiëren. “Foundation is de enige officiële commerciële DAIA Core-licensor” hoeft niet te betekenen “contributor mag zijn eigen code nergens anders meer exploiteren.”

### Founder-to-Foundation grant

Voor de founder is een iets ander instrument logisch omdat zonder beperking een founder die zijn eigen copyright behoudt anders theoretisch een parallelle proprietary DAIA-distributie zou kunnen gaan aanbieden.

Mijn voorkeur:

> Founder retains all copyrights actually owned by Founder, but grants the Qualified DAIA Foundation an **exclusive field-of-use licence for official alternative/proprietary licensing of DAIA Core**, plus all necessary sublicensing rights, while expressly reserving AGPL publication, ordinary use and any unrelated exploitation outside that defined field.

Omdat een exclusieve licentie onder de Nederlandse Auteurswet een akte vereist, moet dit als afzonderlijk degelijk ondertekend instrument worden uitgevoerd.  Een minder formeel alternatief is een brede nonexclusive grant plus covenant dat de founder nooit buiten de Foundation officiële proprietary DAIA Core-licenties zal uitgeven. De exclusive-field route is echter sterker tegen toekomstige omzeiling.

Het founder-instrument moet bovendien per artifact vastleggen: “rights actually owned or controlled”, niet “Founder owns DAIA”. AI-output, dependencies en eventuele third-party code blijven buiten de garantie.

### Patentregeling

AGPL/GPL heeft al een patentregime voor verspreiding onder die licence, maar een commerciële klant die juist onder een alternatieve proprietary licence opereert moet niet afhankelijk zijn van de gedachte dat de AGPL-patentgrant automatisch dezelfde alternatieve transactie dekt.

Ik zou daarom een apart, smal grant opnemen:

> worldwide, royalty-free, non-exclusive patent licence, sublicensable together with the Covered Contribution, uitsluitend voor patent claims die Contributor kan licentiëren en die noodzakelijk worden geschonden door de Covered Contribution alleen of door de Covered Contribution in de combinatie met DAIA Core waaraan zij is bijgedragen.

Dit volgt de logica van gevestigde CLA’s. Qt verlangt een patent licence voor licensable contributor patents die door de contribution zelf of haar gebruik met Qt worden geraakt en legt de contributor geen algemene warranty op dat geen third-party patents worden geschonden.  Harmony bevat eveneens een separate patentlicentie naast zijn copyright licence.

Een volledige portfolio licence, patent assignment of verplicht patentonderzoek is voor een jong project onnodig zwaar. Een zorgvuldig geformuleerde defensive-terminationclausule bij een patentaanval op DAIA kan nuttig zijn, maar moet worden afgestemd op de commercial customer licence.

### Employer, contractors, gezamenlijke makers en AI

Onder de Nederlandse Auteurswet kan bij werk dat in dienstbetrekking bestaat uit het maken van de betreffende werken de werkgever, tenzij anders overeengekomen, als maker gelden. DAIA mag dus nooit alleen vragen “heb jij deze code geschreven?” maar moet vragen “heb jij de rechten of authority om deze grant te geven?”.

Daarom zijn **ICLA + OCLA** nodig. Qt gebruikt dezelfde tweedeling: individuele contributors moeten employer ownership/authorization controleren en een corporate agreement kan een door de organisatie beheerde groep authorized contributors aanwijzen.

Voor contractors geldt hetzelfde beginsel zonder een mondiale “work-for-hire”-aanname: de relevante overeenkomst en het toepasselijke recht moeten bepalen wie de rechten heeft. Bij jointly owned material moeten alle benodigde rightsholders hebben ingestemd of moet één partij aantoonbare authority hebben.

Voor minderjarigen zou ik DAIA aanvankelijk conservatief maken: geen status **commercially cleared** zonder door counsel goedgekeurde ouder/voogdprocedure. Een bijdrage kan anders AGPL-only of excluded blijven.

Voor AI moet de warranty ongeveer luiden:

> “Contributor grants only such transferable or licensable copyright, neighbouring rights, database rights, patent rights or other relevant rights as legally exist and are owned or controlled by Contributor.”

Dat voorkomt de fictie dat iedere gegenereerde byte een auteursrechtelijk werk is. Als praktisch voorbeeld: OpenAI's huidige Europese voorwaarden bepalen dat, tussen OpenAI en de gebruiker, de gebruiker Output bezit en OpenAI haar eventuele rechten daarin overdraagt, maar zeggen tegelijkertijd dat Output niet uniek hoeft te zijn. Zo’n contractuele allocation zegt op zichzelf niet dat nationaal auteursrecht daadwerkelijk op elke output ontstaat.

Redelijke contributor representations zijn daarom:

- contributor heeft capacity en authority om het grant te geven;
- contributor identificeert voor zover redelijk bekend employer-/organization-owned material en third-party material;
- contributor maakt bekende licentiebeperkingen bekend;
- contributor verklaart naar beste weten niet bewust incompatibele code als eigen werk in te dienen;
- contributor geeft géén absolute garantie dat ieder byte origineel, auteursrechtelijk beschermd of vrij van alle denkbare claims is;
- vrijwillige individuele contributors geven bij voorkeur geen brede indemnity.

### Bewijs van instemming en pseudonymiteit

Een DCO `Signed-off-by`, normale PR, GitHub checkbox of agent signature is voor dit doel niet genoeg. Die kunnen provenance of workflow ondersteunen, maar drukken niet vanzelf geïnformeerde instemming uit met toekomstige proprietary sublicensing.

De beste praktijk is:

```text
private e-sign / CLA portal
        │
        ├─ legal name / organization
        ├─ signer authority
        ├─ employer declaration
        ├─ exact agreement version + hash
        ├─ timestamp + acceptance evidence
        ├─ verified email/account
        └─ GitHub identity + authorized worker IDs
                  │
                  ▼
              CLA registry
                  │
            opaque public ID
                  │
                  ▼
        GitHub status check / bot
          "DAIA rights: CLEARED"
                  │
                  ▼
            merge permitted
```

Qt laat individuele contributors bijvoorbeeld via ingelogde accountcontext de volledige CA lezen en expliciet “I AGREE” accepteren; corporate agreements worden apart door de organisatie getekend.  Harmony noemt een traditioneel getekende overeenkomst het juridisch meest conservatieve model maar laat projecten bewust ruimte voor digitale signature/conditional mechanisms.

Een elektronische ondertekening heeft in de EU niet simpelweg geen rechtsgevolg omdat zij elektronisch is; een gekwalificeerde elektronische handtekening heeft de status van een handgeschreven signature. Voor DAIA is echter niet per se een QES voor iedere hobbycontributor nodig: doel is een betrouwbare, reproduceerbare audit trail. De specifieke eisen voor een Nederlandse `akte` worden belangrijker zodra DAIA assignment of een exclusieve licence gebruikt.

**Publieke pseudonymiteit is compatibel met commerciële clearance. Volledige juridische anonimiteit is dat niet.** De buitenwereld kan bijvoorbeeld alleen zien:

| Public | Private |
|---|---|
| `github:examplepseudonym` | legal name/entity |
| agreement ref `DAIA-ICA-a83f…` | signed/e-signed agreement |
| status `cleared` | signer/employer authority |
| agreement version | email/account verification |
| covered commit/blob hashes | authorized worker identities |
| provenance flags | provider/employer details where needed |

Een contributor van wie de juridische partij intern niet kan worden vastgesteld hoort niet als **cleared** te worden weergegeven. Gebruik dan `AGPL-only`, `unverified`, `third-party` of `excluded`.

## Qualified DAIA Foundation, community guarantee, governance en opvolging

Een Nederlandse stichting past conceptueel goed bij het doel. Een stichting is een rechtspersoon met een statutair doel en zonder leden; oprichting gebeurt notarieel. De wet beperkt het stichtingsdoel ten aanzien van uitkeringen aan oprichters/bestuursleden, terwijl normale projectuitgaven en reële werkvergoeding een andere categorie zijn.

### Exacte Qualified DAIA Foundation-test

Ik zou in iedere contributor agreement dezelfde objectieve test opnemen:

| Voorwaarde | Waar primair vastleggen |
|---|---|
| Nederlandse stichting; buitenlandse opvolger alleen als functioneel gelijkwaardige missiegebonden nonprofit | CLA + statuten |
| Rechtspersoon volledig opgericht en geregistreerd | Qualification evidence |
| Statutair doel: ontwikkeling, veiligheid, beschikbaarheid, interoperability en duurzame instandhouding van DAIA | Statuten |
| Complete Official DAIA Core blijft AGPL-3.0-or-later | Statuten + CLA + licensing policy |
| Foundation-controlled Core improvements in een algemene commerciële DAIA Core-release komen ook in de AGPL Core-release | CLA + statuten/policy |
| Customer-specific proprietary modifications vallen niet automatisch onder upstreamverplichting | CLA + customer contract |
| Licensinginkomsten uitsluitend voor projectdoeleinden en redelijke reserves | Statuten + board policy |
| Geen vaste winst-/revenue-share voor founder | Statuten + compensation policy |
| Minimaal drie bestuurders; onafhankelijke meerderheid | Statuten |
| Founder heeft geen unilateral power om bestuursmeerderheid te benoemen, ontslaan of overstemmen | Statuten |
| Geen persoon beslist over eigen vergoeding | Statuten + conflict policy |
| Related-party contract alleen door niet-geconflicteerde decision-makers | Statuten + board rules |
| Foundation mag commerciële customer sublicences geven | CLA |
| Contributor commercial rights mogen niet worden verkocht, verpand of vrij overgedragen | CLA + statutes/reserved matters |
| Transfer slechts aan Qualified Successor | CLA + statuten |
| Successor moet obligations vóór transfer uitdrukkelijk accepteren | Successor accession agreement |
| Ontbinding: relevante IP/licensing rights en vermogen naar mission-compatible successor | Statuten + CLA |
| Geen successor beschikbaar: geen verkoop aan gewone commerciële onderneming | Statuten + CLA |
| Core mission clauses alleen met zware onafhankelijke governance kunnen worden gewijzigd | Statuten |
| Periodieke openbare transparantie over governance en besteding, met bescherming customer/privacydata | Policy/statuten |

Niet alles kan alleen via statuten worden gegarandeerd. Een contributor is geen vanzelfsprekende contractspartij bij de statuten. Daarom moet de community guarantee **ook een rechtstreeks contractual condition van het supplemental grant** zijn. Omgekeerd mag de agreement niet de enige laag zijn: bestuurders moeten in de stichting zelf aan dezelfde missie- en conflictstructuur gebonden zijn.

Ik zou bovendien een kleine **Mission/Rights Guardian**-functie creëren — bijvoorbeeld een raad van toezicht of zorgvuldig statutair ingericht onafhankelijk orgaan — dat goedkeuring moet geven aan uitsluitend de zwaarste reserved matters: wijziging van AGPL guarantee, disposition van aggregated rights, Qualified Successor en ontbinding. Niet aan dagelijkse ontwikkeling.

### Community guarantee

Het belangrijkste ontwerpprincipe is dat commercial licensing niet de AGPL-editie kan “uithollen”.

De definitie van **Official DAIA Core** moet daarom niet simpelweg “wat op GitHub staat” zijn, maar de project-maintained general-purpose Core die Foundation onder het DAIA-project aanbiedt. Vervolgens geldt:

> Iedere Foundation-owned of Foundation-controlled wijziging die onderdeel wordt van de algemene DAIA Core die onder een alternative commercial licence aan klanten wordt geleverd, moet tevens in de Official AGPL Core worden gepubliceerd — idealiter gelijktijdig, eventueel binnen een korte objectieve releasewindow.

Uitgesloten zijn: customer-specific private changes, unrelated customer code, credentials, customer data, independent software en third-party artifacts die de Foundation niet onder AGPL mag herlicentiëren.

PR #21 zit conceptueel al in de juiste richting: de policy draft zegt dat commercieel gelicentieerde project-owned Core changes ook in de AGPL edition terecht moeten komen en dat customer private changes niet automatisch upstream hoeven.

Ik zou de supplemental licence zelf **duurzaam en in beginsel onherroepelijk voor reeds geaccepteerde contributions** maken, maar de **bevoegdheid om nieuwe proprietary sublicences te verstrekken** conditioneren op naleving van de community guarantee.

Een goede remediestructuur:

```text
material breach
     │
written notice
     │
cure period (bijv. 60 dagen)
     │
     ├─ cured → authority continues
     │
     └─ not cured
          │
          ▼
suspension of NEW commercial sublicensing
for affected Covered Contributions
          │
existing bona-fide customer sublicences SURVIVE
          │
persistent / deliberate breach
          ▼
permanent loss of new-licensing authority
or mandatory migration to Qualified Successor
```

Dit is beter dan “bij iedere governancefout vervallen alle rights onmiddellijk”. Dat zou voor commerciële klanten een onacceptabele title risk creëren.

Reeds verleende commercial licences moeten daarom expliciet zeggen dat zij blijven bestaan voor reeds gelicentieerde versions/scope zolang de klant zelf aan zijn contract voldoet. De Foundation kan door een governancebreuk haar **toekomstige** licensing authority verliezen zonder dat een onschuldige klant plotseling zijn productieomgeving illegaal ziet worden.

Qt gebruikt een verwant stabiliteitsprincipe: een contributor mag de CA beëindigen, maar eerdere contributions blijven onder de CA vallen.

### Opvolging en ontbinding

Een Qualified Successor moet cumulatief:

1. een vergelijkbare onafhankelijke non-profit zijn;
2. DAIA's open-sourcemissie overnemen;
3. de AGPL community guarantee expliciet accepteren;
4. dezelfde revenue-purpose restriction accepteren;
5. dezelfde no-private-sale/no-pledge beperkingen accepteren;
6. de bestaande customer sublicences respecteren;
7. alle contributor agreements via een accession instrument overnemen voor zover het toepasselijke recht dat mogelijk maakt.

Als geen Qualified Successor bestaat, is de betere default **commercial licensing authority bevriezen** en foundation-owned copyright/IP uiteindelijk aan een vooraf omschreven open-source/non-profitbestemming laten toevallen, in plaats van de bundel rights bij liquidatie aan de hoogste commerciële bieder te verkopen.

Geen enkele statutaire formulering moet als letterlijk eeuwigdurend/onveranderlijk worden gepresenteerd. De reden voor deze gelaagde constructie — contributor agreements, statuten, successor accession en governance — is juist dat één latere statutenwijziging niet genoeg wordt om het model te omzeilen.

### Inkomsten, reserves en vergoeding van founder

Een stichting mag economische activiteiten hebben en personeel aannemen. KVK vermeldt expliciet dat een stichting bestuurders kan betalen, waaronder salaris wanneer een echte gezagsverhouding bestaat, waarbij het salaris moet passen bij het verrichte werk. Een stichting die werknemers krijgt, moet zich ook als werkgever behandelen.  Dat betekent niet dat iedere denkbare founderbetaling automatisch wenselijk of fiscaal neutraal is.

Voor DAIA zou de statutaire/project-purpose besteding onder meer mogen omvatten:

infrastructuur, hosting, audits, security, juridische en accountantskosten, softwareontwikkeling, contributor bounties, werknemers, contractors, release engineering, communityactiviteiten, redelijke reserves en **marktconforme maintainer-/ontwikkelvergoeding voor werkelijk verricht werk**.

De founder krijgt **geen percentage van licensing revenue, geen founder royalty en geen permanente entitlement**.

Voor een foundercontract moet gelden:

> scope of work → onafhankelijke benchmark → besluit door uitsluitend non-conflicted bestuurders → schriftelijke notulen → periodieke review.

De Foundation kan belastingplichtig worden voor bijvoorbeeld omzetbelasting, loonheffingen of vennootschapsbelasting afhankelijk van haar feitelijke activiteiten. Een stichting is niet automatisch fiscaal “belastingvrij” omdat zij nonprofit is. Dit moet vóór commerciële exploitatie door Nederlandse fiscal counsel/accountant worden gemodelleerd.

Ook moet DAIA **ANBI-status niet als gegeven aannemen**. Voor ANBI's gelden strengere regels rond de beloning van beleidsbepalers. Als een betaalde founder tevens bestuurder/beleidsbepaler zou zijn, is dit een specifiek fiscaal governancevraagstuk.

### Fiscal host

Een fiscal host kan in de pre-foundationfase nuttig zijn voor **geld**, niet voor **IP**.

Open Source Europe illustreert die scheiding expliciet: een hosted project behoudt zijn eigen intellectual property en brand terwijl de host het projectgeld beheert; hosted funds moeten voor projectdoeleinden worden gebruikt.  Fiscal hosting wordt breder juist aangeboden om donaties/grants te ontvangen en projectuitgaven te betalen zonder direct een eigen bank-/boekhoudstructuur te hebben.

Voor DAIA moeten dus vier rollen uit elkaar blijven:

| Rol | Fiscal host? |
|---|---|
| Donaties/funds ontvangen | Ja, mogelijk |
| Projectuitgaven administreren | Ja |
| DAIA-IP bezitten | **Nee, tenzij afzonderlijke en bewuste overeenkomst — niet aanbevolen** |
| Proprietary DAIA licences uitgeven | **Nee** |
| Customer software-licensor zijn | **Nee, tenzij expliciet agent van de daadwerkelijke rights holder; liever Foundation zelf** |

Een fiscal-hostovereenkomst moet expliciet zeggen dat niets daarin een assignment, copyright licence, trademark licence of authority to sublicense DAIA creëert.

## AGPL, dual licensing en vergelijking met gevestigde projecten

### Wat de AGPL-editie al toestaat

DAIA's commerciële verhaal moet uiterst zorgvuldig zijn:

> **AGPL is een commerciële open-sourcelicentie. Een onderneming hoeft niet te betalen omdat zij DAIA zakelijk gebruikt.**

De AGPL is ontworpen rond softwarevrijheden plus copyleft. Zij bevat daarnaast in §13 de netwerkbepaling voor een gemodificeerde versie waarmee gebruikers op afstand via een computernetwerk interacteren. De GNU-uitleg maakt bovendien onderscheid tussen gebruik/kopiëren binnen één organisatie en distributie naar anderen.

Praktisch:

| Situatie | AGPL-hoofdlijn |
|---|---|
| Eén rechtspersoon gebruikt ongewijzigde DAIA intern | Geen commerciële licence vereist enkel wegens zakelijk gebruik |
| Eén rechtspersoon wijzigt DAIA en werknemers gebruiken de gewijzigde service via netwerk | §13 kan een source offer aan die remote users vereisen; dat betekent niet automatisch publicatie aan de hele wereld |
| Afzonderlijke concernvennootschap krijgt copies | Niet zonder meer hetzelfde als puur intern gebruik binnen één juridische entiteit; conveyance/distributionanalyse nodig |
| Externe contractor krijgt softwarecopies | Kan conveyance/distribution zijn; contractueel label “contractor” wist AGPL-verplichtingen niet uit |
| Publieke SaaS met gewijzigde DAIA | §13 is juist daarvoor relevant: interacting users moeten toegang tot Corresponding Source van de modified version krijgen |
| OEM/embedded distributie | Gewone conveyance/copyleft- en sourceverplichtingen worden relevant |
| Proprietary product waarin covered DAIA Core zodanig wordt gecombineerd dat AGPL-copyleft problematisch is | Alternative commercial licence kan reële waarde hebben |
| Klant wil covered DAIA modifications gesloten houden | Commercial licence kan dit toestaan voor de gedefinieerde scope |

Een alternatieve licence verkoopt dus niet “het recht om DAIA commercieel te gebruiken”. Zij kan verkopen:

> het recht om specifiek geïdentificeerde DAIA Core-artifacts onder andere voorwaarden dan AGPL te reproduceren, wijzigen, integreren, distribueren en/of als proprietary onderdeel te exploiteren, inclusief afgesproken gesloten wijzigingen en OEM/distributiescenario's.

Dat is ook waarom een rights audit per commercial release nodig blijft. GNU's dual-licensing guidance benadrukt dat materiaal dat een project niet voldoende beheerst niet zomaar onder een tweede licence kan worden uitgegeven; daarvoor moeten de relevante rights daadwerkelijk beschikbaar zijn.

Een latere commercial licence trekt reeds verleende AGPL-rechten niet in. Dual licensing betekent dat dezelfde rightsholder verschillende permissions kan geven; downstream users die rechtmatig de AGPL-editie verkregen hebben, blijven die licence gebruiken volgens haar voorwaarden. De aanvullende commerciële route bestaat ernaast.

### Vergelijkingsmateriaal

| Project/model | Rechtenmodel | Relevantie voor DAIA |
|---|---|---|
| **Qt** | Contributor retains ownership; verplichte CA; commercial ecosystem; patent grant; corporate flow | Sterkste directe analogie |
| **Harmony** | Keuze assignment of broad retained-copyright licence | Goed draftingmodel voor DAIA grant |
| **FSF/GNU assignment** | Central copyright assignment bij relevante GNU-projecten | Sterk voorbeeld voor centrale enforcement/title, maar zwaarder |
| **Apache** | ICLA/CCLA; contributor authority; patentmodel; geen noodzaak tot copyright assignment | Goed voor employer/patent clauses |
| **Eclipse** | Online contributor agreement + provenance/DCO-process | Goed voor account/evidence workflow |
| **Python** | Contributor agreement/e-signprocess en behandeling toekomstige contributions | Goed operationeel precedent |
| **WordPress** | Gedistribueerd contributorcopyright onder GPL | Laat juist zien waarom “alleen OSS inbound” onvoldoende is voor DAIA's centrale relicensingdoel |
| **MariaDB/MySQL-achtige modellen** | Centrale rights mechanisms/dual-licensinghistorie | Relevant als comparator, maar niet één-op-één kopiëren |

Qt is het meest overtuigende bewijs dat DAIA niet hoeft te kiezen tussen “contributors houden hun copyright” en “een centrale actor kan commerciële gebruikers bedienen”. Qt noemt expliciet zowel open-source commitments als commercial Qt users als reden voor de CA, en laat contributor ownership intact.

Harmony is nuttig omdat het niet ideologisch één model voorschrijft: zijn templates ondersteunen zowel assignment als licensing en noemen expliciet de noodzaak om Contributions, mixed material, patents en outbound licensing afzonderlijk te definiëren.

De lesson voor DAIA is daarom niet “kopieer project X”, maar:

> **Neem Qt/Harmony als rights-model, Apache/Qt als employer/patentmodel, Eclipse/Python/Qt als acceptance-model, en de FSF als referentie voor wat DAIA bewust níét standaard hoeft te doen: central assignment voor iedere contributor.**

## Huidige DAIA-repository, provenance en PR #21

### Wat de repository nu wel en niet bewijst

De huidige PR #21 is op het onderzochte moment **open, draft en niet gemerged**. De PR zelf zegt dat het supplemental contributor grant en de interim-custody proposal uitdrukkelijk onuitgevoerde drafts zijn, dat AGPL-contributions niet stilzwijgend extra commercial rights geven en dat de PR zelf geen third-party code introduceert.

Het draft rights register zegt eveneens dat **commercial clearance nog niet is vastgesteld**, dat er geen executed supplemental grant wordt geregistreerd en — belangrijk — dat Git authorship slechts een discovery aid is en geen juridisch ownership certificate. Het document noemt drie recorded author identities in de geïnspecteerde main history en merkt zelf op dat service accounts daaronder kunnen vallen.

Dat laatste is in de history zichtbaar: commits kunnen bijvoorbeeld als authornaam `DAIA` zijn opgenomen terwijl de GitHub-accountmapping naar `joindaia` wijst. Dat is technisch metadata-bewijs, geen bewijs wie de auteursrechtelijk relevante menselijke creatieve beslissingen heeft genomen.

Er zijn daarnaast in ieder geval Dependabot-updates in de geschiedenis. PR #1 is aantoonbaar door `dependabot[bot]` geopend en betrof één changed file met één addition en één deletion voor een Actions-version bump.  Zulke service-accountmetadata maakt Dependabot niet tot een menselijke auteursrechthebbende in DAIA Core.

**Auditconclusie:** ik heb in de onderzochte publieke commit-/PR-history geen bewijs gevonden van een reeds bestaande substantiële externe menselijke contributor van DAIA Core. Dat is consistent met de door de eigenaar gegeven achtergrond, maar het is **geen bewijs van exclusieve founder ownership**. De repositorygegevens kunnen niet uitsluiten:

- AI-generated of AI-assisted material waarop geen of onzeker copyright rust;
- third-party snippets die zonder duidelijke herkomst zijn verwerkt;
- employer/contractor claims;
- code die inhoudelijk uit een upstreambron is afgeleid;
- andere provenanceproblemen die niet uit Git-authorvelden blijken.

Het juridisch verdedigbare statement is daarom:

> **“No substantive external human copyright holder has been identified in the reviewed public history, but exclusive ownership of the complete repository has not been established and commercial clearance remains subject to provenance review.”**

Dat sluit aan bij PR #21, die zelf waarschuwt dat repository/accountcontrole, Gitmetadata en AI provider terms geen complete copyright chain bewijzen.

### Third-party dependencies

De bestaande repository bevat al een dependency-license inventory. Die vermeldt onder meer MIT-, BSD-, Apache-, PSF-, MPL- en in de webdependencyset LGPL-gerelateerde packages en benadrukt expliciet dat dependencies hun eigen licences behouden en niet door de DAIA licence worden herlicentieerd.

Dat betekent dat een future “DAIA Commercial” build niet simpelweg “alles in de normale build onder onze proprietary terms” kan zeggen. Het commercial licence schedule moet onderscheid maken tussen:

> **DAIA-owned/cleared Core** — alternatief licentieerbaar;

en

> **Third-Party Components** — alleen onder hun eigen licences.

### Welke bestaande artifacts vóór commercial relicensing een provenance review nodig hebben

De audit moet op **blob/contentniveau**, niet op Git-naamniveau gebeuren. Prioriteit:

1. alle first-party coordinator-, runtime-, MCP-, worker-, security- en transportcode;
2. tests en fixtures die substantiële code bevatten;
3. scripts en deployment/configuration templates;
4. documentatie met codevoorbeelden of overgenomen tekst;
5. websitecode, illustraties, iconen, fonts en andere assets;
6. gegenereerde bestanden waarvan de generator/input/provenance relevant is;
7. protocol/schema-files die uit externe specifications kunnen zijn afgeleid;
8. alle code waarvan AI-generation of AI-assisted origin bekend is;
9. alle files waarin snippets uit Stack Overflow, GitHub, docs of andere externe bronnen kunnen zijn verwerkt;
10. iedere dependency of vendored component die daadwerkelijk in een distributable artifact wordt meegeleverd.

Een praktische release clearance is dan:

```text
exact release commit
      │
      ▼
enumerate all shipped artifacts
      │
      ├─ cleared first-party
      ├─ contributor grant cleared
      ├─ third-party / own licence
      ├─ noncopyrightable/generated — documented
      └─ unknown
                │
                ▼
       UNKNOWN blocks commercial release
       of that affected artifact
```

### AI-provenance

Voor bestaande AI-assisted files moet per relevante development workflow minstens worden geregistreerd:

* welke provider/tool waarschijnlijk is gebruikt;
* welke outputvoorwaarden op dat moment golden, voor zover reconstructeerbaar;
* of substantiële menselijke selectie, herformulering, architectuur en editing aantoonbaar zijn;
* of output herkenbare/copy-like third-party code bevat;
* of code scanners of handmatige review verdachte overeenkomsten vinden.

Het doel is niet kunstmatig te bewijzen dat ieder AI-token copyright van de founder is. Het doel is precies het tegenovergestelde: **de commercial license verkoopt alleen rechten waarvan de Foundation redelijkerwijs kan onderbouwen dat zij ze heeft**.

Apache's actuele generative-toolingbeleid is op dit punt een goede OSS-benchmark: een CLA-originalityrepresentatie ontslaat het project niet van analyse van third-party materiaal, toolvoorwaarden en de vraag of output überhaupt beschermbare menselijke auteursbijdrage bevat.

### Concrete wijzigingen aan PR #21

PR #21 is inhoudelijk een goede **policy draft**, maar nog geen contribution-rightsmechanisme. De volgende wijzigingen zijn nodig voordat het een operationeel systeem kan ondersteunen.

**Behoud** de huidige waarschuwingen dat de draft geen executed grant is, dat AGPL niet stilzwijgend commercial relicensing authority geeft en dat een fiscal host geen licensor wordt. Dat is juridisch gezond.

**Voeg Core versus Job toe.** Dit ontbreekt als centrale rights boundary. `DAIA Job Output` moet expliciet buiten alle supplemental rights vallen.

**Verander het grant van een contribution-by-contribution schedule naar een one-time future-contribution framework.** De huidige draft verlangt vóór execution “exact covered contributions (commit and file/blob hashes)”.  Dat is geschikt voor retroactieve clearance, maar niet voor DAIA's nieuwe kernvereiste. De overeenkomst moet één keer worden uitgevoerd; het register voegt daarna automatisch de exacte hashes van ieder later Accepted Core Contribution toe.

**Maak een echte Qualified Foundation-definition.** Nu staan alleen globale beginselen in de interim draft.

**Vervang “interim custody” als los concept door het gelaagde juridische mechanisme** van limited steward rights + direct future Foundation benefit + advance transfer cooperation + independent fail-safe.

**Vul het copyright grant uit.** De huidige draft noemt reproduce, modify, distribute en sublicense.  Voeg de internationale functionele equivalenten toe voor adaptation/derivative works, combining, source/object distribution, making available/communication en multi-tier proprietary sublicensing.

**Leg term/remedies daadwerkelijk vast.** De huidige draft zegt terecht dat duration, remedies, termination en treatment of existing customer sublicences nog moeten worden opgelost.  Die punten moeten vóór een eerste signature uit draftstatus.

**Voeg patent grant toe.** Niet onbeperkt, maar Qt/Apache/Harmony-achtig.

**Splits ICLA en OCLA.** Employer authorization is te belangrijk om als checkbox bij de individuele CLA te laten.

**Operationaliseer het rights register.** Het huidige register heeft al een goede basis met `unverified`, `AGPL-only`, `excluded` en `cleared`.  Voeg agreement-version, private-party record, worker mapping, source/AI provenance, patent position en exact automatic acceptance trigger toe.

**Maak de merge gate hard.** Voor een repo/component in Official Core mag een copyright-relevante externe change niet op `main` komen als de status voor de nieuwe content niet `cleared` is, tenzij maintainers bewust besluiten dat het artifact permanent AGPL-only blijft en dus uit toekomstige proprietary releases moet worden uitgesloten. Voor DAIA's doel is die uitzondering beter zeldzaam.

## Minimum safe state en verplichte counsel-review

### GitHub contribution workflow

De aanbevolen operationele flow is:

```text
Contributor registers
      │
      ├─ Individual?
      │     └─ ICLA + employment/rightsholder declaration
      │
      └─ Organization?
            └─ OCLA + authorized signer + managed contributor list
      │
      ▼
legal identity stored privately
      │
GitHub pseudonym + worker IDs bound
      │
      ▼
CLA status = ACTIVE
      │
      ▼
worker receives a Core task
      │
      ▼
PR / submission
      │
      ├─ identifies source/provenance/AI/third-party material
      │
      ▼
automated CLA + provenance status
      │
      ▼
maintainer review
      │
      ▼
formal Core acceptance / merge
      │
      ▼
immutable artifact hashes added to rights register
      │
      ├─ AGPL-3.0-or-later community right
      └─ supplemental Foundation commercial right
```

Een worker hoeft daarbij geen juridische identiteit te kennen. Hij hoeft alleen een cryptografisch of accountgebonden worker identifier te hebben dat de projectbackend privé aan een geldige participant/organization agreement koppelt.

### Safe-to-accept-external-code checklist

DAIA is naar mijn oordeel pas klaar voor de eerste externe copyright-relevante Core merge als **alle** onderstaande voorwaarden zijn bereikt:

- [ ] `DAIA Core Contribution` en `DAIA External Job Output` zijn juridisch en technisch afzonderlijk gedefinieerd.
- [ ] Er is een versieerbare Core Scope Register.
- [ ] De acceptance trigger ligt op formele Core acceptance/merge, niet op creation.
- [ ] Een Nederlandse IE-/softwarejurist heeft de ICLA en OCLA goedgekeurd.
- [ ] Die agreements dekken future qualifying accepted contributions van authorized workers.
- [ ] Supplemental grant bevat voldoende copyright-sublicensingrechten voor proprietary licensing.
- [ ] Patentclausule is definitief.
- [ ] Auteurscontractenrecht/billijke-vergoedingvraagstuk is opgelost.
- [ ] De Qualified DAIA Foundation-definitie is contractueel definitief.
- [ ] Zolang Foundation niet bestaat, is het interimmechanisme counsel-reviewed en niet slechts een “custody”-label.
- [ ] Death/incapacity/refusal/no-foundation scenario's zijn contractueel afgedekt.
- [ ] Insolventierisico van de Interim Steward is expliciet beoordeeld.
- [ ] Geen interim proprietary customer licences zijn toegestaan.
- [ ] Public pseudonym ↔ private legal party binding is operationeel.
- [ ] Employer-owned contributions kunnen via OCLA worden gecleared.
- [ ] AI/third-party provenance disclosure is onderdeel van PR-flow.
- [ ] Rights register heeft private evidence en public opaque status.
- [ ] GitHub merge check blokkeert uncleared Core material.
- [ ] Bestaande DAIA Core krijgt vóór eerste commercial release een separate provenance audit.
- [ ] Founder-owned/controlled rights krijgen vóór commercial launch een eigen Foundation grant.
- [ ] Commercial customer licence beschermt bestaande sublicences tegen latere Foundation governanceproblemen.
- [ ] Foundation zelf geeft geen licence uit voordat het **exacte release artifact** door de rights register clearance is gegaan.

### Wat DAIA in de tussentijd kan doen

**AGPL openbaar blijven:** ja. Niets in deze structuur vereist dat DAIA tijdelijk gesloten wordt. PR #21 erkent zelf dat de communityversie AGPL blijft en commercial licensing daar later naast moet bestaan.

**Issues en research aannemen:** ja. Ideeën, bugreports, factual research en discussies kunnen gewoon doorgaan. Wanneer zulke bijdragen substantiële auteursrechtelijke tekst/code opleveren die daadwerkelijk in Core wordt geïntegreerd, moet de rights clearance wel volgen.

**Tests en documentatie aannemen:** alleen met dezelfde aandacht als code zodra ze copyright-relevant en onderdeel van Official Core worden. “Het is maar een test” is geen rechtenanalyse.

**Externe Core-code vandaag mergen:** voor het doel van future dual licensing **niet verstandig zolang de agreement nog draft is**. Iedere AGPL-only merge creëert precies de latere relicensing dependency die dit ontwerp probeert te voorkomen.

**Externe Core-code na operationalisering van een counsel-approved interim CLA mergen:** **ja, juridisch plausibel**, mits de hybrid transfer/future-Foundationconstructie juridisch wordt bevestigd en de merge gate daadwerkelijk afdwingt dat alleen covered contributions binnenkomen.

**Veiligste variant:** Foundation eerst. Daarmee verdwijnen de grootste bijzondere interimrisico's — overlijden, founder-estate, insolventie en de vraag hoe een nog niet bestaande partij rechten krijgt — vrijwel geheel.

### Punten die een Nederlandse IE-/softwarejurist vóór livegang móét beoordelen

Dit zijn geen algemene “laat een jurist kijken”-punten; dit zijn de specifieke open juridische vragen waarvan de antwoorden het contractontwerp kunnen wijzigen:

1. **Auteurscontractenrecht.** Of en hoe art. 25b e.v. Auteurswet, in het bijzonder de billijke-vergoedingsregeling, toepast op een vrijwillige, royalty-free, nonexclusive supplemental commercial CLA voor natuurlijke programmeurs; en welke formulering rechtsgeldig is.

2. **Future Contributions.** Of de definitie `Accepted DAIA Core Contribution`, Core Scope Register en acceptance trigger voldoende bepaalbaar zijn om future rights zonder nieuwe signature te laten ontstaan; en of aanvullende artikel-/repositoryspecificiteit nodig is.

3. **Future copyrights en assignment fallback.** Indien een buitenlandse jurisdiction een licence niet voldoende vindt, hoe een “assignment where legally required, licence otherwise”-fallback moet worden geformuleerd zonder Nederlandse formaliteiten te breken.

4. **Aktenvereiste.** Welke e-signmethodiek volstaat als DAIA voor founder rights een exclusive field-of-use licence gebruikt en eventueel later toch copyright assignments accepteert. Art. 2 Auteurswet verlangt voor assignment en exclusieve licence een akte.

5. **Derdenbeding voor toekomstige Foundation.** Of een nog niet bestaande maar objectief gedefinieerde Qualified DAIA Foundation onder de voorgestelde formulering voldoende bepaalbaar is, wanneer zij het recht verkrijgt en welke handeling als acceptance geldt.

6. **Contractsoverneming/novation.** Welke contributor cooperation vooraf geldig kan worden gegeven en welk later transfer/accession instrument nodig is onder art. 6:159 BW en voor buitenlandse contributors.

7. **Overlijden en onbekwaamheid Interim Steward.** Of het directe Foundation right plus opvolgingsmechanisme voldoende voorkomt dat actieve medewerking van erfgenamen/bewindvoerder nodig wordt.

8. **Insolventie Interim Steward.** Dit is waarschijnlijk het belangrijkste interimrisico: welke supplemental contractual rights in een persoonlijk faillissement vallen en in hoeverre non-assignment/no-pledge clauses goederenrechtelijke werking hebben. Niet aannemen dat het woord “custodian” dit oplost.

9. **Independent rights guardian/escrow.** Welke bevoegdheden rechtsgeldig kunnen worden gegeven zonder zelf een tweede licensor of ongewenste rechthebbende te creëren.

10. **Nonexclusive-license enforcement.** In hoeverre de Foundation in Nederland en kernmarkten zelfstandig copyright infringement kan handhaven; of een aparte litigation authorization, lastgeving/volmacht, claim assignment of contributor-cooperation clause nodig is. Qt bevat om vergelijkbare redenen expliciete copyright-enforcement authority.

11. **Community-guarantee remedies.** Of “suspension of authority to issue new commercial sublicences” na cure period contractueel de beste remedie is en hoe die wordt geformuleerd zonder bestaande customer rights aan te tasten.

12. **Sublicence survival.** Zekerstellen dat commerciële customer sublicences blijven bestaan na termination, insolvency, loss of Qualified status of contributor/Foundation dispute, voor zover de customer zelf compliant is.

13. **Qualified Foundation enforcement.** Welke voorwaarden echt als contractual conditions aan het grant kunnen worden gekoppeld en welke alleen interne corporate-governanceverplichtingen zijn.

14. **Statuten.** Finaliseer met Nederlandse notaris/advocaat: projectdoel, AGPL guarantee, governance independence, reserved matters, conflict-of-interest, founder compensation, IP transfer restrictions, wijzigingsmechanisme en liquidation/successor clauses.

15. **Founder control.** Bevestig dat appointment/removal/votingmechanismen de founder niet feitelijk alsnog eenzijdige zeggenschap over de Foundation geven.

16. **Founder-to-Foundation instrument.** Keuze tussen exclusive field-of-use licence en nonexclusive licence + restrictive covenant; exacte reservaties voor AGPL en unrelated founder use.

17. **Persoonlijkheidsrechten.** Welke waivers/consents nodig en toegestaan zijn voor code, documentatie, vertalingen en modification, gezien art. 25 Auteurswet.

18. **Employer ownership.** Nederlandse art. 7-situaties plus foreign employment/work-made-for-hire doctrines; exact ICLA/OCLA-model en employer authorization.

19. **Organizational contributors.** Authority van de organizational signer en hoe de organisatie haar authorized-worker/contributor list later veilig mag aanpassen.

20. **Joint authorship.** Procedure voor contributions waar meerdere natuurlijke personen of groepsvennootschappen relevante rights bezitten.

21. **Minderjarigen.** Capacity/guardianprocedure en of DAIA deze categorie voorlopig beter AGPL-only houdt.

22. **AI-assisted material.** Provider terms per feitelijk gebruikte provider én de afzonderlijke vraag of in output juridisch auteurs-/naburige rechten ontstaan; geen provider “ownership” language als bewijs van auteursrecht behandelen. OpenAI zelf kwalificeert haar output allocation bijvoorbeeld met “to the extent permitted by applicable law” en wijst op non-uniqueness.

23. **Third-party provenance.** Contractuele disclosure standard, permissive/copyleft compatibility en release-exclusionmechanisme voor niet-relicentieerbare dependencies/snippets.

24. **Patents.** Scope van “necessarily infringed”, affiliates, multiple-tier sublicensing en defensive termination.

25. **International choice of law.** Welke buitenlandse dwingendrechtelijke copyright, employment, moral-rights en consumer rules ondanks Nederlands governing law van toepassing kunnen blijven.

26. **Privacy van CLA-register.** Rechtsgrond, bewaartermijnen, toegangsbeheer en internationale verwerking van private identity/employer/e-sign evidence. Publiceren van echte namen is daarvoor niet nodig.

27. **Fiscal host.** Zorg dat een toekomstige host uitsluitend funds/admin beheert en geen implied IP/customer licensing authority krijgt. Open Source Europe's huidige model laat zien dat fiscal hosting en IP ownership juist los kunnen worden gehouden.

28. **Foundation taxation.** BTW, vennootschapsbelasting, loonheffingen, employee/contractor classification, reserves en eventuele ANBI-ambitie afzonderlijk laten toetsen; niet uit het woord “stichting” fiscale vrijstelling afleiden.

29. **Commercial licence wording.** Laat counsel expliciet blokkeren dat marketing of customer agreements suggereren dat gewoon intern of commercieel AGPL-gebruik een betaalplicht creëert.

30. **Bestaande repository.** Vóór de eerste alternative commercial release een forensic provenance review van de exacte release uitvoeren. De huidige history geeft goede negatieve aanwijzingen over externe menselijke contributors, maar bewijst geen complete exclusive chain of title. PR #21 erkent zelf dat commercial clearance nog niet is gevestigd.

**Eindoordeel.** De doelarchitectuur hoeft niet te worden vervangen; zij moet worden **geformaliseerd en minder founder-afhankelijk gemaakt**. DAIA kan permanent AGPL-3.0-or-later blijven, contributors kunnen hun copyright behouden en een onafhankelijke Foundation kan toch voldoende duurzame rights verzamelen om proprietary alternatives te licentiëren. De doorslaggevende maatregelen zijn een one-time agreement vóór worker admission, een acceptance-trigger die alleen Official Core raakt, een zeer brede maar niet-exclusieve supplemental grant, een contractueel én statutair verankerde community guarantee, een private rights registry en een harde merge gate. Voor de pre-foundationperiode is een simpele persoonlijke “custody” onvoldoende; alleen een gelaagde constructie met direct Foundation-benefit en fail-safe transfermechanisme is serieus verdedigbaar. De juridisch sterkste route blijft echter: **richt de Qualified DAIA Foundation op vóór de eerste externe copyright-relevante Core merge; gebruik het interimmodel alleen als de praktische waarde van eerder openstellen dat extra juridische risico rechtvaardigt.**