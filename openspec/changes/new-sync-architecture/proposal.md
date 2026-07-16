## Why

De huidige jirasync implementatie is inefficiënt: elke run haalt alle tickets op gefilterd op aanmaakdatum (`created`), zoekt per ticket het bijbehorende target-ticket via een aparte API-call, en update altijd alle velden ongeacht of er iets gewijzigd is. Dit resulteert in honderden onnodige API-calls per run, mist tickets die na aanmaak gewijzigd zijn, en heeft een kapotte paginering (`startAt` i.p.v. `nextPageToken`).

## What Changes

- **BREAKING**: `--days` parameter wordt optioneel; bij aanwezige state file wordt hij genegeerd
- Filteren op `updated` in plaats van `created` in de JQL-query
- Introductie van een state file (`{instance}.json`) die `last_sync` timestamp en source→target key mapping bijhoudt
- Eerste run: beide boards volledig ophalen, issue map opbouwen uit target ticket titles
- Normale run: alleen tickets ophalen met `updated >= last_sync` (~1 API call), target key opzoeken uit state file (0 API calls per ticket)
- Paginering hersteld: gebruik `nextPageToken` in plaats van `startAt`
- Update alleen velden die daadwerkelijk gewijzigd zijn

## Capabilities

### New Capabilities

- `state-management`: Persistente state file met `last_sync` timestamp en issue map (source key → target key), zodat incrementele sync mogelijk is zonder per-ticket zoekqueries

### Modified Capabilities

- `jira-sync`: Sync-logica wijzigt fundamenteel: eerste run vs. incrementele run, filteren op `updated`, geen per-ticket zoekquery meer
- `cli`: `--days` wordt optioneel en alleen gebruikt als bootstrap bij ontbrekende state file

## Impact

- `jirasync.py`: volledige herschrijving van `get_remote_issues` en `sync_issues_to_local`
- Nieuwe state file locatie nodig (configureerbaar of default naast config file)
- NixOS service module: `ProtectSystem = "strict"` vereist schrijftoegang tot state file directory
- Elastinix service module: eventueel nieuw `stateDir` optie nodig
