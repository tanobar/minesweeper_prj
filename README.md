Ciao!

Questo README momentaneo serve per spiegarvi cosa potete trovare in questa repo e come funziona (a grosse linee).
Ci sono 3 file per adesso:

- minesweeper_env.py è la classe gestisce il mondo di gioco, i paramentri n ed m indicano rispettivamente la dimensione delle griglia (quadrata) e il numero di mine che ci saranno. Il metodo costruttore genera una griglia casuale  con quei parametri da usare come groung truth. I metodi per ora presenti sono reveal(x, y) e print_grid.

-agent.py è la classe dell'agente. Alla creazione costruisce una sua conoscenza del campo, all'inizio ha una visione del campo dove ogni cella è marcata come "?". Per ora ha un metodo observe(x, y, value) che gli permette di aggiornare la cella x, y col valore "value", flag_mine(x, y) ma che per ora non viene usato, choose_action() che per ora l'unica cosa che fa è esplorare random e print_grid() stampa l'attuale knowledge del campo dell'agente.

-main.py potete avviarlo, inizia una partita e l'agente gioca. Di solito il gioco originale è fatto in modo che la prima cella che scopri non abbia mai una mina per evitare morte istantanea. Io ho deciso di fornire all'agente la griglia con 1 cella con 0 mine attorno rivelata come punto di partenza. (ATTENZIONE, se viene creata una griglia troppo densa di mine, potrebbe non avere una cella 0 disponibile e quindi partirebbe random con rischio di morire subito. Decidiamo se mantenere la densità con un certo rapporto per assicurare celle 0 o se togliere il vincolo della cella 0 e far iniziare il gioco su una qualsiasi cella senza mina). Il gioco va avanti con l'agente che scopre tutte le caselle, una per volta, finché non esplode. Svela per prime le celle attorno allo 0, se trova un'altra cella con 0, segna i vicini coperti di quello 0 come safe. Quando finisce di svelare quelle safe va a random. Se dovesse svelare tutte le safe e rimanere solo con delle mine coperte, inizierebbe a svelare le mine e morirebbe, non ha un modo per capire se ha vinto o no.

Per ora questo è quanto, "il codice è la documentazione".