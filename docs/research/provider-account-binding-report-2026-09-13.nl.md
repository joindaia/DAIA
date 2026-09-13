<!-- Source archive: supplied research, not independently verified DAIA findings. -->

> Provenance: research supplied by the project owner on 2026-09-13. The report
> is preserved in its original Dutch wording below. Its `cite`/`filecite` markers
> refer to the originating research session; they are not resolvable references
> in this repository. Provider-specific and legal claims require source recovery
> and independent verification before implementation. No live account-binding
> test was supplied. See the English assessment for the adopted engineering decision.

# Diepgaand onderzoek: private provider-account binding als Sybil-resistance-signaal voor DAIA

## Conclusie en haalbaarheidsverdict

**Onderzoeksdatum: 13 september 2026.**

De hoofdconclusie is duidelijk: **DAIA moet provider-account binding op dit moment niet als productiefunctionaliteit implementeren voor OpenAI/Codex/ChatGPT of Anthropic/Claude.** Bij geen van beide providers is op basis van de huidige publieke, primaire documentatie een ondersteunde externe flow aangetoond waarmee DAIA een individuele provideraccount kan verifiëren, de verificatie aan een DAIA-challenge en participant key kan binden, uitsluitend een project-specifiek pseudoniem kan bewaren, én tegelijkertijd kan vermijden dat DAIA provider-access/refresh tokens, e-mailadressen of andere brede accountbevoegdheden ontvangt. OpenAI komt technisch het dichtst in de buurt, maar de bruikbare mechanismen zijn óf voor Codex zelf bedoeld, óf voor geselecteerde externe “Sign in with ChatGPT”-partners en leveren volgens de huidige publieke documentatie niet het benodigde opaque, stabiele accountsubject aan DAIA. Anthropic documenteert wel account-UUID's in Claude Code-telemetrie en OAuth voor Claude Code zelf, maar geen externe provider-signed account-attestation of OIDC relying-party-interface voor dit doel. citeturn26search0turn26search9 citeturn15view0turn13view0

Dat betekent niet dat het concept cryptografisch verkeerd is. **Het HMAC-pseudoniem is het makkelijke deel; betrouwbare invoer voor die HMAC is het onopgeloste deel.** Een participant-controlled helper die zegt `account_id=X` te hebben gezien, een lokaal gedecodeerde JWT-claim, een lokaal succesvolle CLI-login of een hash die door de worker zelf wordt aangeleverd, geeft de coordinator geen onafhankelijk verifieerbaar bewijs dat de provider dat account aan die participant heeft geauthenticeerd. Dit sluit precies aan op DAIA's huidige eigen onderzoekspositie: de repository zegt expliciet dat één sleutel niet één mens is, dat OAuth-login geen bewijs van unieke personhood is en dat public OAuth/OIDC nog design/backlog is. fileciteturn2file0 fileciteturn17file0

Mijn providerverdict is daarom:

| Provider / kandidaatpad | Wat is aantoonbaar beschikbaar? | Voldoet aan DAIA-eisen? | Verdict |
|---|---|---|---|
| OpenAI — normale Codex “Sign in with ChatGPT” | Ondersteunde browserlogin; Codex ontvangt en bewaart credentials. Pinned source leest `chatgpt_user_id`, `chatgpt_account_id` en planinformatie uit het ID-token. | **Nee.** De onderzochte claim-reader verifieert zelf geen handtekening/issuer/audience; de opgeslagen credentials zijn breed bruikbaar en mogen niet naar DAIA. | **No-go** |
| OpenAI — Codex Agent Identity | Pinned source toont een door JWKS verifieerbare RS256-JWT met vaste issuer/audience en account/user claims. | **Nee.** Audience is `codex-app-server`, bootstrap gebruikt een OpenAI access token, en de JWT bevat daarnaast agent-keymateriaal en accountclaims. Hergebruik door DAIA zou audience/intended-use omzeilen. | **No-go, maar belangrijk bewijs dat een geschikt provider-signed ontwerp technisch mogelijk is** |
| OpenAI — Sign in with ChatGPT voor externe apps | Ondersteund voor deelnemende partners; OpenAI beschrijft dit expliciet als identity-provider sign-in. | **Nog niet.** De publiek gedocumenteerde gegevens aan de app zijn naam, e-mail en profielfoto; geen stabiele opaque `sub`/account-ID met een publiek DAIA-verificatiecontract. | **Conditioneel mogelijk na expliciete provider-integratie** |
| Anthropic — Claude Code `/login` | Accountlogin/OAuth voor Claude Code; account UUID/account ID bestaan in gedocumenteerde telemetry. | **Nee.** Geen gedocumenteerde externe provider-signed accountproof/JWKS/audience-flow voor DAIA. | **No-go** |
| Anthropic — `claude setup-token` | Langlevend OAuth-token voor subscription-authenticatie en automatisering. | **Expliciet ongeschikt.** Het geeft modelgebruik/inference authority en is dus veel breder dan identiteit. | **No-go** |
| Anthropic — Claude Apps Gateway OIDC | Ondersteund OIDC tegen de **eigen bedrijfs-IdP** van de klant. | **Nee voor dit voorstel.** Bewijst corporate-IdP-identiteit, niet bezit van een Anthropic/Claude-account. | **Ander mogelijk trust-signaal, niet provider-account binding** |

OpenAI's eigen Codex-source is bijzonder instructief. Op de gepinde commit `1715e55076737158ba61d43158ede504de6d4ce1` bevat `TokenData` zowel access- en refresh-tokens als een `IdTokenInfo`; daarin worden onder andere `chatgpt_user_id` en `chatgpt_account_id` gelezen. De functie die deze gewone ChatGPT-JWT-claims leest, splitst de JWT en decodeert de payload, maar voert in die codepath geen JWS-handtekening-, issuer- of audiencecontrole uit. Dat is prima als claim-extractie binnen een reeds geauthenticeerde Codex-context, maar het is **geen zelfstandig attestation-protocol voor DAIA**. fileciteturn5file0

Dezelfde gepinde Codex-source bevat inmiddels ook een veel sterker mechanisme genaamd Agent Identity. Daar zijn `iss`, `aud`, `exp`, `account_id` en `chatgpt_user_id` onderdeel van een JWT en verifieert Codex RS256 met een opgehaalde JWKS, een vaste issuer en audience. Maar de vaste audience is expliciet `codex-app-server`; registratie van zo'n identity vereist een bearer access token; en de claimset bevat tevens `agent_private_key`. DAIA mag dus niet simpelweg “de handtekening controleren en de verkeerde audience negeren”: daarmee zou het precies het intended-service-binding dat een veilige token hoort te hebben, ondermijnen. fileciteturn10file0 fileciteturn13file0

