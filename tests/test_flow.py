import unittest
from unittest.mock import patch, MagicMock
import os
import json
from src.main import EffectStokesOrchestrator

class TestPipelineFlow(unittest.TestCase):

    def setUp(self):
        # Ensure output directories exist for the test to write files
        self.output_dir = "/workspace/outputs"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "cache"), exist_ok=True)

    def _simulate_blender_output_creation(self, *args, **kwargs):
        # This function will be the side_effect for subprocess.run
        command_args = args[0] # The command list passed to subprocess.run

        # Extract output paths from the command arguments
        # This assumes the output path is always the last argument after '--'
        if '--' in command_args:
            separator_index = command_args.index('--')
            output_paths = command_args[separator_index + 1:]
        else:
            output_paths = []

        for out_path in output_paths:
            # Create dummy files for the test
            try:
                # Ensure parent directories exist
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with open(out_path, 'w') as f:
                    f.write(f"Mock content for {os.path.basename(out_path)}")
                print(f"[Test Mock] Created dummy file: {out_path}")
            except Exception as e:
                print(f"[Test Mock] Error creating dummy file {out_path}: {e}")
                # Re-raise to fail the test if file creation fails
                raise

        return MagicMock(stdout="Blender output", stderr="", returncode=0)

    @patch('src.llm_interface.LLMInterface') # Patch the LLMInterface class
    @patch('subprocess.run')
    def test_full_pipeline_flow_with_real_agents(self, mock_subprocess_run, MockLLMInterfaceClass):
        # Configure the mock instance of LLMInterface
        mock_llm_instance = MockLLMInterfaceClass.return_value

        # Mock the client attribute of the LLMInterface instance
        mock_llm_instance.client = MagicMock()
        mock_chat_completions_create = MagicMock()
        mock_llm_instance.client.chat.completions.create = mock_chat_completions_create

        # Configure side_effect for generate_code and generate_vision_feedback
        mock_chat_completions_create.side_effect = [
            # 1. For extract_vfx_params in parse_prompt
            MagicMock(choices=[MagicMock(message=MagicMock(content=json.dumps({"vfx_type": "fire punch", "style": "anime", "duration": 5, "colors": ["red", "black"], "camera_speed": "slow-motion"})))]),            # 2. For blender_simulation_script in SimulationAgent
            MagicMock(choices=[MagicMock(message=MagicMock(content="print(\"Mock Blender Simulation Script\")\nimport sys\nwith open(sys.argv[1], 'w') as f: f.write('blend_file_content')\nwith open(sys.argv[2], 'w') as f: f.write('sim_cache_content')"))]),            # 3. For blender_style_script in StyleAgent (first call)
            MagicMock(choices=[MagicMock(message=MagicMock(content="print(\"Mock Blender Style Script 1\")\nimport sys\nwith open(sys.argv[1], 'w') as f: f.write('styled_image_content_1')"))]),            # 4. For blender_style_script in StyleAgent (second call, after feedback)
            MagicMock(choices=[MagicMock(message=MagicMock(content="print(\"Mock Blender Style Script 2\")\nimport sys\nwith open(sys.argv[1], 'w') as f: f.write('styled_image_content_2')"))]),            # 5. For blender_final_render_script in RenderAgent
            MagicMock(choices=[MagicMock(message=MagicMock(content="print(\"Mock Blender Final Render Script\")\nimport sys\nwith open(sys.argv[1], 'w') as f: f.write('final_video_content')"))]),            # 6. For generate_vision_feedback (first call)
            MagicMock(choices=[MagicMock(message=MagicMock(content=json.dumps({"is_perfect": False, "suggestions": "Make it more vibrant", "updated_params": {"colors": ["red", "yellow", "vibrant"]}})))]),            # 7. For generate_vision_feedback (second call)
            MagicMock(choices=[MagicMock(message=MagicMock(content=json.dumps({"is_perfect": True, "suggestions": "", "updated_params": {}})))])
        ]
