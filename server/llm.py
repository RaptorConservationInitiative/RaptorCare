"""
LLM Integration with Ollama
Provides RaptorCare AI for care recommendations and analysis
"""

import logging
import requests
from typing import Optional, Dict
from server.config import get_settings
from server.gpu import GPUPool, GPUType

logger = logging.getLogger(__name__)
settings = get_settings()


class RaptorCareAI:
    """
    Main LLM interface using Ollama
    Runs on GPU 0 (T600/GTX 1650)
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.gpu_id = GPUPool.select_best_gpu(GPUType.LLM)

        # Ensure GPU 0 is set
        GPUPool.set_device(self.gpu_id)
        logger.info(f"🤖 RaptorCareAI initialized on GPU {self.gpu_id}")

    def _call_ollama(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Call Ollama API with prompt"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7,
                    "top_p": 0.9
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return None

    def generate_care_recommendations(self, bird_data: Dict) -> str:
        """Generate daily care recommendations (DEUTSCH)"""

        prompt = f"""
Du bist ein Experte für Greifvogel-Rehabilitation in Auffangstationen.
Basierend auf den folgenden Tierdaten, gebe detaillierte deutsche Pflege-Empfehlungen:

🦅 **Tierdaten:**
- Art: {bird_data.get('species', 'Unbekannt')}
- Gewicht: {bird_data.get('weight', 'Unbekannt')} g
- Verhalten: {bird_data.get('behavior', 'Unbekannt')}
- Hydration: {bird_data.get('hydration_status', 'Unbekannt')}
- Tage in Pflege: {bird_data.get('days_in_care', 'Unbekannt')}

📋 **Geben Sie konkrete Empfehlungen für:**
1. Futtertyp und Menge
2. Aktivitätsförderung
3. Medizinische Überwachung
4. Gehege-Anforderungen
5. Auswilderungs-Readiness-Indikationen

Antworte kurz und präzise auf Englisch.
"""

        result = self._call_ollama(prompt)
        return result or "Empfehlung konnte nicht generiert werden."

    def generate_feeding_plan(self, bird_data: Dict) -> str:
        """Generate feeding plan (DEUTSCH)"""

        prompt = f"""
Du bist ein Spezialist für Greifvogel-Ernährung.
Erstelle einen detaillierten Fütterungsplan für folgendes Tier:

🦅 Spezies: {bird_data.get('species', 'Unbekannt')}
📊 Gewicht: {bird_data.get('weight', 'Unbekannt')} g
🎯 Rehabilitationsstatus: {bird_data.get('status', 'Unbekannt')}

Bitte geben Sie an:
1. Empfohlene Beutetiere (ganz/gehackt)
2. Tägliche Futtermenge
3. Fütterungsfrequenz
4. Fütterungsmethode (eigenständig/unterstützt)
5. Ernährungsziele für diese Woche

Antworte auf Englisch.
"""

        result = self._call_ollama(prompt)
        return result or "Fütterungsplan konnte nicht generiert werden."

    def analyze_health_anomalies(self, health_records: list) -> str:
        """Analyze health trends for anomalies (DEUTSCH)"""

        # Prepare health summary
        health_summary = "\n".join([
            f"  - {record.get('date')}: Gewicht {record.get('weight')}g, "
            f"Verhalten: {record.get('behavior')}"
            for record in health_records[-7:]  # Last 7 records
        ])

        prompt = f"""
Du bist ein Tierarzt spezialisiert auf Greifvögel.
Analysiere die folgenden Gesundheitsdaten und identifiziere potenzielle Probleme:

📅 **Letzte 7 Tage Gesundheitsverlauf:**
{health_summary}

🔍 Bitte identifizieren Sie:
1. Gewichtstrends (Zu- oder Abnahme?)
2. Verhaltensmuster (Normal/Auffällig?)
3. Mögliche Gesundheitsprobleme
4. Empfohlene Maßnahmen

Antworte präzise auf Englisch.
"""

        result = self._call_ollama(prompt)
        return result or "Analyse konnte nicht durchgeführt werden."

    def estimate_release_prognosis(self, bird_data: Dict, health_history: list) -> str:
        """Estimate prognosis for release (DEUTSCH)"""

        days_in_care = bird_data.get('days_in_care', 0)

        prompt = f"""
Du bist ein erfahrener Greifvogel-Rehabber mit 20 Jahren Erfahrung.
Schätze die Wahrscheinlichkeit einer erfolgreichen Auswilderung:

🦅 **Tier:**
- Art: {bird_data.get('species', 'Unbekannt')}
- Aktuelle Gewicht: {bird_data.get('weight', 'Unbekannt')} g
- In Pflege seit: {days_in_care} Tagen
- Ursprüngliche Verletzung: {bird_data.get('injury', 'Unbekannt')}

📊 **Gesundheitstrend:**
{health_history[:3] if health_history else "Keine Daten"}

🎯 **Bitte geben Sie an:**
1. Auswilderungs-Wahrscheinlichkeit (Prozentsatz)
2. Empfohlene Auswilderungszeitpunkt
3. Noch erforderliche Trainings
4. Potenzielle Risiken bei Auswilderung

Antworte auf Englisch.
"""

        result = self._call_ollama(prompt)
        return result or "Prognose konnte nicht generiert werden."


class NeuralNetworkProcessor:
    """
    Neural Network tasks running on GPU 1
    Image analysis, sensor data processing, pattern recognition
    """

    def __init__(self):
        self.gpu_id = GPUPool.select_best_gpu(GPUType.NEURAL_NET)
        GPUPool.set_device(self.gpu_id)
        logger.info(f"🧠 NeuralNetworkProcessor initialized on GPU {self.gpu_id}")

    def analyze_image(self, image_path: str) -> Dict:
        """
        Analyze bird image
        TODO: Implement with torchvision or similar
        """
        logger.info(f"🖼️ Analyzing image on GPU {self.gpu_id}: {image_path}")

        return {
            "status": "success",
            "gpu_used": self.gpu_id,
            "analysis": {
                "species_detected": "Wanderfalke",
                "health_indicators": "Good plumage condition",
                "injury_detection": "No visible injuries"
            }
        }

    def process_sensor_data(self, sensor_data: Dict) -> Dict:
        """
        Process IoT sensor data (temperature, humidity, movement)
        TODO: Implement pattern recognition
        """
        logger.info(f"📊 Processing sensor data on GPU {self.gpu_id}")

        return {
            "status": "success",
            "gpu_used": self.gpu_id,
            "anomalies_detected": []
        }


# Example usage
if __name__ == "__main__":
    # Test LLM
    ai = RaptorCareAI()

    bird_data = {
        "species": "Wanderfalke",
        "weight": 900,
        "behavior": "Alert, frisst gut",
        "hydration_status": "Gut",
        "days_in_care": 5
    }

    print("📋 Care Recommendations:")
    rec = ai.generate_care_recommendations(bird_data)
    print(rec)

    print("\n🍗 Feeding Plan:")
    feed = ai.generate_feeding_plan(bird_data)
    print(feed)

    # Test GPU status
    print("\n🎮 GPU Status:")
    GPUPool.print_gpu_status()