**Aanbeveling:** implementeer hooguit de provider-onafhankelijke datastructuren, fake issuer en negatieve conformance-tests achter een feature flag die geen registratie-, reputatie-, review- of votinggedrag verandert. Een echte OpenAI- of Anthropic-adapter moet `unsupported_pending_provider_contract` blijven totdat de ontbrekende bewijsstukken hieronder bestaan. Dat is ook consistent met de huidige DAIA-status: provider diversity/reputation is design-only en OAuth/OIDC is backlog, terwijl objectieve verificatie en scheduler-isolatie al afzonderlijke mechanismen zijn. fileciteturn17file0

## Onderzoeksbasis en bewijsstatus

Ik heb vier soorten bewijs strikt uit elkaar gehouden:

| Bewijsklasse | Betekenis in dit rapport |
|---|---|
| **Gedocumenteerde garantie** | Gedrag of interface die door een provider, protocolstandaard of toepasselijke primaire juridische bron publiek als ondersteund wordt beschreven. |
| **Pinned source evidence** | Gedrag zichtbaar in een exacte huidige broncommit. Dit is sterker dan giswerk over een client, maar **geen contractuele providergarantie** dat een extern product op die interne details mag bouwen. |
| **Inferentie / ontwerpconclusie** | Een conclusie die uit meerdere bewijsstukken volgt, maar niet door de provider zelf wordt gegarandeerd. Deze is als zodanig aangeduid. |
| **Prototype** | Het door dit onderzoek aanbevolen DAIA-ontwerp. Dit is nog geen ondersteunde providerintegratie. |
| **Live evidence** | Een daadwerkelijk doorlopen providerlogin/attestation met testaccount en echte service-endpoints. **Niet verkregen in dit onderzoek**, conform de opdracht om geen accounts te registreren, geen geld uit te geven en geen persoonlijke credentials te gebruiken. |

Voor DAIA is de repository onderzocht op de huidige state van 13 september. De README op commit `81feef4bafdef48306bc6caba1ef26f90b8acabd` beschrijft DAIA als lokale reference implementation met één trusted coordinator, niet als permissionless identity/consensus-systeem. De huidige code heeft reeds admitted contributor roots, Ed25519 possession challenges, signed result envelopes, same-owner exclusion/exposure history en objectieve verificatiemechanismen, terwijl public OAuth/OIDC nog niet geïmplementeerd is. fileciteturn17file0

De DAIA Python-stack is bovendien geschikt om een credential-vrije prototypeverifier te testen zonder een echte provider aan te roepen: de gepinde `pyproject.toml` gebruikt Python 3.12+, `cryptography>=50.0.1,<51` en in de development-set `pytest>=9.0.2,<10`. Er is dus geen reden om voor het onderzoek echte OAuth-credentials te introduceren. fileciteturn19file0

Voor OpenAI is naast de officiële documentatie de huidige Codex-bron bekeken op commit `1715e55076737158ba61d43158ede504de6d4ce1`. De officiële Codex-authenticatiedocumentatie zegt dat lokale Codex-clients zowel “Sign in with ChatGPT” als API-key-login ondersteunen; bij ChatGPT-login keert de browserflow credentials terug naar Codex, en de documentatie waarschuwt dat opgeslagen `auth.json`-gegevens access tokens kunnen bevatten en als een wachtwoord moeten worden behandeld. OpenAI beschrijft daarnaast aparte access tokens voor trusted non-interactive Codex-automatisering; die vertegenwoordigen de ChatGPT-workspacegebruiker en zijn dus eveneens **autoriteitscredentials**, niet een onschuldig accountbewijs. citeturn26search0turn26search3turn26search6

Voor Anthropic is de huidige publieke `anthropics/claude-code` repository gepind op `b5932767f3acbd07da25367064827e5cb81f43de`. In die publieke repository heb ik geen inspecteerbare core-loginimplementatie gevonden die vergelijkbaar is met OpenAI's huidige `codex-rs/login`-code; de OAuth-hits in de onderzochte repo betreffen hoofdzakelijk plugins, gateways en integraties. Daarom baseert het Anthropic-authenticatieoordeel zich primair op Anthropic's officiële Claude Code-documentatie en niet op aannames over niet-gepubliceerde clientinternals. fileciteturn14file0 fileciteturn7file13

Als referentiemodel voor wat een voldoende sterke externe identity proof **zou** moeten leveren, is OpenID Connect bruikbaar: een ID Token is bedoeld als een ondertekend token over een authenticatiegebeurtenis en kent onder meer issuer, subject en audience; `nonce` is bedoeld om een authorization request aan de resulterende ID Token te relateren en replay te helpen voorkomen. Dat laat zien dat het gewenste protocol goed bekend en uitvoerbaar is. Het bewijst echter niet dat OpenAI of Anthropic DAIA vandaag zo'n relying-party-interface aanbieden. citeturn22search0turn22search2

## OpenAI: Codex en ChatGPT

De gewone Codex-login levert **interessante identifiers, maar geen bruikbaar DAIA-attestation**. In de pinned Codex-source staat een `chatgpt_user_id`, naast een `chatgpt_account_id` die in de source als organisatie/workspace-identificatie wordt beschreven. Het individuele `chatgpt_user_id` is daardoor de logischere kandidaat voor deduplicatie dan `chatgpt_account_id`: het samenklappen op workspace-ID zou immers verschillende leden van een Business/Enterprise/Edu-workspace tot één reviewidentity kunnen reduceren. De precieze levensduursemantiek van `chatgpt_user_id` als extern contract wordt in de onderzochte publieke documentatie echter niet gegarandeerd. fileciteturn5file0

Ook staat `chatgpt_plan_type` in de lokale tokenclaims, met waarden zoals free, plus, pro, business, enterprise en edu. Dat is **source evidence**, geen voldoende garantie voor “nu betaald”: een claim kan alleen iets zeggen over de toestand waartegen hij is uitgegeven, abonnementen kunnen wijzigen, en er is geen publiek DAIA-contract dat deze claim als betalingsattestation definieert. De OpenAI-gebruiksvoorwaarden beschrijven bovendien expliciet dat abonnementen kunnen worden geannuleerd, gedowngraded of geschorst. fileciteturn5file0 citeturn26search14

Daar komt een fundamentele beperking bij: **Codex-logincredentials mogen niet naar de DAIA coordinator worden gestuurd.** OpenAI zegt zelf dat browserlogin credentials aan Codex teruggeeft en dat de lokale loginopslag access tokens kan bevatten die als wachtwoord behandeld moeten worden. De Europese gebruiksvoorwaarden verbieden het delen van accountcredentials of het beschikbaar maken van de account aan anderen; de zakelijke overeenkomst verbiedt eveneens het delen van individuele logincredentials en het verhuren van accounttoegang. citeturn26search0turn26search14turn26search7

Codex Agent Identity bewijst wél dat OpenAI technisch een betere primitive heeft gebouwd. De huidige source definieert een JWT met onder andere:

