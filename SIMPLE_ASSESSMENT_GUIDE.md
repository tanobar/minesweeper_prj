# Guida Rapida - Simple Assessment

## Descrizione
`simple_assessment.py` è uno script per testare le prestazioni delle strategie di minesweeper su diverse configurazioni di griglia.

## Come usare

### Eseguire lo script
```bash
python simple_assessment.py
```

### Modalità disponibili
Lo script ti chiederà di scegliere una delle 3 modalità:

#### **Modalità 1: Griglia piccola** 
- **Configurazione**: 10x10 con 15 mine (15% densità)
- **Strategie testate**: `random`, `backtracking`, `backtracking_advanced`, `backtracking_gac3`
- **Games**: 100 per strategia
- **Tempo stimato**: ~2-3 minuti
- **Scopo**: Confronto completo di tutte le strategie su griglia facile

#### **Modalità 2: Griglia media**
- **Configurazione**: 16x16 con 51 mine (20% densità)
- **Strategie testate**: `backtracking_advanced`, `backtracking_gac3`
- **Games**: 100 per strategia  
- **Tempo stimato**: ~15 minuti
- **Scopo**: Confronto strategie avanzate su griglia intermedia

#### **Modalità 3: Griglia expert**
- **Configurazione**: 16x30 con 99 mine (20.6% densità)
- **Strategie testate**: `backtracking_gac3` (solo la migliore)
- **Games**: 50 partite
- **Tempo stimato**: ~8 minuti
- **Scopo**: Test limite su griglia difficile

## Metriche raccolte

Per ogni strategia vengono misurate:
- **Win Rate**: percentuale di vittorie
- **Celle rivelate**: numero medio di celle scoperte per partita
- **Tempo per mossa**: tempo medio per calcolare una mossa (in millisecondi)
- **Tempo per partita**: durata media di una partita completa (in secondi)

## Output

### Output a schermo
```
============================================================
RISULTATI ASSESSMENT
============================================================
Configurazione: 10x10, 15 mine, 100 games/strategia

STRATEGIA: backtracking_advanced
  Win Rate: 87/100 (87.0%)
  Celle rivelate (media): 79.8
  Tempo per mossa (media): 9.90ms
  Tempo per partita (media): 0.25s
```

### File salvato
- **Nome**: `simple_assessment_YYYYMMDD_HHMMSS.json`
- **Formato**: JSON con tutti i dati grezzi per analisi successive
- **Posizione**: Stessa cartella dello script