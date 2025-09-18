import os
import base64
import json
from llm_interface import LLMInterface
from prompt_templates import PROMPT_TEMPLATES

class FeedbackAgent:
    def __init__(self):
        self.llm = LLMInterface()

    def analyze_render(self, render_path: str, params: dict):
        print(f"[FeedbackAgent] Analyzing render: {render_path} with params: {params}")

        if not os.path.exists(render_path):
            raise FileNotFoundError(f"Render image not found at {render_path}")

        # 1. Read image and encode to base64
        try:
            with open(render_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            raise ValueError(f"Failed to encode image to base64: {e}")

        # 2. Generate vision feedback using LLM
        vision_feedback_json_str = self.llm.generate_vision_feedback(
            "vision_feedback",
            {"style": params.get("style", "")}, # Pass relevant params for feedback
            base64_image
        )

        if not vision_feedback_json_str:
            raise ValueError("Vision LLM failed to generate feedback.")

        # 3. Parse LLM's JSON response
        try:
            # Extract JSON part from LLM's response
            json_start = vision_feedback_json_str.find('{')
            json_end = vision_feedback_json_str.rfind('}') + 1
            if json_start == -1 or json_end == -1:
                raise ValueError("LLM response does not contain a valid JSON object.")
            
            feedback = json.loads(vision_feedback_json_str[json_start:json_end])
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Failed to decode Vision LLM response as JSON: {e}. Response: {vision_feedback_json_str}", e.doc, e.pos)
        except Exception as e:
            raise Exception(f"An unexpected error occurred during feedback parsing: {e}")

        # Ensure required keys are present
        if "is_perfect" not in feedback or "suggestions" not in feedback:
            raise ValueError("Vision LLM response missing 'is_perfect' or 'suggestions' keys.")

        # Add updated_params key if not present (for consistency)
        if "updated_params" not in feedback:
            feedback["updated_params"] = {}

        print(f"[FeedbackAgent] Analysis complete. Feedback: {feedback}")
        return feedback

    def apply_suggestions(self, current_params: dict, feedback: dict):
        print(f"[FeedbackAgent] Applying suggestions {feedback.get("suggestions")} to params: {current_params}")
        
        if not isinstance(current_params, dict) or not isinstance(feedback, dict):
            raise TypeError("current_params and feedback must be dictionaries.")

        # For now, we'll simply update current_params with any provided updated_params from feedback.
        # In a more sophisticated system, this would involve LLM-driven parameter modification.
        updated_params = current_params.copy()
        if "updated_params" in feedback and isinstance(feedback["updated_params"], dict):
            updated_params.update(feedback["updated_params"])

        print(f"[FeedbackAgent] Suggestions applied. New params: {updated_params}")
        return updated_params