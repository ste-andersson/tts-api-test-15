import os
import base64
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from typing import List, Dict, Any
import wave
import time

router = APIRouter()

@router.get("/audio-files", response_class=HTMLResponse)
async def list_audio_files():
    """Listar alla audio-filer i test_output-mappen."""
    
    output_dir = Path("test_output")
    if not output_dir.exists():
        return HTMLResponse("""
        <html>
        <head><title>Audio Files</title></head>
        <body>
            <h1>🎵 Audio Files</h1>
            <p>Inga audio-filer hittades. Kör ett test först:</p>
            <ul>
                <li><code>make test-real</code> - Testa ElevenLabs API</li>
                <li><code>make test-chain</code> - Testa hela kedjan</li>
            </ul>
        </body>
        </html>
        """)
    
    # Hitta alla audio-filer
    audio_files = []
    for file_path in output_dir.glob("*"):
        if file_path.is_file() and file_path.suffix.lower() in ['.pcm', '.wav']:
            stat = file_path.stat()
            audio_files.append({
                'name': file_path.name,
                'path': str(file_path),
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'type': file_path.suffix.lower()
            })
    
    # Sortera efter senaste modifiering (nyaste först)
    audio_files.sort(key=lambda x: x['modified'], reverse=True)
    
    if not audio_files:
        return HTMLResponse("""
        <html>
        <head><title>Audio Files</title></head>
        <body>
            <h1>🎵 Audio Files</h1>
            <p>Inga audio-filer hittades i test_output-mappen.</p>
        </body>
        </html>
        """)
    
    # Generera HTML
    html = """
    <html>
    <head>
        <title>Audio Files</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .file-item { 
                border: 1px solid #ddd; 
                margin: 10px 0; 
                padding: 15px; 
                border-radius: 5px;
                background: #f9f9f9;
            }
            .file-name { font-weight: bold; font-size: 16px; margin-bottom: 5px; }
            .file-info { color: #666; font-size: 14px; margin-bottom: 10px; }
            .file-actions { margin-top: 10px; }
            .btn { 
                display: inline-block; 
                padding: 8px 16px; 
                margin: 2px; 
                text-decoration: none; 
                border-radius: 4px; 
                font-size: 14px;
            }
            .btn-primary { background: #007bff; color: white; }
            .btn-success { background: #28a745; color: white; }
            .btn-warning { background: #ffc107; color: black; }
            .pcm-note { 
                background: #fff3cd; 
                border: 1px solid #ffeaa7; 
                padding: 10px; 
                border-radius: 4px; 
                margin: 10px 0;
            }
            .wav-note { 
                background: #d4edda; 
                border: 1px solid #c3e6cb; 
                padding: 10px; 
                border-radius: 4px; 
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
        <h1>🎵 Audio Files</h1>
        <p>Senaste filer visas först. Klicka på "Spela upp" för att lyssna.</p>
    """
    
    for file_info in audio_files:
        file_size_kb = file_info['size'] / 1024
        modified_time = os.path.getmtime(file_info['path'])
        modified_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(modified_time))
        
        html += f"""
        <div class="file-item">
            <div class="file-name">📁 {file_info['name']}</div>
            <div class="file-info">
                📊 Storlek: {file_size_kb:.1f} KB | 
                🕒 Skapad: {modified_str} | 
                📋 Typ: {file_info['type'].upper()}
            </div>
        """
        
        if file_info['type'] == '.pcm':
            html += f"""
            <div class="pcm-note">
                ⚠️ <strong>PCM-fil:</strong> Kan inte spelas direkt i webbläsaren. 
                Använd "Konvertera till WAV" för att spela upp.
            </div>
            <div class="file-actions">
                <a href="/api/download-audio/{file_info['name']}" class="btn btn-primary">📥 Ladda ner</a>
                <a href="/api/convert-to-wav/{file_info['name']}" class="btn btn-success">🔄 Konvertera till WAV</a>
            </div>
            """
        elif file_info['type'] == '.wav':
            html += f"""
            <div class="wav-note">
                ✅ <strong>WAV-fil:</strong> Kan spelas direkt i webbläsaren!
            </div>
            <div class="file-actions">
                <audio controls style="width: 100%; margin: 10px 0;">
                    <source src="/api/download-audio/{file_info['name']}" type="audio/wav">
                    Din webbläsare stöder inte audio-elementet.
                </audio>
                <br>
                <a href="/api/download-audio/{file_info['name']}" class="btn btn-primary">📥 Ladda ner</a>
            </div>
            """
        
        html += "</div>"
    
    html += """
    </body>
    </html>
    """
    
    return HTMLResponse(html)

@router.get("/download-audio/{filename}")
async def download_audio(filename: str):
    """Laddar ner en audio-fil."""
    file_path = Path("test_output") / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Filen hittades inte")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )

@router.get("/convert-to-wav/{filename}")
async def convert_to_wav(filename: str):
    """Konverterar en PCM-fil till WAV-format."""
    pcm_path = Path("test_output") / filename
    
    if not pcm_path.exists():
        raise HTTPException(status_code=404, detail="PCM-filen hittades inte")
    
    if pcm_path.suffix.lower() != '.pcm':
        raise HTTPException(status_code=400, detail="Endast PCM-filer kan konverteras")
    
    # Skapa WAV-filnamn
    wav_filename = pcm_path.stem + '.wav'
    wav_path = pcm_path.parent / wav_filename
    
    try:
        # Läs PCM-data
        with open(pcm_path, 'rb') as pcm_file:
            pcm_data = pcm_file.read()
        
        # Skapa WAV-fil (16kHz, 16-bit, mono)
        with wave.open(str(wav_path), 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(16000)  # 16kHz
            wav_file.writeframes(pcm_data)
        
        # Returnera HTML-sida som visar den nya WAV-filen
        html = f"""
        <html>
        <head><title>Konvertering klar</title></head>
        <body>
            <h1>✅ Konvertering klar!</h1>
            <p>PCM-filen <strong>{filename}</strong> har konverterats till WAV.</p>
            
            <h2>🎵 Spela upp WAV-filen:</h2>
            <audio controls style="width: 100%; margin: 20px 0;">
                <source src="/api/download-audio/{wav_filename}" type="audio/wav">
                Din webbläsare stöder inte audio-elementet.
            </audio>
            
            <div style="margin: 20px 0;">
                <a href="/api/download-audio/{wav_filename}" class="btn" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">📥 Ladda ner WAV</a>
                <a href="/api/audio-files" class="btn" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin-left: 10px;">📋 Visa alla filer</a>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(html)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fel vid konvertering: {str(e)}")
