# /tests/test_flow.py
import unittest
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from unittest.mock import patch
from main import EffectStokesOrchestrator

class TestPipelineFlow(unittest.TestCase):

    @patch('simulation_agent.SimulationAgent.run_simulation')
    @patch('style_agent.StyleAgent.apply_style')
    @patch('feedback_agent.FeedbackAgent.analyze_render')
    @patch('render_agent.RenderAgent.finalize_render')
    def test_full_pipeline_flow(self, mock_finalize, mock_analyze, mock_apply_style, mock_run_sim):
        # Mock 객체들이 API 명세에 맞는 모의 데이터를 반환하도록 설정
        mock_run_sim.return_value = "mock/sim_data"
        mock_apply_style.return_value = "mock/styled_render.png"
        # 첫 번째 피드백은 개선 제안, 두 번째는 완료를 반환
        mock_analyze.side_effect = [
            {"is_perfect": False, "suggestions": "더 강하게!", "updated_params": {}},
            {"is_perfect": True}
        ]
        mock_finalize.return_value = "mock/final_video.mp4"

        # 오케스트레이터 실행
        orchestrator = EffectStokesOrchestrator()
        final_path = orchestrator.run_pipeline("test prompt")

        # 각 에이전트가 올바르게 호출되었는지 확인
        self.assertTrue(mock_run_sim.called)
        self.assertEqual(mock_apply_style.call_count, 2) # 최초 실행 + 피드백 후 재실행
        self.assertEqual(mock_analyze.call_count, 2)
        self.assertTrue(mock_finalize.called)
        self.assertEqual(final_path, "mock/final_video.mp4")

if __name__ == '__main__':
    unittest.main()
