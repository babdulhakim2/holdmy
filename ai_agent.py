from collections import deque
import time
import json
import vertexai
from vertexai.generative_models import GenerativeModel
from vertex_config import init_vertex

class AIAgent:
    def __init__(self, goal):
        # Initialize Vertex AI
        self.generation_config, self.safety_settings = init_vertex()
        self.model = GenerativeModel("gemma-2-27b-it")
        
        self.goal = goal
        self.state = "initial"
        self.context = deque(maxlen=10)
        self.last_audio_time = time.time()
        self.silence_duration = 0

    def analyze_text(self, text):
        print(f"\nAnalyzing text: {text}")
        prompt = f"""
        Goal: {self.goal}
        Current state: {self.state}
        Recent context: {' '.join(self.context)}
        New text: "{text}"

        Analyze the text and determine:
        1. Is this waiting music, an automated message, or human speech?
        2. What DTMF action, if any, should be taken?
        3. Should the call be transferred to a human operator? 
        4. What should the new state be?

        Respond with a JSON object containing 'text_type', 'dtmf_action', 'transfer', and 'new_state'.
        The response must be valid JSON.
        """

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
            )
            
            # Parse the response text as JSON
            result = json.loads(response.text)
            self.state = result.get('new_state', self.state)
            self.context.append(text)
            return result
            
        except Exception as e:
            print(f"Error in AI analysis: {str(e)}")
            return None

    def update_silence(self, duration):
        current_time = time.time()
        if current_time - self.last_audio_time > duration:
            print(f"\nSilence detected: {duration} seconds")
            self.state = "silence_detected"
        self.last_audio_time = current_time