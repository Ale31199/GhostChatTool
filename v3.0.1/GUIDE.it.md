# GhostChatTool v3.0.1 — Guida italiana

[English — predefinito](GUIDE.en.md) · Italiano · [Español](GUIDE.es.md) · [Français](GUIDE.fr.md) · [Deutsch](GUIDE.de.md)

## Che versione è?

È la v3.0.1 che lavora sui log locali, **senza Chrome o altri browser aperti**. Non è la v1 manuale né la v4 con estensione. Il programma originale è invariato; sono aggiunti comandi di gestione e guide. Nei comandi forniti, i tentativi automatici di ricaricare la finestra e i nudges sono disattivati: se la lista resta vecchia, chiudi completamente l'app e riaprila tu.

È un rimedio sperimentale non ufficiale, non una patch OpenAI. Non garantisce la scomparsa di ogni chat eliminata da un altro dispositivo, neppure dopo la riapertura. Interviene solo quando una riga dei log contiene l'ID della chat insieme a `conversation_deleted` o `conversation deleted`. Senza questa prova locale non ripara. Non controlla direttamente il server e non fa due verifiche server.

## Preparazione e installazione

Servono Windows 10/11, Python 3.10 o successivo disponibile come `py` o `python`, Windows PowerShell e il database `%USERPROFILE%\.codex\sqlite\codex-dev.db`. Non servono pacchetti aggiuntivi, accessi o credenziali. Estrai tutto lo ZIP prima di avviare i file.

**Se hai già la v3.0.1 funzionante, non installarne un'altra.** Per migrare, ferma la vecchia versione e disattivane l'avvio automatico seguendo le sue istruzioni. Puoi vedere la cartella di avvio premendo Windows + R e scrivendo `shell:startup`. Non cancellare elementi sconosciuti o la cartella `.codex`. L'installer si ferma se trova un altro avvio GhostChat, un watcher attivo o la cartella di destinazione già esistente. Non disinstalla automaticamente la v4 o le estensioni.

1. Apri `GUIDE.html` per scegliere la lingua. `DRY_RUN.cmd` mostra i candidati senza modificare il database; un altro watcher attivo può comunque scrivere, quindi fermalo per un test interamente in sola lettura.
2. Avvia `INSTALL.cmd`, leggi l'avviso e scrivi `INSTALL`. Installa in `%LOCALAPPDATA%\GhostChatTool-v3.0.1`, aggiunge il collegamento `GhostChatTool v3.0.1.lnk` all'avvio dell'utente e avvia il controllo nascosto.
3. Nella **cartella installata**, usa `STATUS.cmd` per lo stato, `STOP.cmd` per fermarlo e `START.cmd` per ripartire. Non servono diritti amministrativi. Non è un servizio: Windows e la sessione utente devono essere attivi. STOP non disattiva l'avvio al prossimo accesso.

Se compare un errore, non considerare riuscita l'installazione. Leggi il messaggio e controlla lo stato. Non aggirare le regole di sicurezza del tuo computer aziendale.

## Test semplice

1. Crea una chat di prova fuori dai Projects e verifica che sia visibile sul PC.
2. Elimina **solo quella chat di prova** dal telefono. La cancellazione sul server è definitiva. Tieni l'app del PC connessa.
3. Controlla `STATUS.cmd`: serve un nuovo orario di riparazione e un numero di rimozioni maggiore di zero. Il manifesto privato indica quale chat è stata riparata. Una vecchia “ultima riparazione” non dimostra che lo sia questa chat.
4. Se resta nella lista, esci completamente dall'app, anche dai processi in background, e riaprila dal menu Start. Non serve cercare un pulsante Ricarica; GhostChat non forza la chiusura.
5. Se non c'è una nuova riparazione, ferma il watcher, chiudi l'app e usa `DRY_RUN.cmd`. Senza l'evento richiesto non viene eliminato nulla. `REPAIR_ONCE.cmd`, con app e watcher chiusi, permette un controllo/riparazione singolo dei soli candidati confermati. Poi riapri l'app e usa `START.cmd`.

Il controllo è normalmente ogni tre secondi e la ricerca dei file di log ogni quindici circa, **ma non è una promessa sui tempi**: l'app potrebbe non produrre mai l'evento necessario. Non eliminare altre chat reali per tentativi.

## Backup, ripristino e rimozione

Backup: `%USERPROFILE%\.codex\sqlite\ghostchat-backups`. Log, stato e manifesti privati: `%USERPROFILE%\.codex\sqlite\ghostchat-patch`. Dopo le riparazioni vengono conservati fino a 20 backup, nella stessa cartella usata dalle vecchie versioni. Conserva altrove quelli importanti.

`RESTORE.cmd` ferma il watcher di questo pacchetto, richiede l'app completamente chiusa e la conferma `RESTORE`. Ripristina il backup più recente dell'**intero database locale**, non una singola chat; crea anche un backup prima del ripristino. Può annullare altre modifiche locali. Il watcher resta fermo, ma l'avvio al login rimane e, ripartendo, può applicare nuovamente la stessa riparazione. Per disattivare l'avvio durante il recupero, usa prima `UNINSTALL.cmd` e poi il ripristino dai file conservati.

`UNINSTALL.cmd` ferma il watcher e rimuove solo il collegamento di avvio di questo pacchetto. Conserva programma, database, log e backup; non annulla riparazioni precedenti e non rimuove altre versioni o estensioni.

## Limiti e riservatezza

I nuovi comandi controllano lo schema prima dell'avvio; nel programma originale l'esclusione dei Projects dipende dalla colonna `project_id`. Non è garantito un arresto sicuro per ogni futuro cambio di schema. Il backup precede la riparazione e `PRAGMA integrity_check` viene eseguito dopo la modifica già confermata: non verifica il server e non garantisce un annullamento automatico. Se un aggiornamento dell'app rompe la compatibilità, interrompi l'uso.

Non vengono letti/esportati cookie, token o `auth.json`, non sono chiamate API private e non viene modificato o iniettato codice nell'eseguibile. Log, manifesti e backup possono contenere dati personali: **non condividerli senza rimuovere le informazioni sensibili**. Nella release ci sono solo codice, guide e test sintetici. Dettagli in `README.md`; verifiche effettive in `TEST_REPORT.md`.
