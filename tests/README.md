# TTS API Tester

Detta är teststrukturen för TTS API:et. Testerna är designade för att verifiera att alla moduler fungerar korrekt både individuellt och tillsammans.

## Teststruktur

### **Unit Tester**
- **`test_receive_text.py`** - Testar text-validering från frontend
- **`test_text_to_audio.py`** - Testar ElevenLabs API-integration  
- **`test_send_audio.py`** - Testar audio-hantering till frontend

### **Integration Tester**
- **`test_full_tts_pipeline.py`** - Testar hela TTS-pipelinen

## Kommandon

### **Lokala tester (Makefile)**
```bash
make test          # Kör alla tester
make test-unit     # Kör bara unit-tester (ingen internet)
make test-api      # Kör API-tester (kräver internet)
make test-full     # Kör hela pipeline (kräver internet)
```

### **Endpoint-tester**
- **`GET /api/test`** - Kör alla tester och returnerar resultat
- **`GET /api/test-status`** - Visar tillgängliga tester

## Krav

- **pytest** - Testramverk
- **pytest-asyncio** - Async test-stöd
- **Internet** - För API-tester (ElevenLabs)
- **API-nyckel** - ElevenLabs API-nyckel i .env

## Vad testerna verifierar

### **receive_text_from_frontend**
- ✅ Giltig text tas emot korrekt
- ❌ Tom text avvisas
- ❌ För lång text avvisas (>1000 tecken)
- ❌ Ogiltig JSON avvisas
- ❌ Saknade text-fält hanteras

### **text_to_audio**
- ✅ Anslutning till ElevenLabs fungerar
- ✅ Audio-chunks tas emot korrekt
- ✅ Längre text hanteras
- ✅ Timeout hanteras snyggt
- ✅ API-fel hanteras

### **send_audio_to_frontend**
- ✅ Audio-chunks skickas vidare korrekt
- ✅ Binära frames hanteras
- ✅ Error-meddelanden skickas
- ✅ Final frames detekteras
- ✅ Debug-info skickas

### **Full Pipeline**
- ✅ Hela kedjan fungerar från text till audio
- ✅ Fel hanteras genom hela pipelinen
- ✅ Prestanda mäts
- ✅ Status-meddelanden skickas

## Felhantering

Testerna visar tydligt var fel uppstår:
- Exakt vilken rad som kraschade
- Stack trace med alla detaljer
- Vilka assertions som misslyckades
- Tydliga felmeddelanden

## Audio Playback

För tester som genererar audio:
- Audio konverteras till base64
- Inbäddas i testresultatet
- Kan spelas upp direkt från endpoint
- Verifierar att ljudet faktiskt fungerar
