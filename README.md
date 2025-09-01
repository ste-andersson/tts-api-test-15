# TTS API Test Center 🎯

Ett robust testcenter för Text-to-Speech API med ElevenLabs integration.

## 🚀 Funktioner

- **TTS API**: WebSocket-baserad text-to-speech med ElevenLabs
- **Test Center**: Omfattande testning av alla moduler
- **Audio Viewer**: Web-baserad ljudfilhantering
- **Mock & Real Testing**: Både simulerade och riktiga API-tester

## 🏗️ Projektstruktur

```
tts-api-test-15/
├── app/
│   ├── endpoints/
│   │   ├── health.py          # Hälsokontroll endpoints
│   │   ├── tts_ws.py          # WebSocket TTS endpoint
│   │   ├── test.py            # Test center endpoint
│   │   └── audio_viewer.py    # Audio filhantering
│   ├── tts/
│   │   ├── receive_text_from_frontend.py  # Text reception
│   │   ├── text_to_audio.py               # ElevenLabs integration
│   │   └── send_audio_to_frontend.py      # Audio forwarding
│   ├── config.py              # Konfiguration
│   └── main.py                # FastAPI app
├── tests/
│   ├── utils/
│   │   └── pcm_to_wav.py      # PCM till WAV konvertering
│   ├── test_receive_text.py   # Text reception tester
│   ├── test_text_to_audio.py  # Text-to-audio tester
│   ├── test_send_audio.py     # Audio forwarding tester
│   ├── test_full_tts_pipeline.py  # Mock pipeline tester
│   ├── test_real_elevenlabs.py    # Riktiga ElevenLabs tester
│   └── test_full_chain.py         # Fullständig pipeline tester
├── Makefile                   # Test och utvecklingskommandon
├── requirements.txt           # Python dependencies
├── render.yaml               # Render deployment konfiguration
└── README.md                 # Denna fil
```

## 🛠️ Installation

```bash
# Klona projektet
git clone <repository-url>
cd tts-api-test-15

# Skapa virtuell miljö och installera dependencies
make install

# Aktivera virtuell miljö
source .venv/bin/activate  # Linux/Mac
# eller
.venv\Scripts\activate     # Windows
```

## 🚀 Körning

### Lokal utveckling
```bash
make dev          # Starta utvecklingsserver
make run          # Starta produktionsserver
```

### Tester
```bash
# Enhetstester
make test-unit

# API Mock-tester
make test-api-mock

# Fullständig Pipeline Mock
make test-full-mock

# ElevenLabs API Test (kräver API-nyckel)
make test-elevenlabs

# Fullständig Pipeline Test
make test-pipeline

# Rensa test output
make clear-output

# Kör med egen text
make test-elevenlabs TEXT="Hej världen!"
```

## 🧪 Test Center

### Via Web UI
Besök `http://localhost:8080/api/` för det fullständiga test center med:
- **Text input** för anpassade tester
- **Test-knappar** för olika testtyper
- **Audio filhantering** för genererade filer

### Via API Endpoints
- `GET /api/test` - Visa tillgängliga tester
- `GET /api/test?test_type=elevenlabs` - Kör ElevenLabs test
- `GET /api/test?test_type=pipeline` - Kör pipeline test
- `GET /api/test?test_type=elevenlabs&text=Hej världen` - Kör med egen text

### Tillgängliga Tester
- **unit**: Enhetstester (testar individuella moduler)
- **api-mock**: API Mock-tester (testar API med mock-data)
- **full-mock**: Fullständig Pipeline Mock (testar hela kedjan med mock-data)
- **elevenlabs**: ElevenLabs API Test (testar mot riktig ElevenLabs API)
- **pipeline**: Fullständig Pipeline Test (testar hela kedjan från frontend till audio)

## 🎵 Audio Hantering

- **Automatisk konvertering**: PCM → WAV i alla tester
- **Web-baserad spelare**: Spela upp WAV-filer direkt i webbläsaren
- **Filhantering**: Ladda ner både PCM och WAV filer
- **Sortering**: Nyaste filer visas först

## 🔧 Konfiguration

Skapa en `.env` fil med:
```env
ELEVENLABS_API_KEY=din_api_nyckel_här
DEFAULT_VOICE_ID=din_voice_id_här
DEFAULT_MODEL_ID=eleven_ttv_v3
ALLOWED_ORIGIN_REGEX=^https?://(localhost(:\d+)?|.*\.lovable\.app|.*\.onrender\.com)$
MAX_TEXT_CHARS=1000
LOG_LEVEL=info
```

## 🌐 Deployment

### Render
Projektet är konfigurerat för Render med `render.yaml`:
- Automatisk deployment från Git
- Miljövariabler för ElevenLabs API
- CORS-konfiguration för webbläsare

### Lokal utveckling
```bash
make dev          # Starta med auto-reload
make run          # Starta produktionsserver
```

## 📚 API Dokumentation

När servern är igång, besök:
- `http://localhost:8080/docs` - Swagger UI
- `http://localhost:8080/redoc` - ReDoc

## 🧹 Underhåll

```bash
make clear-output     # Rensa test_output mapp
make lint             # Kör kodanalys
make format           # Formatera kod
```

## 🔍 Felsökning

### Vanliga problem
1. **404 på `/api/`**: Starta om servern efter ändringar
2. **ElevenLabs API fel**: Kontrollera API-nyckel i `.env`
3. **Test misslyckas**: Kör `make clear-output` och testa igen

### Loggar
- Servern loggar till konsolen
- Test-resultat visas i web UI
- Detaljerad output i test-resultat

## 📝 Utveckling

### Lägg till nya tester
1. Skapa test-fil i `tests/` mappen
2. Lägg till i `test_configs` i `app/endpoints/test.py`
3. Uppdatera `get_test_info()` funktionen
4. Lägg till Makefile target

### Lägg till nya endpoints
1. Skapa router i `app/endpoints/`
2. Registrera i `app/main.py`
3. Uppdatera CORS-konfiguration om nödvändigt

## 🤝 Bidrag

1. Fork projektet
2. Skapa feature branch
3. Commit ändringar
4. Push till branch
5. Skapa Pull Request

## 📄 Licens

Detta projekt är öppen källkod under [MIT License](LICENSE).