```text
iss = https://chatgpt.com/codex-backend/agent-identity
aud = codex-app-server
account_id
chatgpt_user_id
iat / exp
agent_runtime_id
agent_private_key
plan_type
```

en valideert dat token met RS256, OpenAI-JWKS, exact issuer- en audiencebeleid en expiratie. De bootstrap registreert een gegenereerde agent public key bij OpenAI door een bearer access token te gebruiken; vervolgacties worden aan de agent key en een task-ID/timestamp gebonden. Dat is **sterke pinned-source evidence van provider-signed identity machinery**, maar juist de vaste `aud=codex-app-server` bewijst waarom DAIA deze JWT niet als generieke loginbadge mag recyclen. fileciteturn10file0 fileciteturn13file0

Een participant-side helper zou dit probleem niet oplossen. Zelfs wanneer de helper lokaal een authentieke Agent Identity JWT zou controleren, kan DAIA niet vertrouwen op het daarna geproduceerde `HMAC(account_id)` als de helper volledig onder controle van de participant staat. De participant kan een aangepaste helper schrijven die willekeurige account-ID's invoert. Zou de helper daarentegen de originele OpenAI-JWT naar DAIA sturen, dan worden gevoelige providerclaims/keymaterial blootgesteld én gebruikt DAIA een token dat aan een andere audience is uitgegeven. **Er is dus geen veilige middenweg door simpelweg “meer logica in de helper” te stoppen.** Dit is een protocolconclusie uit de pinned source, niet een providerstatement. fileciteturn10file0

OpenAI heeft sinds 2026 wel een veel relevanter extern product: **Sign in with ChatGPT**. OpenAI beschrijft dit expliciet als identity-provider sign-in waarmee een ChatGPT-identiteit kan worden gebruikt om een account bij een ondersteunde externe applicatie te maken, koppelen of openen. Het wordt uitgerold naar geselecteerde plugins en partners en is organisatiebeleid-afhankelijk. Volgens de huidige helpdocumentatie ontvangt de externe applicatie daarbij echter **naam, e-mailadres en eventueel profielfoto**; conversaties, memory, files, tokens en billingdata worden niet door de identity-login zelf gedeeld. citeturn26search9turn26search5

Daar zit voor DAIA precies het gat: de huidige publieke documentatie specificeert geen extern zichtbaar, opaque en stabiel user-level `sub`, geen DAIA-specifieke audience/JWKS-verificatiecontracten en geen manier waarop een third party alleen zo'n subject krijgt terwijl e-mail achterwege blijft. **Email als deduplicatiesleutel gebruiken is niet acceptabel**: zelfs een hash van e-mail blijft dictionary/enumerationgevoelig, e-mail kan wijzigen, en het voorstel verlangt expliciet dat DAIA geen e-mail verzamelt. Sign in with ChatGPT is daarom de **meest geloofwaardige toekomstige OpenAI-integratie**, maar alleen nadat OpenAI een voor DAIA geschikt partnercontract/documentatie aanbiedt, bijvoorbeeld een pairwise opaque subject of een provider-signed attestation voor de DAIA-client. citeturn26search9

De ideale OpenAI-proof zou conceptueel slechts bevatten:

```text
iss = <documented OpenAI identity issuer>
aud = <DAIA verifier client-id>
sub = <stable opaque or pairwise ChatGPT user subject>
nonce = H("DAIA-bind-v1" || challenge-id || participant-public-key)
iat / exp
```

zonder e-mail, zonder plan/billingdata en zonder enige token waarmee modellen of account-API's kunnen worden aangeroepen. Dat patroon sluit aan bij OIDC's issuer/subject/audience/nonce-model, maar **OpenAI documenteert deze specifieke DAIA-capability vandaag niet**. citeturn22search0turn22search2

Het OpenAI-oordeel is daarmee **conditioneel technisch haalbaar, operationeel nog niet ondersteund**. De concrete ontbrekende bewijsstukken zijn: een supported third-party registratiepad voor DAIA; gegarandeerde semantics en lifetime van een user-level opaque subject; exact issuer/audience/signature/JWKS-contract; nonce/challengebinding; bevestiging dat geen access/refresh/inference token aan DAIA wordt verstrekt; een PII-vrije response; en providerterms/consentregels voor dit specifieke gebruik. Een gewone `codex login` mag niet als impliciete toestemming voor dat nieuwe identity-product worden geïnterpreteerd. citeturn26search0turn26search9turn26search14

## Anthropic: Claude en Claude Code

Anthropic bevindt zich verder van een direct bruikbare externe attestation-flow. Claude Code ondersteunt volgens Anthropic verschillende authentication modes, waaronder individuele Claude.ai-accounts, Team/Enterprise, Claude Console en cloudproviders. De normale interactieve flow is bedoeld om Claude Code zelf te authenticeren; de documentatie beschrijft ook OAuth-credentials en credentialopslag voor dat doel. citeturn15view0

Er bestaan wel interessante user-level identifiers. Anthropic's Claude Code monitoringdocumentatie onderscheidt voor geauthenticeerde Claude-sessies onder meer `organization.id`, `user.account_uuid`, `user.account_id`, `user.email` en `user.id`. Daarbij is `user.id` expliciet een willekeurige installatie-ID die niet uit de Claude-accountidentiteit is afgeleid en door lokale configuratie te verwijderen opnieuw kan ontstaan. Het is daardoor ongeschikt voor deduplicatie. `user.account_uuid`/`user.account_id` zijn semantisch veel interessanter omdat zij volgens de documentatie aan de geauthenticeerde accountgebruiker worden gekoppeld. citeturn13view0turn13view2

Maar ook hier geldt het kernonderscheid: **een identifier in lokale telemetry is geen attestation**. Een participant-controlled proces kan een telemetryveld lezen en vervolgens tegen DAIA liegen over de waarde. Nergens in de onderzochte publieke Anthropic-documentatie wordt deze account UUID beschreven als een third-party-verifiable, provider-signed claim met Anthropic issuer, DAIA audience en openbare verificatiesleutels. Daarom mag `user.account_uuid` niet rechtstreeks als betrouwbare input voor `HMAC(secret, account_uuid)` worden gebruikt. citeturn13view0turn13view2

`claude setup-token` is ook geen uitweg. Anthropic documenteert dat dit een OAuth-token met lange geldigheidsduur voor CI/scripts creëert, waarmee een Claude-subscription kan worden gebruikt; het token is juist bedoeld om Claude/modelgebruik te authenticeren. Dat is precies het soort brede credential dat het voorstel uitsluit. Het naar DAIA sturen zou inference authority introduceren waar alleen identity control nodig is. citeturn15view0

