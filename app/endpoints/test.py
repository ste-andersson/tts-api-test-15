import asyncio
import json
import base64
import time
import subprocess
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional

router = APIRouter()

class TestRunner:
    """Kör tester och samlar resultat."""
    
    def __init__(self):
        self.test_results = {}
        self.audio_data = {}
    
    async def run_specific_test(self, test_type: str) -> Dict[str, Any]:
        """Kör ett specifikt test baserat på typ."""
        test_configs = {
            "unit": {
                "name": "Enhetstester",
                "path": "tests/test_receive_text.py",
                "description": "Testar individuella moduler"
            },
            "api-mock": {
                "name": "API Mock-tester",
                "path": "tests/test_text_to_audio.py tests/test_send_audio.py",
                "description": "Testar API med mock-data"
            },
            "full-mock": {
                "name": "Fullständig Pipeline Mock",
                "path": "tests/test_full_tts_pipeline.py",
                "description": "Testar hela kedjan med mock-data"
            },
            "elevenlabs": {
                "name": "ElevenLabs API Test",
                "path": "tests/test_real_elevenlabs.py",
                "description": "Testar mot riktig ElevenLabs API"
            },
            "pipeline": {
                "name": "Fullständig Pipeline Test",
                "path": "tests/test_full_chain.py",
                "description": "Testar hela kedjan från frontend till audio"
            }
        }
        
        if test_type not in test_configs:
            raise ValueError(f"Okänd test-typ: {test_type}")
        
        config = test_configs[test_type]
        
        try:
            print(f"🚀 Startar {config['name']}...")
            
            # Kör testet med pytest
            cmd = [sys.executable, "-m", "pytest", "-v", "-s"]
            if " " in config["path"]:
                # För tester som kör flera filer
                cmd.extend(config["path"].split())
            else:
                cmd.append(config["path"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            # Analysera resultat
            success = result.returncode == 0
            output = result.stdout
            error = result.stderr
            
            return {
                "test_type": test_type,
                "test_name": config["name"],
                "description": config["description"],
                "success": success,
                "output": output,
                "error": error,
                "return_code": result.returncode,
                "command": " ".join(cmd)
            }
            
        except Exception as e:
            return {
                "test_type": test_type,
                "test_name": config["name"],
                "description": config["description"],
                "success": False,
                "output": "",
                "error": str(e),
                "return_code": -1,
                "command": " ".join(cmd) if 'cmd' in locals() else "unknown"
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Kör alla tester och returnerar sammanfattning."""
        test_types = ["unit", "api-mock", "full-mock", "elevenlabs", "pipeline"]
        
        start_time = time.time()
        results = {}
        
        for test_type in test_types:
            result = await self.run_specific_test(test_type)
            results[test_type] = result
        
        total_time = time.time() - start_time
        
        return {
            "status": "completed",
            "total_time": round(total_time, 3),
            "tests": results,
            "summary": {
                "total": len(test_types),
                "passed": sum(1 for r in results.values() if r["success"]),
                "failed": sum(1 for r in results.values() if not r["success"])
            }
        }

def get_test_info() -> Dict[str, Any]:
    """Returnerar information om tillgängliga tester."""
    return {
        "unit": {
            "name": "Enhetstester",
            "description": "Testar individuella moduler",
            "command": "make test-unit",
            "url": "/api/test?test_type=unit"
        },
        "api-mock": {
            "name": "API Mock-tester", 
            "description": "Testar API med mock-data",
            "command": "make test-api-mock",
            "url": "/api/test?test_type=api-mock"
        },
        "full-mock": {
            "name": "Fullständig Pipeline Mock",
            "description": "Testar hela kedjan med mock-data",
            "command": "make test-full-mock",
            "url": "/api/test?test_type=full-mock"
        },
        "elevenlabs": {
            "name": "ElevenLabs API Test",
            "description": "Testar mot riktig ElevenLabs API",
            "command": "make test-elevenlabs",
            "url": "/api/test?test_type=elevenlabs"
        },
        "pipeline": {
            "name": "Fullständig Pipeline Test", 
            "description": "Testar hela kedjan från frontend till audio",
            "command": "make test-pipeline",
            "url": "/api/test?test_type=pipeline"
        }
    }

@router.get("/test")
async def test_endpoint(
    test_type: Optional[str] = Query(None, description="Typ av test att köra"),
    info: Optional[bool] = Query(False, description="Visa bara information utan att köra tester"),
    text: Optional[str] = Query(None, description="Text att testa med")
) -> Dict[str, Any]:
    """Enhetlig endpoint för tester - visar info och kör tester."""
    
    # Hämta test-information
    test_info = get_test_info()
    
    # Om info=True, visa bara information
    if info:
        return {
            "status": "info",
            "message": "Använd /test?test_type=<typ> för att köra specifika tester",
            "available_tests": test_info,
            "examples": [
                "/test?test_type=elevenlabs - Kör ElevenLabs API test",
                "/test?test_type=pipeline - Kör fullständig pipeline test",
                "/test?test_type=elevenlabs&text=Hej världen - Kör med egen text",
                "/test - Kör alla tester",
                "/test?info=true - Visa bara denna information"
            ]
        }
    
    try:
        runner = TestRunner()
        
        if test_type:
            # Kör specifikt test
            if test_type not in test_info:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Okänd test-typ: {test_type}. Tillgängliga: {', '.join(test_info.keys())}"
                )
            
            # Sätt TEXT-miljövariabel om text angavs
            if text:
                import os
                os.environ["TEXT"] = text
            
            result = await runner.run_specific_test(test_type)
            return {
                "status": "completed",
                "test": result,
                "message": f"Körde {result['test_name']} med text: '{text or 'standardtext'}'",
                "available_tests": test_info,  # Inkludera info för enkelhet
                "test_text": text or "standardtext"
            }
        else:
            # Kör alla tester
            # Sätt TEXT-miljövariabel om text angavs
            if text:
                import os
                os.environ["TEXT"] = text
            
            results = await runner.run_all_tests()
            results["available_tests"] = test_info  # Inkludera info för enkelhet
            results["test_text"] = text or "standardtext"
            return results
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")

@router.get("/test-ui")
async def test_ui() -> str:
    """Returnerar HTML-UI för tester med dropdown."""
    test_info = get_test_info()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TTS Test UI</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; max-width: 800px; }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            select, input[type="text"] { 
                width: 100%; 
                padding: 10px; 
                border: 1px solid #ddd; 
                border-radius: 4px; 
                font-size: 16px;
            }
            button { 
                background: #007bff; 
                color: white; 
                padding: 12px 24px; 
                border: none; 
                border-radius: 4px; 
                font-size: 16px; 
                cursor: pointer;
            }
            button:hover { background: #0056b3; }
            .result { 
                margin-top: 20px; 
                padding: 15px; 
                border-radius: 4px; 
                white-space: pre-wrap;
            }
            .success { background: #d4edda; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; border: 1px solid #f5c6cb; }
            .info { background: #d1ecf1; border: 1px solid #bee5eb; }
        </style>
    </head>
    <body>
        <h1>🎯 TTS Test UI</h1>
        
        <div class="form-group">
            <label for="testType">Välj test:</label>
            <select id="testType">
                <option value="">-- Välj test --</option>
    """
    
    for test_key, test_data in test_info.items():
        html += f'<option value="{test_key}">{test_data["name"]}</option>'
    
    html += """
            </select>
        </div>
        
        <div class="form-group">
            <label for="testText">Text att testa med (valfritt):</label>
            <input type="text" id="testText" placeholder="Lämna tomt för standardtext">
        </div>
        
        <div class="form-group">
            <button onclick="runTest()">🚀 Kör Test</button>
            <button onclick="runAllTests()">🔄 Kör Alla Tester</button>
        </div>
        
        <div id="result"></div>
        
        <script>
        async function runTest() {
            const testType = document.getElementById('testType').value;
            const testText = document.getElementById('testText').value;
            
            if (!testType) {
                alert('Välj ett test först!');
                return;
            }
            
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '<div class="info">⏳ Kör test...</div>';
            
            try {
                let url = `/api/test?test_type=${testType}`;
                if (testText) {
                    url += `&text=${encodeURIComponent(testText)}`;
                }
                
                const response = await fetch(url);
                const data = await response.json();
                
                if (data.status === 'completed') {
                    resultDiv.innerHTML = `
                        <div class="success">
                            <h3>✅ Test klart!</h3>
                            <p><strong>Test:</strong> ${data.test.test_name}</p>
                            <p><strong>Text:</strong> ${data.test_text}</p>
                            <p><strong>Status:</strong> ${data.test.success ? 'Lyckades' : 'Misslyckades'}</p>
                            <pre>${data.test.output || 'Ingen output'}</pre>
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `<div class="error">❌ Fel: ${JSON.stringify(data)}</div>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="error">❌ Fel: ${error.message}</div>`;
            }
        }
        
        async function runAllTests() {
            const testText = document.getElementById('testText').value;
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '<div class="info">⏳ Kör alla tester...</div>';
            
            try {
                let url = '/api/test';
                if (testText) {
                    url += `?text=${encodeURIComponent(testText)}`;
                }
                
                const response = await fetch(url);
                const data = await response.json();
                
                if (data.status === 'completed') {
                    let resultHtml = '<div class="success"><h3>✅ Alla tester klara!</h3>';
                    resultHtml += `<p><strong>Text:</strong> ${data.test_text}</p>`;
                    resultHtml += `<p><strong>Resultat:</strong> ${data.summary.passed}/${data.summary.total} lyckades</p>`;
                    
                    for (const [testKey, testResult] of Object.entries(data.tests)) {
                        const status = testResult.success ? '✅' : '❌';
                        resultHtml += `<p>${status} ${testResult.test_name}: ${testResult.success ? 'Lyckades' : 'Misslyckades'}</p>`;
                    }
                    
                    resultHtml += '</div>';
                    resultDiv.innerHTML = resultHtml;
                } else {
                    resultDiv.innerHTML = `<div class="error">❌ Fel: ${JSON.stringify(data)}</div>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="error">❌ Fel: ${error.message}</div>`;
            }
        }
        </script>
    </body>
    </html>
    """
    
    return html
