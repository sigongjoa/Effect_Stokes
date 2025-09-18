import unittest
import os
import json
import sys
sys.path.append('/mnt/d/progress/Effect_Stokes/src')
from src.main import EffectStokesOrchestrator

class TestPipelineFlow(unittest.TestCase):

    def setUp(self):
        # Ensure output directories exist for the test to write files
        self.output_dir = os.path.join(os.getcwd(), 'local_test_outputs') # Changed for local testing
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "cache"), exist_ok=True)

    def test_full_pipeline_flow_with_real_services(self):
        # Orchestrator execution
        orchestrator = EffectStokesOrchestrator()
        final_output = orchestrator.run_pipeline("A slow-motion video of a powerful fire punch, in a demon-slayer anime style. The effect should last for 5 seconds, featuring vibrant red and black flames.")
        self.assertIsNotNone(final_output)
        self.assertIn("sim_cache_path", final_output)
        self.assertIn("blend_file_path", final_output)

        # Assertions
        # Check final output path
        self.assertIn("sim_cache_path", final_output)
        self.assertIn("blend_file_path", final_output)
        self.assertTrue(os.path.exists(final_output["sim_cache_path"]))
        self.assertTrue(os.path.exists(final_output["blend_file_path"]))

        

        # Clean up generated files (optional, but good practice for tests)
        # For simplicity, we'll rely on Docker volume cleanup or manual cleanup for now.

if __name__ == '__main__':
    unittest.main()