Anthropic's `forceLoginOrgUUID` laat verder zien dat Claude Code in bepaalde loginpaden organisatie-lidmaatschap kan afdwingen. De documentatie waarschuwt echter zelf dat alternatieve credentialpaden anders behandeld worden; bovendien is een organisatie-ID sowieso niet hetzelfde als een individuele revieweridentiteit. Eén Team- of Enterprise-organisatie kan meerdere gebruikers/seats omvatten. Een workspace UUID als pseudoniem zou dus het tegenovergestelde probleem veroorzaken: legitiem verschillende gebruikers worden onterecht één identity. citeturn15view0

Er is nog een interessante maar andere mogelijkheid: **Claude Apps Gateway** ondersteunt OIDC tegen een door de klant beheerde corporate identity provider. Dat geeft een standaard, cryptografisch beter verificatiepad voor bijvoorbeeld “deze worker wordt door bedrijfs-IdP X als subject Y geauthenticeerd”. Maar Anthropic documenteert daarbij juist dat de gebruiker niet per se een eigen Claude.ai-account/subscription nodig heeft; de gateway beheert de upstream modeltoegang. Dit kan ooit een afzonderlijk “enterprise-identity”-signaal voor DAIA zijn, maar het bewijst **geen controle over een individuele Anthropic-provideraccount** en moet niet stiekem als equivalent worden behandeld. citeturn14view0

Ook hier is het gebruik van bestaande credentials contractueel de verkeerde richting. Anthropic's Consumer Terms verbieden het delen van accountlogin, API keys of andere accountcredentials en leggen verantwoordelijkheid voor accountgebruik bij de accountbezitter. De Commercial Terms stellen eveneens gebruiks- en accountverantwoordelijkheden en beperkingen rond reselling/bypass. Een DAIA-protocol dat gebruikers vraagt hun Claude OAuth-token te uploaden, zou daarom zowel technisch overbevoegd als slecht afgestemd op het huidige providerproduct zijn. citeturn17view1turn17view2

Het Anthropic-oordeel is daardoor **no-go onder de huidige openbare contracten**, met eenzelfde conditionele uitweg als bij OpenAI: Anthropic zou een dedicated identity-only OIDC/attestation-interface moeten aanbieden waarbij een stabiel user-level subject aan een specifiek DAIA-audience en challenge wordt gebonden en waarbij geen model-access credential wordt afgegeven. De minimaal ontbrekende evidence bestaat uit de documented subject semantics, issuer, audience, signature/JWKS, nonce/challenge semantics, een PII-minimal response en providerbevestiging dat deze derde-partij-identiteitsfunctie ondersteund gebruik is. citeturn15view0turn13view0

## Minimale privacy-architectuur en datastroom

De veiligste architectuur is niet “worker leest account-ID en HMAC't hem”, maar een **provider-authenticated event → narrowly trusted verifier → projectpseudoniem → coordinator**. De providerverificatiestap hieronder is bij beide providers momenteel de geblokkeerde schakel.

```text
 Participant / worker        DAIA coordinator       Narrow verifier          Provider
 participant keypair
        |                           |                      |                     |
        |<--- challenge C ----------|                      |                     |
        |    project, service,      |                      |                     |
        |    nonce, expiry,         |                      |                     |
        |    participant-key hash   |                      |                     |
        |                           |                      |                     |
        |-- Sign_participant(C) --->|                      |                     |
        |                           |-- reserve C -------->|                     |
        |                           |                      |                     |
        |================== provider identity authorization ==================>|
        |                           |                      |<-- signed proof -----|
        |                           |                      |   iss/aud/sub/nonce  |
        |                           |                      |                     |
        |                           |                      | verify signature,    |
        |                           |                      | issuer, audience,    |
        |                           |                      | exp, nonce, subject  |
        |                           |                      |                     |
        |                           |                      | P = HMAC(Kproject,   |
        |                           |                      |       canonical sub) |
        |                           |                      | wipe raw proof/sub   |
        |                           |                      |                     |
        |                           |<-- signed receipt ---|                     |
        |                           |    P, provider,       |                     |
        |                           |    participant key,   |                     |
        |                           |    challenge, time    |                     |
        |                           |                      |                     |
        |<--- binding status -------|                      |                     |

 Public job / GitHub: géén provider-ID, géén e-mail, géén provider token,
                      bij voorkeur zelfs géén provider-pseudoniem.
```

**De provider-signed proof is de noodzakelijke trust anchor.** De narrow verifier kan privacy verbeteren, maar kan geen waarheid creëren uit een participant assertion. Hetzelfde geldt voor lokale attestation: zonder een externe trust chain die zowel het provideraccount als de DAIA-challenge bindt, bewijst het hoogstens dat een bepaalde lokale binary iets heeft uitgevoerd. Een vrijwillige verklaring (“mijn Claude account is X”) kan auditmetadata zijn, maar levert nul cryptografische Sybil-resistance. Dit volgt uit het onderscheid tussen client assertions en provider-authenticated subject claims; OIDC is juist ontworpen rond een issuer die tegenover een specifieke client/audience voor het subject instaat. citeturn22search0turn22search2

Er zijn daarbij twee verschillende interpretaties van “DAIA verzamelt geen personal account data” die expliciet moeten worden gekozen. **Strikte variant:** geen enkele door DAIA geëxploiteerde component mag ooit het globale provider-subject zien. Dan is zelfs de narrow verifier hierboven onvoldoende en is een **provider-generated pairwise/project-scoped subject of blinded attestation** noodzakelijk. Geen van beide onderzochte providers documenteert vandaag zo'n DAIA-flow. **Opslag-minimaliserende variant:** de coordinator mag alleen het pseudoniem bewaren, terwijl een afgeschermde verifier het provider-subject transient verwerkt, HMAC't en onmiddellijk verwijdert. Dat is technisch mogelijk zodra een geschikte providerproof bestaat, maar de verifier verwerkt dan nog steeds accountgerelateerde persoonsgegevens en valt dus binnen de privacy- en securityscope. citeturn21search11turn21search14

Voor de pseudonymisatie is een eenvoudiger schema beter dan complexe accountdatabase-logica:

```text
K_project = willekeurige 256-bit geheime sleutel,
            uniek per DAIA deployment + project,
            uitsluitend aanwezig bij de verifier/KMS.

canonical_subject =
    len("DAIA/provider-account/v1") || "DAIA/provider-account/v1" ||
    len(provider)                   || provider                   ||
    len(issuer)                     || exact_issuer               ||
    len(subject_kind)               || "user"                     ||
    len(provider_subject)           || provider_subject

P = base64url_no_pad(
        HMAC-SHA-256(K_project, canonical_subject)
    )
```

De lengteprefixen moeten een vaste integerencoding gebruiken, bijvoorbeeld unsigned 32-bit big-endian, zodat `("ab","c")` nooit met `("a","bc")` kan botsen. De provider is een gesloten enum (`openai`, `anthropic`, …); `issuer` is de exact geconfigureerde vertrouwde issuer en niet een user-supplied string; en het provider-subject wordt byte-voor-byte behandeld zoals na geldige tokenverificatie ontvangen. **Geen access token, refresh token of e-mailadres komt in deze berekening voor.** Dit is een prototype-aanbeveling; HMAC-SHA-256 is hier een pseudonymization primitive, niet het ontbrekende accountbewijs.

