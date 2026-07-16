## 1. State file module

- [x] 1.1 Implementeer `load_state(config_file)` — leest `<config-basename>.state.json`, geeft dict terug of `None` bij niet-aanwezige/corrupte file
- [x] 1.2 Implementeer `save_state(config_file, last_sync, issues)` — schrijft state file atomair weg
- [x] 1.3 Voeg `source_updated` tracking toe aan issue entries in de state

## 2. Paginering repareren

- [x] 2.1 Vervang `startAt`-gebaseerde paginering door `nextPageToken` cursor in alle fetch-functies
- [x] 2.2 Verwijder de `approximate-count` API call (niet meer nodig)

## 3. Source fetch aanpassen

- [x] 3.1 Vervang `created >= -{days}d` door `updated >= {last_sync}` in de JQL query voor incrementele runs
- [x] 3.2 Implementeer eerste-run modus: geen datumfilter wanneer geen state file aanwezig
- [x] 3.3 Handhaaf `--days` als optionele bootstrap filter voor eerste run

## 4. Eerste-run issue map opbouwen

- [x] 4.1 Implementeer `fetch_all_target_issues(config, auth, headers)` — haalt alle target tickets op met `nextPageToken` paginering
- [x] 4.2 Implementeer `build_issue_map_from_target(issues)` — extraheert `[SOURCE-KEY]` prefix uit summaries en bouwt mapping op
- [x] 4.3 Roep deze functies aan bij eerste-run modus vóór de sync-loop

## 5. Sync-loop herschrijven

- [x] 5.1 Vervang per-ticket JQL zoekquery door lookup in issue map
- [x] 5.2 Sla tickets over waarvan `source_updated` in state gelijk is aan `updated` van het opgehaalde ticket
- [x] 5.3 Update `source_updated` in de issue map na elke succesvolle sync van een ticket
- [x] 5.4 Voeg nieuwe tickets toe aan de issue map na aanmaken op target board

## 6. CLI aanpassen

- [x] 6.1 Maak `--days` optioneel (geen `required=True`, geen default)
- [x] 6.2 Log een waarschuwing wanneer `--days` opgegeven is maar genegeerd wordt vanwege aanwezige state file

## 7. NixOS / Elastinix

- [x] 7.1 Voeg `ReadWritePaths` toe aan de systemd service in `service-jirasync.nix` voor de directory van de state file
- [ ] 7.2 Test dat de state file succesvol geschreven wordt onder de systemd hardening

## 8. Verificatie

- [x] 8.1 Test eerste run: beide boards ophalen, issue map opbouwen, state file aangemaakt
- [x] 8.2 Test incrementele run: alleen gewijzigde tickets verwerkt, state file bijgewerkt
- [x] 8.3 Test corrupt/ontbrekende state file: terugval naar eerste-run modus zonder crash
- [x] 8.4 Verifieer paginering met een query die meer dan 100 resultaten geeft (`nextPageToken`)
