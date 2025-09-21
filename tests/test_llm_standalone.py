import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from llm_interface import LLMInterface
from prompt_templates import PROMPT_TEMPLATES # Import PROMPT_TEMPLATES to get extract_vfx_params

# Set the LLM API base URL (assuming Ollama is running on localhost:11434)
os.environ["LLM_API_BASE"] = "http://localhost:11434/v1"

def test_llm_standalone():
    llm_interface = LLMInterface()

    task_name = "extract_vfx_params"
    params = {
        "user_prompt": "A slow-motion video of a powerful fire punch, in a demon-slayer anime style. The effect should last for 5 seconds, featuring vibrant red and black flames."
    }

    print(f"Testing LLM with task: {task_name} and params: {params}")
    generated_response = llm_interface.generate_code(task_name, params)
    print("\n--- Generated Response ---\n")
    print(generated_response)
    print("\n--------------------------\n")


if __name__ == "__main__":
    test_llm_standalone()