import pytest
import json
from backend.app import app, param_evaluator # Import app and param_evaluator

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_run_preview_fixed_params(client):
    test_params = {
        "simulation_params": {
            "viscosity": 0.02,
            "initial_shape_size": 0.4
        },
        "visualization_params": {
            "arrow_scale_factor": 3.0,
            "emission_strength": 50.0
        },
        "preview_settings": {
            "duration_frames": 5
        }
    }
    response = client.post('/api/run_preview', json=test_params)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'preview_data' in data
    assert len(data['preview_data']['frame_data']) == 5

    # Verify evaluated values for a fixed parameter
    for frame_data in data['preview_data']['frame_data']:
        assert frame_data['viscosity'] == 0.02
        assert frame_data['arrow_scale_factor'] == 3.0

def test_run_preview_function_params(client):
    test_params = {
        "simulation_params": {
            "viscosity": "0.02 + 0.01 * sin(t * 0.1)",
            "initial_shape_size": "0.4 + 0.1 * (t / 60)"
        },
        "visualization_params": {
            "arrow_scale_factor": "3.0 + 1.0 * sin(t * 0.2)",
            "emission_strength": "50.0 * (t / 60)"
        },
        "preview_settings": {
            "duration_frames": 5
        }
    }
    response = client.post('/api/run_preview', json=test_params)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'preview_data' in data
    assert len(data['preview_data']['frame_data']) == 5

    # Verify evaluated values for function parameters
    for i, frame_data in enumerate(data['preview_data']['frame_data']):
        t = i
        expected_viscosity = param_evaluator.evaluate("0.02 + 0.01 * sin(t * 0.1)", t=t)
        expected_initial_shape_size = param_evaluator.evaluate("0.4 + 0.1 * (t / 60)", t=t)
        expected_arrow_scale_factor = param_evaluator.evaluate("3.0 + 1.0 * sin(t * 0.2)", t=t)
        expected_emission_strength = param_evaluator.evaluate("50.0 * (t / 60)", t=t)

        assert frame_data['viscosity'] == pytest.approx(expected_viscosity)
        assert frame_data['initial_shape_size'] == pytest.approx(expected_initial_shape_size)
        assert frame_data['arrow_scale_factor'] == pytest.approx(expected_arrow_scale_factor)
        assert frame_data['emission_strength'] == pytest.approx(expected_emission_strength)

def test_run_preview_invalid_params(client):
    test_params = {
        "simulation_params": {
            "viscosity": "invalid_function("
        },
        "visualization_params": {},
        "preview_settings": {
            "duration_frames": 5
        }
    }
    response = client.post('/api/run_preview', json=test_params)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert "Parameter 'viscosity' is a string but not a valid mathematical expression." in data['message']

def test_run_preview_missing_params(client):
    test_params = {
        "simulation_params": {},
        "visualization_params": {},
        "preview_settings": {
            "duration_frames": 5
        }
    }
    response = client.post('/api/run_preview', json=test_params)
    assert response.status_code == 200 # Should still return 200 with defaults
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'preview_data' in data
    assert len(data['preview_data']['frame_data']) == 5

def test_get_llm_inferred_params_function_based(client):
    test_description = {"effect_description": "시간에 따라 세기가 줄어드는 푸른 소용돌이"}
    response = client.post('/api/get_llm_inferred_params', json=test_description)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'simulation_params' in data
    assert 'visualization_params' in data

    # Verify that some parameters are strings (functions) and others are numbers
    sim_params = data['simulation_params']
    viz_params = data['visualization_params']

    # Check for at least one function-based simulation parameter
    assert any(isinstance(v, str) for k, v in sim_params.items() if k in ["viscosity", "initial_shape_size", "vortex_strength", "source_strength"])
    # Check for at least one function-based visualization parameter
    assert any(isinstance(v, str) for k, v in viz_params.items() if k in ["arrow_scale_factor", "emission_strength"])

    # Optionally, check for some fixed parameters to ensure they are still numbers
    assert isinstance(sim_params.get("grid_resolution"), list)
    assert isinstance(viz_params.get("arrow_density"), int)
