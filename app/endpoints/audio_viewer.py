import os
import base64
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from typing import Dict, Any, List, Optional
import wave
import time

router = APIRouter()

@router.get("/audio-files")
async def list_audio_files() -> Dict[str, Any]:
    """Returnerar lista över audio-filer för dropdown."""
    output_dir = Path("test_output")
    
    if not output_dir.exists():
        return {
            "files": [],
            "message": "Inga audio-filer hittades. Kör ett test först."
        }
    
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
    
    return {
        "files": audio_files,
        "message": f"Hittade {len(audio_files)} audio-filer"
    }

@router.get("/audio-ui")
async def audio_ui() -> str:
    """Returnerar HTML-UI för audio-filer med dropdown."""
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Audio Files</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; max-width: 800px; }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            select { 
                width: 100%; 
                padding: 10px; 
                border: 1px solid #ddd; 
                border-radius: 4px; 
                font-size: 16px;
            }
            button { 
                background: #007bff; 
                color: white; 
                padding: 10px 20px; 
                border: none; 
                border-radius: 4px; 
                font-size: 14px; 
                cursor: pointer;
                margin: 5px;
            }
            button:hover { background: #0056b3; }
            .file-info { 
                margin: 20px 0; 
                padding: 15px; 
                background: #f8f9fa; 
                border-radius: 4px; 
                border: 1px solid #dee2e6;
            }
            .audio-player { width: 100%; margin: 10px 0; }
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
        
        <div class="form-group">
            <label for="audioFile">Välj audio-fil:</label>
            <select id="audioFile" onchange="showFileInfo()">
                <option value="">-- Välj fil --</option>
            </select>
        </div>
        
        <div id="fileInfo"></div>
        
        <script>
        // Ladda filer när sidan laddas
        window.onload = loadAudioFiles;
        
        async function loadAudioFiles() {
            try {
                const response = await fetch('/api/audio-files');
                const data = await response.json();
                
                const select = document.getElementById('audioFile');
                select.innerHTML = '<option value="">-- Välj fil --</option>';
                
                data.files.forEach(file => {
                    const option = document.createElement('option');
                    option.value = JSON.stringify(file);
                    option.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
                    select.appendChild(option);
                });
                
                if (data.files.length === 0) {
                    select.innerHTML = '<option value="">Inga filer hittades</option>';
                }
            } catch (error) {
                console.error('Fel vid laddning av filer:', error);
            }
        }
        
        function showFileInfo() {
            const select = document.getElementById('audioFile');
            const fileInfoDiv = document.getElementById('fileInfo');
            
            if (!select.value) {
                fileInfoDiv.innerHTML = '';
                return;
            }
            
            const file = JSON.parse(select.value);
            const fileSizeKB = (file.size / 1024).toFixed(1);
            const modifiedTime = new Date(file.modified * 1000).toLocaleString('sv-SE');
            
            let html = `
                <div class="file-info">
                    <h3>📁 ${file.name}</h3>
                    <p><strong>Storlek:</strong> ${fileSizeKB} KB</p>
                    <p><strong>Typ:</strong> ${file.type.toUpperCase()}</p>
                    <p><strong>Skapad:</strong> ${modifiedTime}</p>
            `;
            
            if (file.type === '.pcm') {
                html += `
                    <div class="pcm-note">
                        ⚠️ <strong>PCM-fil:</strong> Kan inte spelas direkt i webbläsaren.
                        <br>Ladda ner och konvertera till WAV med: <code>python tests/utils/pcm_to_wav.py ${file.name}</code>
                    </div>
                    <button onclick="downloadFile('${file.name}')">📥 Ladda ner</button>
                `;
            } else if (file.type === '.wav') {
                html += `
                    <div class="wav-note">
                        ✅ <strong>WAV-fil:</strong> Kan spelas direkt i webbläsaren!
                    </div>
                    <audio controls class="audio-player">
                        <source src="/api/download-audio/${file.name}" type="audio/wav">
                        Din webbläsare stöder inte audio-elementet.
                    </audio>
                    <br>
                    <button onclick="downloadFile('${file.name}')">📥 Ladda ner</button>
                `;
            }
            
            html += '</div>';
            fileInfoDiv.innerHTML = html;
        }
        
        function downloadFile(filename) {
            window.open(`/api/download-audio/${filename}`, '_blank');
        }
        </script>
    </body>
    </html>
    """
    
    return html

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
