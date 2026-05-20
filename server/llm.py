"""
LLM Integration - Ollama-basierte KI für Pflege- und Reha-Empfehlungen
"""

import requests
import logging
from typing import Optional, List
from datetime import datetime
from langchain.llms.ollama import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from server.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RaptorCareAI:
    """Interface to Ollama LLM for care recommendations"""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

        try:
            # Initialize LLM with streaming
            self.llm = Ollama(
                base_url=self.base_url,
                model=self.model,
                callback_manager=CallbackManager(
                    [StreamingStdOutCallbackHandler()]
                ),
                temperature=0.3,  # Low temperature for consistent recommendations
                top_p=0.9,
            )
            logger.info(f"✅ Ollama LLM initialized: {self.model} at {self.base_url}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Ollama LLM: {str(e)}")
            self.llm = None

    def check_connection(self) -> bool:
        """Check if Ollama server is reachable"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Ollama connection failed: {str(e)}")
            return False

    def get_care_recommendations(self, bird_context: dict) -> dict:
        """
        Generate care recommendations for a specific bird

        bird_context should contain:
        - species
        - current_status
        - weight_history
        - recent_health_issues
        - medications
        - feeding_history
        """

        if not self.llm:
            logger.warning("LLM not initialized, returning default recommendations")
            return self._default_recommendations()

        try:
            # Build context prompt
            prompt = self._build_care_prompt(bird_context)

            # Generate recommendation
            logger.info(f"Generating care recommendations for bird {bird_context.get('id')}")
            response = self.llm.invoke(prompt)

            return {
                "success": True,
                "recommendations": response,
                "confidence": 0.85,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Recommendation generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback": self._default_recommendations()
            }

    def get_rehabilitation_prognosis(self, bird_context: dict) -> dict:
        """
        Predict rehabilitation prognosis based on bird history

        Returns: {prognosis, success_probability, estimated_timeline, risk_factors}
        """

        if not self.llm:
            logger.warning("LLM not initialized, returning default prognosis")
            return self._default_prognosis()

        try:
            prompt = self._build_prognosis_prompt(bird_context)

            logger.info(f"Generating prognosis for bird {bird_context.get('id')}")
            response = self.llm.invoke(prompt)

            return {
                "success": True,
                "prognosis": response,
                "confidence": 0.75,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Prognosis generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback": self._default_prognosis()
            }

    def detect_health_anomalies(self, health_history: List[dict]) -> dict:
        """
        Analyze health records for anomalies and trends

        health_history: List of daily health records with weight, behavior, etc.
        """

        if not self.llm:
            logger.warning("LLM not initialized, returning default anomaly detection")
            return {"anomalies": [], "trends": []}

        try:
            prompt = self._build_anomaly_detection_prompt(health_history)

            logger.info("Analyzing health records for anomalies")
            response = self.llm.invoke(prompt)

            return {
                "success": True,
                "analysis": response,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Anomaly detection failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "anomalies": [],
                "trends": []
            }

    # ========================================================================
    # PROMPT BUILDERS
    # ========================================================================

    def _build_care_prompt(self, bird_context: dict) -> str:
        """Build detailed care recommendation prompt"""

        species = bird_context.get("species", "Unknown")
        status = bird_context.get("status", "In treatment")
        weight = bird_context.get("recent_weight", "Unknown")
        health_issues = bird_context.get("health_issues", [])
        medications = bird_context.get("medications", [])

        prompt = f"""
# RaptorCare Pflegeempfehlungen

## Patienteninformation
- **Art**: {species}
- **Status**: {status}
- **Gewicht**: {weight}g
- **Aktuelle Gesundheitsprobleme**: {', '.join(health_issues) if health_issues else 'Keine'}
- **Medikamente**: {', '.join(medications) if medications else 'Keine'}

## Aufgabe
Gib konkrete, praktikable Pflegeempfehlungen für diesen Greifvogel basierend auf seiner Art, seinem Status und seinen Gesundheitsproblemen.

Strukturiere deine Antwort wie folgt:
1. **Fütterung**: Empfohlener Futtertyp, Menge, Häufigkeit
2. **Unterbringung**: Gehegeanforderungen und Umweltbedingungen
3. **Tägliche Beobachtung**: Worauf man achten sollte
4. **Vorbeugungsmaßnahmen**: Infektionsprävention und Stressabbau
5. **Auswilderungsvorbereitung**: Falls relevant

Antworte prägnant und medizinisch korrekt.
"""
        return prompt

    def _build_prognosis_prompt(self, bird_context: dict) -> str:
        """Build rehabilitation prognosis prompt"""

        species = bird_context.get("species", "Unknown")
        days_in_care = bird_context.get("days_in_care", 0)
        injuries = bird_context.get("injuries", [])
        weight_change = bird_context.get("weight_change_percent", 0)

        prompt = f"""
# Rehabilitationsprognose

## Patientenhistorie
- **Art**: {species}
- **Tage in Pflege**: {days_in_care}
- **Verletzungen**: {', '.join(injuries) if injuries else 'Keine bekannt'}
- **Gewichtsentwicklung**: {weight_change:+.1f}%

## Analyse
Beurteile basierend auf dieser Information:
1. Die Wahrscheinlichkeit einer erfolgreichen Auswilderung (0-100%)
2. Den geschätzten Zeithorizont bis zur Auswilderung
3. Potenzielle Komplikationen oder Risikofaktoren
4. Empfohlene Maßnahmen zur Optimierung der Erfolgsaussichten

Antworte fachlich und realistisch.
"""
        return prompt

    def _build_anomaly_detection_prompt(self, health_history: List[dict]) -> str:
        """Build health anomaly detection prompt"""

        # Vereinfachte Zusammenfassung der letzten 7 Tage
        summary = "\n".join([
            f"Tag {i+1}: Gewicht {r.get('weight')}g, Status: {r.get('condition')}"
            for i, r in enumerate(health_history[-7:])
        ])

        prompt = f"""
# Anomalieerkennung

## Letzte Gesundheitseinträge (7 Tage)
{summary}

## Aufgabe
Analysiere diese Gesundheitsdaten und identifiziere:
1. **Auffällige Trends**: Gewichtsverlust, Verhaltensänderungen
2. **Potenzielle Probleme**: Worauf sollte der Pfleger achten?
3. **Empfohlene Maßnahmen**: Sollte ein Tierarzt hinzugezogen werden?

Antworte prägnant und actionsorientiert.
"""
        return prompt

    def _default_recommendations(self) -> dict:
        """Default recommendations when LLM is unavailable"""
        return {
            "feeding": "Angepasstes Futterangebot basierend auf Art und Gewicht",
            "housing": "Ruhige, sichere Unterbringung mit Flugmöglichkeit",
            "monitoring": "Tägliche Gewichtskontrolle, Beobachtung des Verhaltens",
            "prevention": "Hygiene, Stressabbau, Sozialisation vorbereiten"
        }

    def _default_prognosis(self) -> dict:
        """Default prognosis when LLM is unavailable"""
        return {
            "probability": "Basierend auf Artenspezifika und Verlauf zu bewerten",
            "timeline": "Typischerweise 4-12 Wochen Rehabilitation",
            "risks": "Infektionen, unzureichende Fitness, Verhaltensprobleme"
        }

# Global LLM instance
_llm_instance: Optional[RaptorCareAI] = None

def get_llm() -> RaptorCareAI:
    """Get or create global LLM instance"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = RaptorCareAI()
    return _llm_instance
