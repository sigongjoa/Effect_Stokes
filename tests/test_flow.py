import unittest
from unittest.mock import patch
from src.main import EffectStokesOrchestrator

class TestPipelineFlow(unittest.TestCase):

    @patch('src.main.RenderAgent')
    @patch('src.main.FeedbackAgent')
    @patch('src.main.StyleAgent')
    @patch('src.main.SimulationAgent')
    @patch('src.main.LLMInterface') # LLMInterface도 모의해야 합니다.
    def test_full_pipeline_flow(self, MockLLMInterface, MockSimulationAgent, MockStyleAgent, MockFeedbackAgent, MockRenderAgent):
        # Mock 객체들이 API 명세에 맞는 모의 데이터를 반환하도록 설정
        MockLLMInterface.return_value.generate_code.return_value = '{"vfx_type": "fire", "style": "anime"}' # parse_prompt에서 사용
        MockSimulationAgent.return_value.run_simulation.return_value = {"sim_cache": "mock/sim_data"}
        MockStyleAgent.return_value.apply_style.side_effect = ["mock/styled_render_1.png", "mock/styled_render_2.png"]
        # 첫 번째 피드백은 개선 제안, 두 번째는 완료를 반환
        MockFeedbackAgent.return_value.analyze_render.side_effect = [
            {"is_perfect": False, "suggestions": "더 강하게!", "updated_params": {}},
            {"is_perfect": True}
        ]
        MockFeedbackAgent.return_value.apply_suggestions.return_value = {} # apply_suggestions도 모의해야 합니다.
        MockRenderAgent.return_value.finalize_render.return_value = "mock/final_video.mp4"

        # 오케스트레이터 실행
        orchestrator = EffectStokesOrchestrator()
        final_path = orchestrator.run_pipeline("test prompt")

        # 각 에이전트가 올바르게 호출되었는지 확인
        MockLLMInterface.return_value.generate_code.assert_called_once()
        MockSimulationAgent.return_value.run_simulation.assert_called_once()
        self.assertEqual(MockStyleAgent.return_value.apply_style.call_count, 2) # 최초 실행 + 피드백 후 재실행
        self.assertEqual(MockFeedbackAgent.return_value.analyze_render.call_count, 2)
        self.assertEqual(MockFeedbackAgent.return_value.apply_suggestions.call_count, 1) # 피드백이 한 번 적용됨
        MockRenderAgent.return_value.finalize_render.assert_called_once()
        self.assertEqual(final_path, "mock/final_video.mp4")

if __name__ == '__main__':
    unittest.main()