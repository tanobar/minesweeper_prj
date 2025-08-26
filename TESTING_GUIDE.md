# Guida ai Test - Minesweeper Strategies

Questa guida spiega come testare e valutare le strategie di risoluzione del minesweeper implementate nel progetto.

## Cosa fa il sistema

Il progetto implementa **5 strategie diverse** per risolvere automaticamente il gioco del minesweeper:

1. **`random`** - Scelte casuali (strategia baseline)
2. **`backtracking`** - Risoluzione CSP base 
3. **`backtracking_advanced`** - CSP con euristiche
4. **`backtracking_gac3`** - CSP + euristiche + GAC3
5. **`backtracking_pb`** - CSP completo + PB

## Come usare i test

### Test Rapido (verifica funzionamento)

Per verificare che tutto funzioni correttamente:

```bash
python quick_test.py
```

**Cosa fa:**
- Testa una singola partita per ogni strategia
- Esegue un mini-assessment con 3 partite per strategia  
- Verifica che tutti gli import e le dipendenze funzionino
- **Durata:** ~10 secondi

Per raccogliere dati statistici seri:

#### Assessment Veloce (~2 minuti)
```bash
python assessment.py --mode quick
```
- 1 configurazione griglia (8x8, 10 mine)
- 50 partite per strategia
- **Total:** 250 partite

#### Assessment Medio (~7 minuti)  
```bash
python assessment.py --mode medium
```
- 2 configurazioni griglia (8x8, 10x10)
- 50 partite per strategia per configurazione
- **Total:** 500 partite

#### Assessment Completo (~20 minuti (a me (Tano) ci mette poco))
```bash
python assessment.py --mode full
```
- 3 configurazioni griglia (8x8, 10x10, 12x12)
- 50 partite per strategia per configurazione  
- **Total:** 750 partite

#### Personalizzazione
```bash
# Più partite per risultati più stabili
python assessment.py --mode medium --games 100

# Cartella personalizzata per i risultati
python assessment.py --mode quick --results-dir "my_tests"
```

##  Cosa aspettarsi come output

### Durante l'esecuzione

```
 Modalità: quick
 Strategie: random, backtracking, backtracking_advanced, backtracking_gac3, backtracking_pb
 Configurazioni: 1

 Griglia 8x8 con 10 mine
    [1/5] Strategia: random
     Win rate: 2/50 (4.0%)
    [2/5] Strategia: backtracking
     Win rate: 21/50 (42.0%)
  [...]

  Assessment completato in 1.8 minuti
```

### File di output salvati in `results/`

##  Metriche raccolte

- **Win Rate:** Percentuale di partite vinte su totale
- **Celle Rivelate (media):** Quante celle scopre prima di perdere/vincere
- **Tempo per Mossa:** Performance temporale (ms per mossa)
- **Tempo per Partita:** Tempo totale per completare una partita



- **Per test veloci:** Usa `quick_test.py` durante lo sviluppo
- **Per dati affidabili:** Usa `assessment.py --mode medium` o `--mode full`
- **Per analisi dettagliate:** Esamina i file JSON generati
- **Per presentazioni:** Usa i report testuali generati

Il sistema è progettato per essere semplice da usare ma produrre dati scientificamente validi per analisi quantitative delle strategie.
