## MODIFIED Requirements

### Requirement: --days parameter is optioneel
De `--days` parameter SHALL optioneel zijn. Wanneer een state file aanwezig is SHALL `--days` genegeerd worden. Wanneer geen state file aanwezig is en `--days` niet opgegeven, SHALL jirasync alle tickets ophalen.

#### Scenario: --days genegeerd bij aanwezige state file
- **WHEN** jirasync opstart met `--days 30` en een valide state file aanwezig is
- **THEN** gebruikt jirasync `last_sync` uit de state file als filter en negeert `--days`

#### Scenario: --days als bootstrap zonder state file
- **WHEN** jirasync opstart met `--days 30` en geen state file aanwezig is
- **THEN** gebruikt jirasync `updated >= -30d` als filter voor de eerste run

#### Scenario: Eerste run zonder --days
- **WHEN** jirasync opstart zonder `--days` en zonder state file
- **THEN** haalt jirasync alle tickets op van het source project zonder datumfilter
