import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import io from 'socket.io-client';

const API_BASE_URL = 'http://localhost:5000/api'; // Backend API URL
const SOCKET_IO_URL = 'http://localhost:5000'; // Socket.IO URL

const socket = io(SOCKET_IO_URL);

function App() {
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState('idle'); // idle, running, completed, failed, stopped
  const [progress, setProgress] = useState(0); // 0-100 for rendering progress
  const [currentStep, setCurrentStep] = useState(''); // simulation, blender_processing, rendering, etc.
  const [outputUrl, setOutputUrl] = useState(''); // URL to rendered frames/video
  const [gifUrl, setGifUrl] = useState(''); // URL to generated GIF
  const [effectDescription, setEffectDescription] = useState({
    vfx_type: "swirling vortex",
    style: "blue liquid",
  });

  // Default parameters (matching backend's defaults for now)
  const [simulationParams, setSimulationParams] = useState({
    grid_resolution: [101, 101],
    time_steps: 30,
    viscosity: 0.02,
    initial_shape_type: "vortex",
    initial_shape_position: [1.0, 1.0],
    initial_shape_size: 0.4,
    initial_velocity: [0.0, 0.0],
    boundary_conditions: "no_slip_walls",
    vortex_strength: 1.2,
    source_strength: 2.0,
  });

  const [visualizationParams, setVisualizationParams] = useState({
    arrow_color: [0.0, 0.0, 0.8],
    arrow_scale_factor: 3.0,
    arrow_density: 15,
    emission_strength: 50.0,
    transparency_alpha: 0.1,
    camera_location: [0, -5, 2], // Added for run_blender_oneshot.py
    light_energy: 3.0, // Added for run_blender_oneshot.py
    render_samples: 128, // Added for faster testing
  });

  // Recursive component to render and edit parameters
  const ParameterEditor = ({ params, setParams, path = [] }) => {
    const handleChange = (key, value) => {
      const newParams = { ...params };
      let current = newParams;
      for (let i = 0; i < path.length; i++) {
        current = current[path[i]];
      }

      if (Array.isArray(current)) {
        current[key] = value;
      } else {
        current[key] = value;
      }
      setParams(newParams);
    };

    const renderInput = (key, value) => {
      const currentPath = [...path, key];
      const label = currentPath.join('.');

      if (typeof value === 'object' && value !== null) {
        return (
          <div key={key} style={{ marginLeft: '20px' }}>
            <h4>{key}:</h4>
            <ParameterEditor params={value} setParams={setParams} path={currentPath} />
          </div>
        );
      } else if (Array.isArray(value)) {
        return (
          <div key={key} style={{ marginLeft: '20px' }}>
            <h4>{key}:</h4>
            {value.map((item, index) => (
              <div key={index}>
                <label>{`${label}[${index}]`}:</label>
                <input
                  type={typeof item === 'number' ? 'number' : 'text'}
                  value={item}
                  onChange={(e) => handleChange(index, typeof item === 'number' ? parseFloat(e.target.value) : e.target.value)}
                />
              </div>
            ))}
          </div>
        );
      } else {
        return (
          <div key={key}>
            <label>{label}:</label>
            <input
              type={typeof value === 'number' ? 'number' : 'text'}
              value={value}
              onChange={(e) => handleChange(key, typeof value === 'number' ? parseFloat(e.target.value) : e.target.value)}
            />
          </div>
        );
      }
    };

    return (
      <div>
        {Object.entries(params).map(([key, value]) => renderInput(key, value))}
      </div>
    );
  };

  useEffect(() => {
    socket.on('connect', () => {
      console.log('Connected to Socket.IO server');
      setLogs(prev => [...prev, 'Connected to server.']);
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from Socket.IO server');
      setLogs(prev => [...prev, 'Disconnected from server.']);
    });

    socket.on('pipeline_log', (data) => {
      setLogs(prev => [...prev, data.message]);
    });

    socket.on('pipeline_status', (data) => {
      setStatus(data.status);
      setCurrentStep(data.current_step);
      if (data.progress !== undefined) {
        setProgress(data.progress);
      }
      if (data.output_url) {
        setOutputUrl(data.output_url);
      }
      if (data.gif_url) {
        setGifUrl(data.gif_url);
      }
      setLogs(prev => [...prev, `Status: ${data.status} - ${data.message}`]);
    });

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('pipeline_log');
      socket.off('pipeline_status');
    };
  }, []);

  const handleInferParams = async () => {
    setLogs(prev => [...prev, 'Inferring parameters from LLM...']);
    try {
      const response = await axios.post(`${API_BASE_URL}/get_llm_inferred_params`, {
        effect_description: effectDescription,
      });
      if (response.data.status === 'success') {
        setSimulationParams(response.data.inferred_simulation_params);
        setVisualizationParams(response.data.inferred_visualization_params);
        setLogs(prev => [...prev, 'Parameters inferred successfully.']);
      } else {
        setLogs(prev => [...prev, `Parameter inference failed: ${response.data.message}`]);
      }
    } catch (error) {
      setLogs(prev => [...prev, `API Error during inference: ${error.response?.data?.message || error.message}`]);
    }
  };

  const handleRunPipeline = async () => {
    setLogs([]);
    setStatus('running');
    setProgress(0);
    setOutputUrl('');
    setGifUrl(''); // Clear previous GIF URL
    try {
      const response = await axios.post(`${API_BASE_URL}/run_pipeline`, {
        simulation_params: simulationParams,
        visualization_params: visualizationParams,
      });
      setLogs(prev => [...prev, `API Response: ${response.data.message}`]);
    } catch (error) {
      setLogs(prev => [...prev, `API Error: ${error.response?.data?.message || error.message}`]);
      setStatus('failed');
    }
  };

  const handleStopPipeline = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/stop_pipeline`);
      setLogs(prev => [...prev, `API Response: ${response.data.message}`]);
    } catch (error) {
      setLogs(prev => [...prev, `API Error: ${error.response?.data?.message || error.message}`]);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>VFX Pipeline Control</h1>
      </header>
      <div className="App-content">
        <div className="controls-panel">
          <h2>Effect Description</h2>
          <div>
            <label>VFX Type:</label>
            <input
              type="text"
              value={effectDescription.vfx_type}
              onChange={(e) => setEffectDescription({ ...effectDescription, vfx_type: e.target.value })}
            />
          </div>
          <div>
            <label>Style:</label>
            <input
              type="text"
              value={effectDescription.style}
              onChange={(e) => setEffectDescription({ ...effectDescription, style: e.target.value })}
            />
          </div>
          <button onClick={handleInferParams} disabled={status === 'running'}>
            Infer Parameters from LLM
          </button>

          <h2>Parameters</h2>
          <h3>Simulation Parameters</h3>
          <ParameterEditor params={simulationParams} setParams={setSimulationParams} />

          <h3>Visualization Parameters</h3>
          <ParameterEditor params={visualizationParams} setParams={setVisualizationParams} />

          <button onClick={handleRunPipeline} disabled={status === 'running'}>
            Run Pipeline
          </button>
          <button onClick={handleStopPipeline} disabled={status !== 'running'}>
            Stop Pipeline
          </button>
        </div>
        <div className="status-panel">
          <h2>Status: {status}</h2>
          <p>Current Step: {currentStep}</p>
          <p>Progress: {progress.toFixed(2)}%</p>
          <div className="log-console">
            <h3>Logs</h3>
            {logs.map((log, index) => (
              <p key={index}>{log}</p>
            ))}
          </div>
        </div>
        <div className="results-panel">
          <h2>Results</h2>
          {outputUrl && (
            <div>
              <h3>Rendered Frames</h3>
              {/* Image gallery/video player will go here */}
              <p>Output available at: {outputUrl}</p>
              {/* For now, just show a placeholder image */}
              <img src={`${outputUrl}/frame_0000.png`} alt="Rendered Frame" style={{ maxWidth: '100%', height: 'auto' }} />
            </div>
          )}
          {gifUrl && (
            <div>
              <h3>Generated GIF</h3>
              <img src={gifUrl} alt="Generated GIF" style={{ maxWidth: '100%', height: 'auto' }} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
