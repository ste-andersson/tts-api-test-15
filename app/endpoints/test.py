import asyncio
import json
import base64
import time
import subprocess
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

router = APIRouter()

class TestRunner:
    """Kör tester och samlar resultat."""
    
    def __init__(self):
        self.test_results = {}
        self.audio_data = {}
    
    async def run_test(self, test_name: str, test_path: str) -> Dict[str, Any]:
        """Kör ett specifikt test och returnerar resultat."""
        try:
            # Kör testet med pytest
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_path, "-v", "--json-report"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            # Analysera resultat
            success = result.returncode == 0
            output = result.stdout
            error = result.stderr
            
            # Samla audio-data om testet kördes framgångsrikt
            audio_data = None
            if success and "test_audio" in test_name.lower():
                audio_data = self._generate_test_audio()
            
            return {
                "test_name": test_name,
                "success": success,
                "output": output,
                "error": error,
                "audio_data": audio_data
            }
            
        except Exception as e:
            return {
                "test_name": test_name,
                "success": False,
                "output": "",
                "error": str(e),
                "audio_data": None
            }
    
    def _generate_test_audio(self) -> str:
        """Genererar test-audio data (base64)."""
        # Simulerar audio-data för tester
        # I verkligheten skulle detta komma från faktiska tester
        test_audio = b"test_audio_data_for_" + str(time.time()).encode()
        return base64.b64encode(test_audio).decode()
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Kör alla tester och returnerar sammanfattning."""
        tests = [
            ("test_receive_text", "tests/test_receive_text.py"),
            ("test_text_to_audio", "tests/test_text_to_audio.py"),
            ("test_send_audio", "tests/test_send_audio.py"),
            ("test_full_tts_pipeline", "tests/test_full_tts_pipeline.py")
        ]
        
        start_time = time.time()
        results = {}
        
        for test_name, test_path in tests:
            result = await self.run_test(test_name, test_path)
            results[test_name] = result
            
            # Samla audio-data
            if result.get("audio_data"):
                self.audio_data[test_name] = result["audio_data"]
        
        total_time = time.time() - start_time
        
        return {
            "status": "completed",
            "total_time": round(total_time, 3),
            "tests": results,
            "audio_data": self.audio_data,
            "summary": {
                "total": len(tests),
                "passed": sum(1 for r in results.values() if r["success"]),
                "failed": sum(1 for r in results.values() if not r["success"])
            }
        }

@router.get("/test")
async def run_tests() -> Dict[str, Any]:
    """Kör alla tester och returnerar resultat."""
    try:
        runner = TestRunner()
        results = await runner.run_all_tests()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")

@router.get("/test-status")
async def get_test_status() -> Dict[str, Any]:
    """Returnerar senaste testresultat."""
    return {
        "status": "ready",
        "message": "Use /test endpoint to run tests",
        "available_tests": [
            "test_receive_text",
            "test_text_to_audio", 
            "test_send_audio",
            "test_full_tts_pipeline"
        ]
    }
