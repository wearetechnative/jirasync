## MODIFIED Requirements

### Requirement: Source tickets ophalen
Jirasync SHALL source tickets ophalen gefilterd op `updated` datum (niet `created`) en SHALL `nextPageToken` gebruiken voor paginering.

#### Scenario: Incrementele run haalt alleen gewijzigde tickets op
- **WHEN** een state file aanwezig is met `last_sync`
- **THEN** fetcht jirasync alleen tickets met `updated >= last_sync` via JQL

#### Scenario: Eerste run haalt alle tickets op
- **WHEN** geen state file aanwezig is en `--days` niet opgegeven
- **THEN** fetcht jirasync alle tickets van het source project zonder datumfilter

#### Scenario: Eerste run met --days bootstrap
- **WHEN** geen state file aanwezig is en `--days N` opgegeven
- **THEN** fetcht jirasync tickets met `updated >= -{N}d`

#### Scenario: Paginering via nextPageToken
- **WHEN** een API response `isLast: false` retourneert
- **THEN** gebruikt jirasync de `nextPageToken` uit de response voor de volgende pagina

### Requirement: Target ticket opzoeken zonder zoekquery
Jirasync SHALL het bijbehorende target ticket opzoeken via de issue map in de state file, zonder een JQL zoekquery per ticket.

#### Scenario: Target key gevonden in issue map
- **WHEN** een source ticket key aanwezig is in de issue map
- **THEN** gebruikt jirasync direct de bijbehorende target key zonder API call

#### Scenario: Target key niet in issue map
- **WHEN** een source ticket key niet aanwezig is in de issue map
- **THEN** maakt jirasync een nieuw ticket aan op het target board en voegt de mapping toe

### Requirement: Alleen gewijzigde velden updaten
Jirasync SHALL alleen een update-request sturen wanneer de veldwaarden daadwerkelijk afwijken van de bekende vorige staat.

#### Scenario: Ticket niet gewijzigd since last sync
- **WHEN** `source_updated` in de state file gelijk is aan `updated` van het opgehaalde ticket
- **THEN** slaat jirasync dit ticket over zonder API calls naar het target board

#### Scenario: Ticket gewijzigd since last sync
- **WHEN** `source_updated` in de state file ouder is dan `updated` van het opgehaalde ticket
- **THEN** synchroniseert jirasync de gewijzigde velden naar het target board

### Requirement: Eerste-run issue map opbouwen
Bij een eerste run SHALL jirasync alle bestaande target tickets ophalen en de issue map opbouwen op basis van de `[SOURCE-KEY]` prefix in de ticket summary.

#### Scenario: Bestaande target tickets herkend
- **WHEN** een target ticket een summary heeft die begint met `[TNIIT-NNN]`
- **THEN** voegt jirasync de mapping `TNIIT-NNN → target_key` toe aan de issue map

#### Scenario: Target ticket zonder herkend prefix
- **WHEN** een target ticket geen `[SOURCE-KEY]` prefix heeft in de summary
- **THEN** slaat jirasync dit ticket over bij het opbouwen van de issue map