Een random `K_project` per deployment/project is kleiner en makkelijker te redeneren dan één wereldwijde DAIA-secret. Twee onafhankelijke DAIA-deployments kunnen dezelfde provideraccount dan niet correleren, zelfs niet wanneer zij toevallig dezelfde projectnaam gebruiken. Ook verschillende projecten binnen één deployment worden onlinkbaar. Alleen de provider zelf kan uiteraard herkennen dat dezelfde account verschillende loginflows heeft gebruikt, omdat de provider de bronidentiteit kent.

De verifier hoort daarnaast een aparte signing key te hebben en een compact binding receipt te tekenen:

```text
{
  "v": 1,
  "service": "daia",
  "project_id": "...",
  "provider": "openai|anthropic",
  "provider_pseudonym": "P...",
  "participant_key_sha256": "...",
  "challenge_id": "...",
  "verified_at": "...",
  "expires_at": "...",
  "verifier_key_id": "..."
}
```

De coordinator valideert die verifierhandtekening, controleert dat `challenge_id` door hemzelf is uitgegeven en nog niet is gebruikt, en controleert dat de receipt exact aan de participant public key is gebonden die de challenge heeft ondertekend. De providerproof zelf moet vervolgens met bijvoorbeeld `nonce = H("DAIA-bind-v1" || challenge_id || participant_key_hash || random_nonce)` aan dezelfde transactie gebonden zijn. OIDC ondersteunt zo'n noncepatroon in beginsel; de huidige providerinterfaces leveren DAIA die garantie nog niet. citeturn22search0turn22search2

De partijen leren in dit model bewust verschillende dingen:

| Partij | Mag leren | Mag niet duurzaam krijgen |
|---|---|---|
| Provider | Eigen account; dat de gebruiker een DAIA-verificatie uitvoert; DAIA client/service; authorization timestamp | DAIA-contribution history hoeft niet terug naar provider |
| Narrow verifier | Provider, issuer en het ruwe subject **alleen transient**; challenge en participant-key hash | E-mail, wachtwoord, billingdata, access/refresh tokens, inference scopes, langdurige raw subject-log |
| DAIA coordinator | Projectpseudoniem, providerklasse, participant-key linkage, verification/expiry status | Raw account-ID, email, provider-ID-token, access/refresh token, provider password |
| Publieke job/GitHub | Geen van bovenstaande identiteitsdata | Zelfs het HMAC-pseudoniem hoort niet publiek te worden gemaakt |
| Andere DAIA deployment | Niets bruikbaars om te correleren | Geen gedeelde HMAC-key of globale pseudoniemen |

Het HMAC-resultaat is **pseudoniem, niet anoniem**. DAIA kan bijdragen van hetzelfde `P` binnen het project koppelen; de verifier kan bij een nieuwe geldige providerproof opnieuw hetzelfde `P` afleiden; en een gecompromitteerde HMAC-key verandert de privacy-eigenschappen. Europese privacytoezichthouders behandelen pseudonymisatie juist als vervanging van direct identificerende gegevens waarbij aanvullende informatie de koppeling nog mogelijk maakt; dit haalt gegevens niet automatisch buiten de AVG/GDPR. citeturn21search11turn21search14

Key rotation heeft een nuttige consequentie: als DAIA het ruwe provider-subject bewust niet opslaat, kan een nieuwe HMAC-key bestaande pseudoniemen **niet** offline herberekenen. Dat is geen bug maar een privacytrade-off. De schoonste rotatie is `K_project_v2` introduceren, bestaande bindingen tijdelijk onder v1 accepteren en bij de eerstvolgende provider-reverification een v2-pseudoniem aan hetzelfde interne reviewprincipal migreren. Na de migratie wordt v1 vernietigd. “Naadloze” offline rotatie vereist anders dat DAIA een recoverable/encrypted provider-subject of equivalentiële mapping bewaart, wat de privacydoelstelling verzwakt.

Bij account-relinking moet bezit van een nieuwe worker key nooit automatisch een nieuw reviewprincipal opleveren. Een worker die onder dezelfde providerproof opnieuw verifieert, krijgt dezelfde `P` en wordt aan dezelfde reviewidentity gekoppeld. Bezit van een oude participant key kan de overgang extra authenticeren; bij sleutelverlies kan fresh provider verification een recoverypad vormen, maar ook dan hoort het reviewprincipal niet “nieuw” te worden.

Erasure is principieel lastiger. **Volledige verwijdering van alle bindinginformatie betekent dat dezelfde provideraccount later opnieuw kan registreren en als onbekend kan verschijnen.** Een langdurige abuse tombstone voorkomt dat, maar is zelf blijvende pseudonieme data. Als DAIA zo'n tombstone nodig acht, moet die apart worden gedomainscheiden, minimaal zijn, een expliciete eindige bewaartermijn hebben en in privacybeleid/rechtsgrond worden verantwoord. “Verwijderen behalve onze verborgen eeuwige Sybil-hash” is geen goed privacyontwerp. AVG-erasure kent wettelijke voorwaarden en uitzonderingen; welke rechtsgrond of bewaartermijn passend is moet voor een echte service juridisch worden vastgesteld. citeturn21search11turn21search14

Een enumeration oracle moet volledig worden vermeden. De verifier hoort **nooit** een endpoint te bieden waar iemand `email@example.com` of een vermoede provideraccount-ID kan insturen om het bijbehorende DAIA-pseudoniem of “bestaat/bestaat niet” op te vragen. Alleen een succesvol provider-authenticated event mag een pseudoniem opleveren. Geen publieke reverse lookup, generieke foutmeldingen, rate limits op challenges en gescheiden verifier/HMAC-signing keys beperken de schade van probing en keycompromise.

## Dreigingsmodel, Sybil-economie en beleidsgrenzen

Accountcontrol bewijst slechts één ding: **op het verificatiemoment kon dezelfde actor een provider-authenticatie voor dat account voltooien**. Het bewijst niet dat de actor een unieke mens is, eigenaar is in juridische zin, eerlijk handelt, een onafhankelijke review produceert, dat niemand anders de account gebruikt, of dat een abonnement nog betaald is. Die beperkingen blijven bestaan zelfs wanneer het onderliggende cryptografische bewijs perfect is.

De belangrijkste aanvalsklassen zijn:

