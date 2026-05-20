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
        """Generate daily care recommendations."""

        prompt = f"""
You are an expert in raptor rehabilitation at a wildlife rescue station.
Based on the following bird data, provide detailed care recommendations in English:

🦅 **Bird data:**
- Species: {bird_data.get('species', 'Unknown')}
- Weight: {bird_data.get('weight', 'Unknown')} g
- Behavior: {bird_data.get('behavior', 'Unknown')}
- Hydration status: {bird_data.get('hydration_status', 'Unknown')}
- Days in care: {bird_data.get('days_in_care', 'Unknown')}

📋 **Provide specific guidance for:**
1. Diet and meal size
2. Activity support
3. Medical monitoring
4. Enclosure requirements
5. Release readiness indicators

Answer clearly and concisely in English.
"""

        result = self._call_ollama(prompt)
        return result or "Recommendation could not be generated."

    def generate_feeding_plan(self, bird_data: Dict) -> str:
        """Generate a feeding plan."""

        prompt = f"""
You are a specialist in raptor nutrition.
Create a detailed feeding plan for the following bird:

🦅 Species: {bird_data.get('species', 'Unknown')}
📊 Weight: {bird_data.get('weight', 'Unknown')} g
🎯 Rehabilitation status: {bird_data.get('status', 'Unknown')}

Please include:
1. Recommended prey type (whole/chopped)
2. Daily food amount
3. Feeding frequency
4. Feeding method (independent/assisted)
5. Nutrition goals for this week

Answer in English.
"""

        result = self._call_ollama(prompt)
        return result or "Feeding plan could not be generated."

    def analyze_health_anomalies(self, health_records: list) -> str:
        """Analyze health trends for anomalies."""

        # Prepare health summary
        health_summary = "\n".join([
            f"  - {record.get('date')}: Weight {record.get('weight')}g, "
            f"Behavior: {record.get('behavior')}"
            for record in health_records[-7:]  # Last 7 records
        ])

        prompt = f"""
You are a veterinarian specializing in raptors.
Analyze the following health data and identify potential concerns:

📅 **Last 7 days of health records:**
{health_summary}

🔍 Please identify:
1. Weight trends (gain or loss?)
2. Behavior patterns (normal/abnormal?)
3. Possible health issues
4. Recommended actions

Answer concisely in English.
"""

        result = self._call_ollama(prompt)
        return result or "Analysis could not be completed."

    def estimate_release_prognosis(self, bird_data: Dict, health_history: list) -> str:
        """Estimate prognosis for release."""

        days_in_care = bird_data.get('days_in_care', 0)

        prompt = f"""
You are an experienced raptor rehabilitation specialist with 20 years of field work.
Estimate the likelihood of a successful release:

🦅 **Bird:**
- Species: {bird_data.get('species', 'Unknown')}
- Current weight: {bird_data.get('weight', 'Unknown')} g
- Days in care: {days_in_care}
- Original injury: {bird_data.get('injury', 'Unknown')}

📊 **Health trend:**
{health_history[:3] if health_history else 'No data'}

🎯 **Please provide:**
1. Release probability (percentage)
2. Recommended release timing
3. Additional training required
4. Potential release risks

Answer in English.
"""

        result = self._call_ollama(prompt)
        return result or "Prognosis could not be generated."

    def generate_research_summary(
        self,
        bird_data: Dict,
        health_history: list,
        notes: Optional[str] = None
    ) -> str:
        """Generate a structured research summary for a bird case."""
        health_items = "\n".join([
            f"- {record.get('date', 'unknown')}: Weight {record.get('weight', '?')}g, Behavior: {record.get('behavior', 'unknown')}"
            for record in (health_history or [])[-7:]
        ]) or "No health data available."

        research_goal = notes or "Create a concise research report with hypotheses and recommendations."

        prompt = f"""
You are a scientific expert in raptor rehabilitation.
Create a structured research summary for the following case, including possible research questions:

🦅 Bird data:
- Species: {bird_data.get('species', 'Unknown')}
- Weight: {bird_data.get('weight', 'Unknown')} g
- Status: {bird_data.get('status', 'Unknown')}
- Days in care: {bird_data.get('days_in_care', 'Unknown')}
- Injury: {bird_data.get('injury', 'Unknown')}

📊 Health history (last 7 entries):
{health_items}

📌 Research objective:
{research_goal}

Please provide:
1. Brief case summary
2. Relevant research questions
3. Recommended observation and measurement parameters
4. Research-relevant conclusions
"""

        result = self._call_ollama(prompt)
        return result or "Research summary could not be generated."

    def generate_research_hypotheses(
        self,
        bird_data: Dict,
        health_history: list
    ) -> str:
        """Generate hypotheses and insight directions for research."""
        health_trend = "\n".join([
            f"- {record.get('date', 'unknown')}: Weight {record.get('weight', '?')}g, Condition: {record.get('behavior', 'unknown')}"
            for record in (health_history or [])[-7:]
        ]) or "No health data available."

        prompt = f"""
You are a research assistant for species and rehabilitation research specializing in raptors.
Based on the following information, formulate at least three testable hypotheses:

🦅 Bird profile:
- Species: {bird_data.get('species', 'Unknown')}
- Weight: {bird_data.get('weight', 'Unknown')} g
- Status: {bird_data.get('status', 'Unknown')}
- Days in care: {bird_data.get('days_in_care', 'Unknown')}

📈 Health and progress data:
{health_trend}

Please reply with clear, quantitatively or qualitatively testable hypotheses.
"""

        result = self._call_ollama(prompt)
        return result or "Research hypotheses could not be generated."

    def summarize_literature(self, text: str) -> str:
        """Summarize scientific or clinical text for research use."""
        prompt = f"""
You are a scientific editor for raptor and wildlife research.
Summarize the following text into a concise summary featuring key findings and possible research questions:

{text}

Answer in a structured way and do not cite sources, but clearly state the main points.
"""
        result = self._call_ollama(prompt)
        return result or "Literature summary could not be created."

    def analyze_research_trends(self, records: list) -> str:
        """Analyze trend data for potential research signals."""
        summary = "\n".join([
            f"- {item.get('date', 'unknown')}: {item.get('metric', 'N/A')}={item.get('value', 'N/A')}"
            for item in (records or [])[-10:]
        ]) or "No trend data available."

        prompt = f"""
You are an analytical scientist focused on rehabilitation data.
Analyze these trend data and identify key patterns, deviations, or research questions:

{summary}

Please provide a brief interpretation, possible causes, and suggestions for further research.
"""
        result = self._call_ollama(prompt)
        return result or "Trend analysis could not be completed."


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
                "species_detected": "Peregrine Falcon",
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
        "species": "Peregrine Falcon",
        "weight": 900,
        "behavior": "Alert, eating well",
        "hydration_status": "Good",
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
