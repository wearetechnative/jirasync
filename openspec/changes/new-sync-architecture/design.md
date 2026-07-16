## Context

Jirasync synchroniseert Jira tickets van een source board naar een target board. De huidige implementatie haalt elke run alle tickets op gefilterd op aanmaakdatum, zoekt per ticket het target-equivalent via een aparte JQL-query, en updatet altijd alle velden. Op een board van 118 tickets kost dit ~360 API calls per run, zelfs als er niets gewijzigd is. Bovendien is de paginering kapot (gebruikt `startAt`, maar de API verwacht `nextPageToken`) en worden tickets gemist die na aanmaak gewijzigd zijn.

## Goals / Non-Goals

**Goals:**
- Normale runs: alleen gewijzigde tickets verwerken via `updated >= last_sync` filter
- State file: persisteer `last_sync` timestamp en source→target key mapping
- Eerste run: volledig beide boards ophalen en issue map opbouwen
- Paginering repareren: `nextPageToken` gebruiken
- API calls minimaliseren: geen per-ticket zoekquery meer op target board

**Non-Goals:**
- Bidirectionele sync
- Detectie van verwijderde source tickets
- Wijzigingen in target board terugspiegelen naar source

## Decisions

### 1. State file locatie

**Beslissing**: State file staat naast de config file, zelfde naam met `.state.json` extensie.
Voorbeeld: `iit.json` → `iit.state.json`

**Reden**: Simpel te vinden, geen extra configuratie nodig, logisch gekoppeld aan de config instantie.

**Alternatief overwogen**: Configureerbaar pad via `--state-file` parameter — onnodige complexiteit voor dit gebruik.

### 2. State file formaat

```json
{
  "last_sync": "2026-07-16T10:15:34Z",
  "issues": {
    "TNIIT-96": {
      "target_key": "BRDGIIT-2211",
      "source_updated": "2026-07-02T14:02:50Z"
    }
  }
}
```

**Reden**: `last_sync` voor de JQL filter, `source_updated` per ticket om dubbele updates te voorkomen wanneer een ticket in het `updated` window valt maar inhoudelijk niet veranderd is ten opzichte van de vorige sync.

### 3. Eerste run bootstrap

**Beslissing**: Bij ontbrekende state file worden alle tickets van beide boards opgehaald. `--days` wordt alleen gebruikt als filter op de source fetch tijdens de eerste run (optioneel, default = geen filter = alles).

**Reden**: Issue map opbouwen vereist kennis van bestaande target tickets. Zonder dat zou elke source ticket opnieuw aangemaakt worden als duplicate.

**Alternatief overwogen**: Altijd alle target tickets doorzoeken per run — dit is precies het probleem dat we oplossen.

### 4. Sync flow normale run

```
1. Lees state file → last_sync, issue_map
2. Fetch source: updated >= last_sync  (~1 API call)
3. Voor elk gewijzigd ticket:
   a. Vergelijk source_updated met state → skip als gelijk
   b. Lookup target_key in issue_map     (0 API calls)
   c. Niet in map → maak aan, voeg toe aan map
   d. In map → update alleen gewijzigde velden
4. Schrijf state file
```

### 5. Paginering

**Beslissing**: Gebruik `nextPageToken` cursor-based paginering voor alle Jira Cloud API calls.

**Reden**: De `/rest/api/3/search/jql` endpoint retourneert `nextPageToken` en `isLast`. `startAt` wordt genegeerd door de API, waardoor de huidige loop op de eerste pagina blijft hangen.

### 6. NixOS state file schrijftoegang

**Beslissing**: State file directory moet schrijfbaar zijn. In de Elastinix service module moet `ReadWritePaths` of een dedicated `StateDirectory` toegevoegd worden.

**Reden**: De huidige systemd hardening gebruikt `ProtectSystem = "strict"` wat schrijven buiten `/tmp` en `/var` blokkeert.

## Risks / Trade-offs

- **State file kwijt** → Eerste-run modus: herindexeert alles, veilig maar duur in API calls. Mitigatie: state file in stabiele directory, backup via gewone file backup.
- **State file corrupt** → Crash bij laden. Mitigatie: JSON parse error afvangen, terugvallen op eerste-run modus.
- **Clock skew tussen source Jira en lokale machine** → Mogelijk kleine window van gemiste updates. Mitigatie: `last_sync` iets terug in de tijd zetten (bijv. 60 seconden overlap).
- **Eerste run traag** → Eenmalig, acceptabel. Geen mitigatie nodig.

## Migration Plan

1. Deploy nieuwe jirasync versie
2. Bij eerste run: state file wordt automatisch aangemaakt
3. Geen handmatige stappen vereist
4. Rollback: verwijder state file, zet oude versie terug — volgende run werkt als vanouds