| Aanval / situatie | Wat account-binding wél doet | Wat het niet oplost |
|---|---|---|
| Tien worker keys op dezelfde provideraccount | Alle tien kunnen naar hetzelfde `P` worden teruggebracht en als één reviewprincipal tellen. | Niet detecteren hoeveel fysieke mensen de account gebruiken. |
| Eén persoon bezit tien provideraccounts | Tien verschillende `P`'s. | Geen unique-personhood. |
| Bedrijf bezit honderd seats/accounts | Kan individuele accountsubjects opleveren. | Geen bewijs van honderd onafhankelijke belanghebbenden of reviewers. |
| Gestolen account | Bewijst huidige authcontrol zolang de aanval toegang heeft. | Bewijst eigendom niet. |
| Verhuurde/gedeelde account | Bewijst dat iemand ermee kan authenticeren. | Detecteert verhuur of gedeeld gebruik niet betrouwbaar. |
| Gratis account/evaluation | Deduplicatie kan nog werken. | Geen substantiële economische Sybil-kost. |
| Betaald account | Kan acquisitiekosten verhogen als payment/entitlement afzonderlijk betrouwbaar wordt geattesteerd. | Geen personhood en geen onafhankelijkheid. |
| Abonnement stopt na verificatie | Oude accountcontrol kan blijven bestaan in DAIA-state. | Geen current-payment proof zonder fresh entitlement attestation. |
| Eén persoon gebruikt OpenAI én Anthropic | Twee verschillende providerpseudoniemen. | Mag niet worden voorgesteld als twee onafhankelijke personen. |
| Local model zonder provideraccount | Geen providerbinding. | Mag niet uit DAIA worden uitgesloten. |

Voor OpenAI kan een algemeen “verified ChatGPT account” bovendien **niet redelijk als betaald Sybil-kostsignaal worden gemodelleerd**. Codex wordt volgens de huidige OpenAI-informatie niet uitsluitend via een betaald individueel abonnement aangeboden; de huidige producttoegang omvat ook gratis/lagere planroutes. Een account-control proof zonder afzonderlijke provider-signed entitlement kan daarom een monetaire acquisition floor van praktisch **€/$0 subscription fee** hebben. Er is geen betrouwbare publieke providerbron waarmee hier bovenop een gemiddelde accountaanmaakkost kan worden gekwantificeerd, dus die moet niet worden verzonnen. citeturn4search1

Anthropic heeft een concretere zichtbare subscriptionkost voor individuele Claude Code-gebruikers: de huidige productinformatie vermeldt onder meer Claude Pro rond $20 per maand, met een lager effectief maandbedrag bij jaarlijkse betaling, en duurdere Max-tiers; Claude Code kan daarnaast via Team/Enterprise of andere deploymentvormen worden gebruikt. Dat geeft hoogstens een **lineaire acquisitiefrictie** wanneer een toekomstige verifier daadwerkelijk en vers een relevante subscriptionstatus zou attesteren. Een gewone accountproof bewijst dit niet, en `setup-token` gebruiken als bewijs is uitgesloten omdat het zelf model authority geeft. citeturn12search0turn15view0

Daarom zou ik geen formule invoeren als “Pro = 2 stemmen, Max = 5 stemmen” of “duurdere seat = hogere reputatie”. Dat monetiseert governance rechtstreeks: een vermogende aanvaller kan autoriteit inkopen terwijl onderzoekers met lokale modellen of gratis accounts structureel worden benadeeld. Economische frictie is eventueel bruikbaar als **abuse-rate signal**, niet als bewijs van waarheid of recht op meer macht.

De juiste DAIA-policy is monotonic: providerbinding kan bekende duplicaten **samenklappen**, maar mag nooit op zichzelf extra stemmen creëren. Conceptueel:

```text
worker_authentication_identity = participant public key / admitted contributor root

review_principal =
    verified_provider_binding_P     if such a binding exists
    existing_contributor_principal  otherwise

rule:
    max 1 counted review per known review_principal
```

Daar hoort een belangrijke caveat bij: een malicious participant kan anders eenvoudig besluiten zijn tweede worker **niet** te binden. Providerbinding is daarom alleen een gedeeltelijk negatief signaal: “deze twee zijn zeker niet onafhankelijk op accountniveau” is waardevol; “deze twee hebben verschillende of geen binding, dus zijn onafhankelijk” is ongeldig. DAIA's huidige repository onderkent al hetzelfde basale probleem: afzonderlijke contributor roots of OAuth-logins zijn geen bewijs van verschillende mensen. fileciteturn2file0 fileciteturn17file0

Dat leidt tot de juiste interpretatie voor review:

```text
zelfde verified provider-account
    => MOET als één account-level reviewidentity tellen

verschillende verified accounts
    => MAG NIET worden geïnterpreteerd als bewijs van onafhankelijkheid

geen providerbinding / local model
    => blijft ondersteunde contributorcategorie

provider reputation / paid tier
    => geeft geen extra privilege voor secrets, network, writes of deployment
```

Productie, review, reputatie en privileged execution moeten dus orthogonaal blijven. Een worker kan uitstekende productieoutput leveren zonder provideraccount. Een providerbinding kan helpen voorkomen dat meerdere keys van dezelfde bekende account een reviewquorum vullen. Objectieve verification receipts blijven sterker bewijs over het artifact dan accountmetadata. En geen hoeveelheid accountreputatie behoort netwerktoegang, repository writes, deploymentmacht, persoonlijke secrets of een ruimere execution sandbox te verlenen. Dat is in lijn met DAIA's huidige evidence-gated architectuur, waarin promotion en execution authority al afzonderlijk worden behandeld. fileciteturn17file0 fileciteturn2file0

Voor één persoon die zowel OpenAI als Anthropic gebruikt, moet **geen covert cross-provider identity matching** plaatsvinden. E-mail vergelijken, e-mail hashes vergelijken, browserfingerprints gebruiken of provideraccounts probabilistisch clusteren zou de privacydoelstelling ondergraven en creëert bovendien vals-positieve identityclaims. De namespaces horen bewust onafhankelijk te blijven:

```text
P_openai    = HMAC(K_project, "openai"    || issuer_A || sub_A)
P_anthropic = HMAC(K_project, "anthropic" || issuer_B || sub_B)
```

Dat betekent bewust dat dezelfde persoon twee account-level signalen kan bezitten. Het is beter die beperking eerlijk te accepteren dan een verborgen universal-person identifier te bouwen.

Voor rented/stolen account-markten of de empirische kans dat één aanvaller meerdere seats/accounts heeft, heb ik **geen primaire providerdata gevonden die een betrouwbare kostenverdeling ondersteunt**. Een numeriek “Sybil cost = $X per identiteit” zou daarom schijnprecisie zijn. De enige verantwoord kwantificeerbare bedragen zijn gepubliceerde abonnementsprijzen of €/$0 voor accountcategorieën waarvoor geen betaald abonnement nodig is; overige acquisitie-, diefstal- en rentalcosts moeten als onbekend worden gemodelleerd. citeturn12search0turn4search1

## Voorwaarden, privacy en governance

