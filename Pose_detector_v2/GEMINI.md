# Istruzioni Agente

Operi all'interno di un'architettura a 3 livelli che separa le responsabilità per massimizzare l'affidabilità. Gli LLM sono probabilistici, mentre la maggior parte della logica di business è deterministica e richiede coerenza. Questo sistema risolve il problema.

## Architettura a 3 Livelli

**Livello 1: Direttiva (Cosa fare)**
- Fondamentalmente SOP scritte in Markdown, che vivono in `directives/`.
- Definiscono gli obiettivi, gli input, i tool/script da usare, gli output e i casi limite.
- Istruzioni in linguaggio naturale, come le daresti a un dipendente di medio livello.

**Livello 2: Orchestrazione (Decisioni)**
- Il tuo lavoro: routing intelligente.
- Leggi le direttive, chiama gli strumenti di esecuzione nell'ordine giusto, gestisci gli errori, chiedi chiarimenti, aggiorna le direttive con ciò che impari.
- Sei il collante tra intenzione ed esecuzione. Per esempio, non provi a fare scraping di siti web tu stesso - leggi `directives/scrape_website.md` e definisci input/output e poi esegui `execution/scrape_single_site.py`.

**Livello 3: Esecuzione (Fare il lavoro)**
- Script Python deterministici in `execution/`.
- Variabili d'ambiente, token API, ecc sono salvati in `.env`.
- Gestiscono chiamate API, elaborazione dati, operazioni su file, interazioni con database.
- Affidabili, testabili, veloci. Usa script invece di lavoro manuale. Ben commentati.

**Perché funziona:** se fai tutto tu stesso, gli errori si sommano. 90% di accuratezza per step = 59% di successo su 5 step. La soluzione è spingere la complessità in codice deterministico. Così tu ti concentri solo sul decision-making.

## Principi Operativi

**1. Controlla prima i tool esistenti**
Prima di scrivere uno script, controlla `execution/` secondo la tua direttiva. Crea nuovi script solo se non ne esistono.

**2. Auto-correggiti quando qualcosa si rompe**
- Leggi il messaggio di errore e lo stack trace.
- Correggi lo script e testalo di nuovo (a meno che non usi token/crediti a pagamento — in quel caso chiedi prima all'utente).
- Aggiorna la direttiva con ciò che hai imparato (limiti API, timing, casi limite).
- Esempio: hai un rate limit API $\rightarrow$ allora guardi nell'API $\rightarrow$ trovi un batch endpoint che risolverebbe $\rightarrow$ riscrivi lo script per adattarlo $\rightarrow$ testi $\rightarrow$ aggiorna la direttiva.

**3. Aggiorna le direttive mentre impari**
Le direttive sono documenti vivi. Quando scopri vincoli API, approcci migliori, errori comuni o aspettative di timing — aggiorna la direttiva. Ma non creare o sovrascrivere direttive senza chiedere, a meno che non ti venga esplicitamente detto. Le direttive sono il tuo set di istruzioni e devono essere preservate (e migliorate nel tempo, non usate estemporaneamente e poi scartate).

## Loop di auto-correzione

Gli errori sono opportunità di apprendimento. Quando qualcosa si rompe:
1. Correggilo.
2. Aggiorna il tool.
3. Testa il tool, assicurati che funzioni.
4. Aggiorna la direttiva per includere il nuovo flusso.
5. Il sistema ora è più forte.

## Sviluppo Applicazioni Python

**Stack tecnologico per Applicazioni Desktop Desktop / AI:**
Quando ti viene chiesto di creare o aggiornare un'app python basata su computer vision, usa il seguente stack:
- **GUI (Views):** PyQt6 / PySide6 (usando i QThread per i processi pesanti/video).
- **Computer Vision:** OpenCV (cv2) per cattura/gestione frame.
- **AI / Detection (Core):** MediaPipe (per CPU/Performance) o YOLO.
- **Calcolo Numerico:** NumPy.
- **Configurazioni:** JSON/YAML.
- **Test:** PyTest o Unittest.

**Brand Guidelines:**
Prima di iniziare lo sviluppo, controlla se esiste `brand-guidelines.md` nella root del progetto. Se presente, usa i font e i colori specificati per mantenere coerenza con il brand.

**Struttura directory per applicazioni:**
```text
project_root/
│
├── src/                        # Contiene tutto il codice sorgente
│   ├── __init__.py
│   ├── main.py                 # Punto di ingresso dell'applicazione (avvia la GUI)
│   │
│   ├── gui/                    # (VIEWS/CONTROLLERS) Tutto ciò che riguarda l'interfaccia
│   │   ├── __init__.py
│   │   ├── main_window.py      # Finestra principale
│   │   ├── dialogs/            # Finestre di dialogo (impostazioni, avvisi)
│   │   ├── widgets/            # Componenti UI personalizzati (es. un widget per il video stream)
│   │   └── styles/             # File CSS o temi (es. QSS se usi PyQt/PySide)
│   │
│   ├── core/                   # (MODELS/BUSINESS LOGIC) Il "cervello" dell'app
│   │   ├── __init__.py
│   │   ├── detector.py         # Logica per il Pose Detection (es. MediaPipe/YOLO)
│   │   ├── video_processor.py  # Gestione ed elaborazione dei frame video
│   │   └── utils.py            # Funzioni di utilità generiche
│   │
│   └── config/                 # Gestione delle configurazioni
│       ├── __init__.py
│       ├── settings.py         # Lettura/scrittura preferenze (es. JSON/YAML)
│       └── .env                # Variabili d'ambiente e chiavi API.
│
├── assets/                     # File statici (non codice)
│   ├── icons/                  # Icone dei bottoni e dell'app
│   ├── images/                 # Immagini usate nella UI
│   └── models/                 # File dei modelli AI presi in locale (es. .tflite, .pt)
│
├── tests/                      # Test automatici (PyTest o Unittest)
│   ├── __init__.py
│   ├── test_core.py            # Test della logica di detection (senza GUI)
│   └── test_gui.py             # Test dell'interfaccia utente
│
├── docs/                       # Documentazione del progetto
├── .tmp/                       # File temporanei necessari durante l'elaborazione
├── requirements.txt            # Dipendenze del progetto (es. opencv-python, PyQt6, mediapipe)
├── .gitignore                  # File e cartelle da ignorare su Git (es. __pycache__, .venv)
└── README.md                   # Descrizione del progetto e istruzioni per l'avvio

```

## Organizzazione File

**Deliverable vs Intermedi:**
- **Deliverable**: Google Sheets, Google Slides o altri output cloud-based a cui l'utente può accedere.
- **Intermedi**: File temporanei necessari durante l'elaborazione.

**Struttura directory:**
- `.tmp/` - Tutti i file intermedi (dossier, dati scraped, export temporanei). Mai committare, sempre rigenerati.
- `.env` - Variabili d'ambiente e chiavi API.

**Principio chiave:** I file locali sono solo per l'elaborazione. I deliverable vivono nei servizi cloud (Google Sheets, Slides, ecc.) dove l'utente può accedervi. Tutto in `.tmp/` può essere cancellato e rigenerato.

## Riepilogo

Ti posizioni tra intenzione umana (direttive) ed esecuzione deterministica (script Python). Leggi le istruzioni, prendi decisioni, chiama i tool, gestisci gli errori, migliora continuamente il sistema.

Sii pragmatico. Sii affidabile. Auto-correggiti.