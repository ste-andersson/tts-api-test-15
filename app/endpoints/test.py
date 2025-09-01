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
    
    # Om inga parametrar skickas, visa tillgängliga tester
    if not test_type and not info:
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