De servicevoorwaarden versterken de technische aanbeveling om nooit bestaande CLI-credentials als identity bridge te gebruiken. OpenAI's Europese voorwaarden zeggen dat gebruikers hun accountcredentials niet mogen delen of hun account aan anderen beschikbaar mogen stellen en verbieden het omzeilen van rate limits, restrictions en protective measures. OpenAI's zakelijke overeenkomst verbiedt het delen van individuele accountcredentials en het verhuren van accounttoegang. De officiële Codex-documentatie behandelt opgeslagen ChatGPT-authenticatie bovendien zelf als gevoelig credentialmateriaal. citeturn26search14turn26search7turn26search0

Anthropic hanteert overeenkomstige grenzen rond accountcredentials; tegelijkertijd is `claude setup-token` expliciet ontworpen om geautomatiseerd Claudegebruik te authenticeren. Dat maakt zo'n token niet tot een geschikte “proof of subscription” voor een derde partij. **Least privilege betekent hier: DAIA moet een speciaal identity-product gebruiken of helemaal geen providerbinding doen.** citeturn17view1turn17view2turn15view0

Gewone toestemming voor `codex login` of `claude /login` is ook niet hetzelfde als toestemming om die identiteit in DAIA als persistent anti-abuse signal te gebruiken. Voor OpenAI bestaat inmiddels een expliciet extern “Sign in with ChatGPT”-consentscherm; OpenAI zegt dat organisaties dit via approved-applicationbeleid kunnen toestaan of blokkeren. Dat ondersteunt juist het idee dat een DAIA-integratie via een provider-approved application moet lopen en niet via stille inspectie van `~/.codex/auth.json`. citeturn26search9turn26search0

Voor productie zijn daarom minimaal twee verschillende soorten toestemming/bevestiging nodig. **Participant-side:** expliciete opt-in waarbij DAIA uitlegt dat de providerlogin uitsluitend voor account-level deduplicatie wordt gebruikt, wat DAIA/verifier/provider leren, dat dit geen personhoodbewijs is, hoe lang de binding wordt bewaard en hoe removal/reverification werkt. **Provider-side:** een ondersteunde application/integration-status en documentatie/contract waaruit blijkt dat het provider identity-mechanisme voor deze third-party purpose mag worden gebruikt. Die providerbevestiging ontbreekt momenteel voor de gewenste minimale flow bij beide providers. citeturn26search9turn15view0

AVG-technisch moet DAIA een HMAC-providerpseudoniem voorzichtig behandelen als **pseudonieme persoonsgegevens**, niet als anonymous data. De identifier maakt een terugkerende participant binnen het project juist doelbewust “singled out” en de verifier kan bij een volgende geldige providerlogin dezelfde waarde opnieuw afleiden. De officiële Europese/regulatorische bronnen maken duidelijk dat pseudonymisatie persoonsgegevens niet automatisch uit de gegevensbeschermingsregels haalt wanneer koppeling met aanvullende informatie mogelijk blijft. citeturn21search11turn21search14

Dat impliceert in een echte deployment ten minste data-minimalisatie, purpose limitation, bewaartermijnen, toegangscontrole, key-compromise procedures, een duidelijk privacy notice en een expliciete beslissing over de toepasselijke AVG-rechtsgrond. Ik zou **niet automatisch “consent” als juridische Article 6-grondslag claimen**: de productmatige opt-in kan noodzakelijk zijn voor transparantie en providerautorisatie terwijl de formele rechtsgrond afhankelijk is van de uiteindelijke dienstrelatie, governance en deployment. Dat is een juridisch ontwerpbesluit waarvoor de concrete DAIA-operatie moet worden beoordeeld, niet iets wat een cryptografisch schema kan vaststellen. citeturn21search11turn21search14

Ook moeten logging en observability speciaal worden ontworpen. De narrow verifier mag geen standaard HTTP body logging, token dumps, Sentry payloads of debug traces met raw provider subject/ID-token introduceren. De coordinator hoort alleen `binding_ref`/pseudoniem en operationele timestamps te zien. De HMAC-key en verifier signing key horen afzonderlijk roteerbaar en niet via application logs/export/backups blootgesteld te worden.

Bij key compromise verschillen de gevolgen. Diefstal van de **receipt-signing key** laat een aanvaller valse “verified binding”-receipts minten en is dus een integrity-incident. Diefstal van `K_project` laat een aanvaller pseudoniemen herberekenen wanneer hij kandidaat-provider-subjects kan verkrijgen en is primair een privacy/linkability-incident. Beide moeten daarom aparte key IDs, rotation en revocation hebben. De projectkey mag nooit in browser/clientsoftware of GitHub terechtkomen.

De coordinator moet verder geen API hebben als:

```text
GET /provider-binding/openai/<account-id>
POST /lookup-email-hash
GET /is-bound?pseudonym=...
```

Externe callers zouden daarmee een enumeration/linkability-service krijgen. Interne schedulerqueries horen op een random database `binding_ref` of het intern opgeslagen pseudoniem te werken, niet op externally queryable provideridentifiers.

## Credential-vrij testharnas en acceptatieplan

DAIA kan vrijwel het gehele eigen protocol **nu al testen zonder één echte OpenAI- of Anthropic-account**. De huidige repository heeft `cryptography` en `pytest` al gepind, dus een fake provider kan tijdens tests een tijdelijke RSA- of Ed25519-keypair genereren, een JWKS-equivalent publiceren en synthetische claims ondertekenen. Dat test precies de fouten die een echte adapter later moet afwijzen zonder providercredentials te verzamelen. fileciteturn19file0

Het minimale testharnas zou uit drie test-only componenten bestaan:

```text
tests/provider_binding/
    fake_issuer.py
        - generated signing key
        - fake JWKS
        - issue_claim(...)

    fake_verifier.py
        - strict issuer allowlist
        - audience check
        - signature/JWK check
        - iat/exp/nonce check
        - challenge consumption
        - participant-key binding
        - HMAC pseudonym
        - signed verifier receipt

    test_provider_binding.py
        - positive + all negative/replay/dedup cases
```

De fake issuer moet **geen echte providernamen of productie-endpoints vertrouwen**. Gebruik bijvoorbeeld:

```text
issuer       = https://issuer.daia.invalid/openai-test
audience     = daia-binding-test
subject A    = synthetic-account-A
subject B    = synthetic-account-B
organization = synthetic-workspace-1
```

Zo kan er nooit per ongeluk een echte OAuth-flow, persoonlijke credential of productieaccount in de test terechtkomen.

De acceptatiematrix moet minimaal het volgende afdwingen:

