## ADDED Requirements

### Requirement: State file aanmaken na succesvolle sync
Na elke succesvolle sync run SHALL jirasync een state file wegschrijven naast de config file (zelfde naam, extensie `.state.json`) met daarin de `last_sync` timestamp en de volledige issue map.

#### Scenario: State file aangemaakt na eerste run
- **WHEN** jirasync succesvol een eerste run voltooit zonder bestaande state file
- **THEN** schrijft jirasync `<config-basename>.state.json` met `last_sync` (ISO 8601 UTC) en alle gesyncte issues met hun `target_key` en `source_updated`

#### Scenario: State file bijgewerkt na incrementele run
- **WHEN** jirasync succesvol een incrementele run voltooit met bestaande state file
- **THEN** overschrijft jirasync de state file met bijgewerkte `last_sync` en bijgewerkte issue entries voor alle verwerkte tickets

### Requirement: State file inlezen bij opstart
Bij opstart SHALL jirasync proberen de state file te lezen en bij succes de incrementele modus activeren.

#### Scenario: State file bestaat en is valide
- **WHEN** jirasync opstart en een valide state file aanwezig is
- **THEN** activeert jirasync incrementele modus met `last_sync` uit de state file

#### Scenario: State file bestaat niet
- **WHEN** jirasync opstart en geen state file aanwezig is
- **THEN** activeert jirasync eerste-run modus en haalt alle tickets op van beide boards

#### Scenario: State file is corrupt of onleesbaar
- **WHEN** jirasync opstart en de state file niet parseerbaar is als JSON
- **THEN** logt jirasync een waarschuwing en activeert eerste-run modus

### Requirement: Issue map bijhouden
De state file SHALL voor elk gesynchroniseerd ticket de source key, target key en `source_updated` timestamp bevatten.

#### Scenario: Nieuw ticket toegevoegd aan issue map
- **WHEN** jirasync een nieuw ticket aanmaakt op het target board
- **THEN** voegt jirasync de source key toe aan de issue map met de bijbehorende target key en `source_updated`

#### Scenario: Bestaand ticket bijgewerkt in issue map
- **WHEN** jirasync een bestaand ticket synchroniseert met gewijzigde velden
- **THEN** werkt jirasync `source_updated` bij in de issue map entry voor dat ticket