| Test | Manipulatie | Verwacht resultaat |
|---|---|---|
| Geldige proof | Correcte signer, issuer, audience, nonce, expiry, subject en participant key | **Accept** |
| Fabricated claim | Helper levert willekeurig JSON/account-ID zonder trusted provider signature | **Reject** |
| Self-signed fake provider | Claim correct gevormd maar key niet in trusted JWKS | **Reject** |
| Foreign issuer | Geldige signature van andere issuer | **Reject** |
| Foreign audience | Geldige proof voor `codex-app-server`, `claude-code` of andere service | **Reject** |
| Expired proof | `exp < now` | **Reject** |
| Future/not-yet-valid proof | Onredelijke `iat`/eventuele `nbf` | **Reject** |
| Replay | Zelfde `challenge_id`/nonce tweemaal | Eerste eventueel accept, tweede **reject** |
| Swapped participant key | Providerproof hoort bij challenge A, receipt probeert key B | **Reject** |
| Wrong project/service | Zelfde authproof opnieuw gebruikt onder ander project/service | **Reject** |
| Forged helper | Lokale helper beweert succesvolle login maar heeft geen verifier signature | **Reject** |
| Verifier-key compromise simulation | Receipt onder ingetrokken/oude key | **Reject** na revocation |
| Provider-key rotation | Nieuwe trusted `kid`; bounded JWKS refresh | **Accept** alleen na trusted key update |
| Unknown `kid` | Niet in trusted JWKS, ook niet na bounded refresh | **Reject** |
| Twee workers, één subject | Zelfde verified subject, verschillende participant keys | Zelfde `P`; **één reviewprincipal** |
| Twee onafhankelijke subjects | Zelfde issuer/project, subject A en B | Verschillende `P` |
| Zelfde workspace, andere users | Zelfde organization-ID, verschillende user subjects | Verschillende `P`; workspace mag niet de useridentity vervangen |
| Zelfde subject, ander project | Zelfde provideraccount | Ander `P` |
| Zelfde subject, andere deployment | Onafhankelijke `K_project` | Ander `P` |
| Account removal | Binding gemarkeerd removed | Niet meer eligible; geen automatische stem |
| Fresh recovery | Nieuwe participant key + fresh providerproof met hetzelfde subject | Zelfde logical reviewprincipal |
| Erasure zonder tombstone | Volledige verwijdering gevolgd door nieuwe verificatie | Test documenteert dat re-registration niet detecteerbaar is |
| Erasure mét tijdelijke tombstone | Re-registration binnen vastgestelde retention | Wordt volgens expliciete abuse-policy herkend |
| OpenAI + Anthropic synthetic account | Zelfde gesimuleerde persoon bij twee issuers | **Geen cross-provider koppeling** |

De foreign-audience-test is vooral belangrijk voor OpenAI: een echte, geldig door OpenAI ondertekende Agent Identity JWT met `aud=codex-app-server` moet in een toekomstige DAIA-verifier **falen**, niet slagen. Dat beschermt tegen de verleiding om “signed by provider” te verwarren met “issued for this service”. De huidige OpenAI-source demonstreert precies deze issuer/audience-validatie in zijn eigen Agent Identity-verifier. fileciteturn10file0

De forged-helper-test is even fundamenteel: het resultaat van een local executable, browser extension, MCP tool of contributor helper mag nooit voldoende zijn om `verified=true` te zetten. De helper kan de UX orkestreren en de participant key beheren; **alle assurance moet uiteindelijk teruglopen naar een provider-signed proof of een narrow verifier die zo'n proof zelfstandig heeft gevalideerd**.

Voordat een provideradapter uit testmodus mag komen, moet hij deze volledige gate passeren:

| Gate | Vereiste | OpenAI nu | Anthropic nu |
|---|---|---:|---:|
| Supported external identity flow | Provider documenteert deze toepassing | ⚠️ Alleen geselecteerde Sign in with ChatGPT partners, contract voor DAIA ontbreekt | ❌ |
| Stable individual subject | User-level, opaque, stabiel en gedocumenteerd | ❌ Publiek extern contract ontbreekt | ❌ Attestable extern contract ontbreekt |
| Cryptographic verification | Issuer + signature/JWKS + exact audience | ⚠️ Bestaat intern in Agent Identity, maar verkeerde audience; externe flow onvoldoende gedocumenteerd | ❌ voor Claude-accountbinding |
| DAIA challenge binding | Nonce/challenge kan aan participant key/service worden gekoppeld | ❌ Niet aangetoond voor gewenste external flow | ❌ |
| No provider authority | Geen inference/account access token bij DAIA | ❌ Codexcredentials voldoen niet; extern identityproduct moet worden bevestigd | ❌ Claude OAuth/setup-token voldoet niet |
| No required email/name storage | Alleen opaque subject naar verifier | ❌ Huidige Sign in with ChatGPT documenteert naam/e-mail/profielfoto | ❌ Geen geschikte flow |
| Terms/admin support | Provider-supported app + gebruikers/admin consent | ⚠️ Partnermechanisme bestaat maar DAIA-status niet aangetoond | ❌ voor deze use-case |
| Credential-free synthetic conformance | Alle bovenstaande negatieve tests | **Kan nu worden gebouwd** | **Kan nu worden gebouwd** |
| Live dedicated-provider test | Testaccount, echte keys/endpoints, privacycheck | **Niet uitgevoerd** | **Niet uitgevoerd** |

OpenAI's externe Sign in with ChatGPT maakt die provider uiteindelijk plausibeler dan Anthropic voor een pilot: OpenAI heeft inmiddels expliciet een identity-providerproduct voor ondersteunde externe applicaties. Maar het huidige gedocumenteerde outputcontract deelt PII en specificeert niet het DAIA-benodigde opaque user subject. Dat is een wezenlijke missing-evidence gate, geen detail dat DAIA zelf moet improviseren. citeturn26search9

Voor Anthropic ontbreekt zelfs die externe Claude-account-IdP-laag in de onderzochte documentatie. Hun OIDC gateway is bruikbaar met een klant-IdP, maar dat is een ander identity domain; hun Claude OAuth-credentials zijn voor Claudegebruik zelf. Ook daar moet DAIA dus wachten op een expliciet ondersteunde identity/attestation-interface in plaats van lokale account UUID's of OAuth-tokens te hergebruiken. citeturn14view0turn15view0

**Eindbesluit voor de research proposal:** behoud provider-account binding als mogelijke toekomstige **abuse-resistance signal**, maar verander nu geen admission-, consent-, reputation- of votingregel. Implementeer desgewenst alleen de provider-neutrale challenge/receipt/HMAC-interface, project-scoping en synthetic conformance suite. Zet zowel `openai` als `anthropic` productieadapters op hard fail totdat een provider-supported, identity-only en DAIA-bound bewijsflow aantoonbaar bestaat. Zodra die bestaat, is de juiste regel niet “één account = één mens”, maar veel beperkter en verdedigbaarder: **“workers die aantoonbaar dezelfde provideraccount gebruiken mogen niet als extra onafhankelijke reviewers tellen; verschillende accounts bewijzen niets over menselijke of organisatorische onafhankelijkheid.”** Dat past bij DAIA's huidige ontwerpfilosofie dat identitysignalen objective verification en execution boundaries aanvullen, nooit vervangen. fileciteturn2file0 fileciteturn17file0
