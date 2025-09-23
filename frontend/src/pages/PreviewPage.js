import React, { useState } from 'react';
import axios from 'axios';
import { useParameters } from '../context/ParameterContext';
import ParameterEditor from '../components/ParameterEditor';

const API_BASE_URL = 'http://localhost:5000/api';

const PreviewPage = () => {
  const { effectDescription, setEffectDescription, simulationParams, setSimulationParams, setVisualizationParams } = useParameters();
  const [logs, setLogs] = useState([]);
  const [previewFrames, setPreviewFrames] = useState([]);
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const [status, setStatus] = useState('idle');
  const [previewDurationFrames, setPreviewDurationFrames] = useState(30); // New state for preview duration

  const handleInferParams = async () => {
    setLogs(['Inferring parameters from LLM...']);
    setStatus('inferring');
    setPreviewFrames([]); // Clear frames
    setCurrentFrameIndex(0); // Reset slider
    try {
      const response = await axios.post(`${API_BASE_URL}/get_llm_inferred_params`, {
        effect_description: effectDescription,
      });
      if (response.data.status === 'success') {
        setSimulationParams(response.data.simulation_params);
        setVisualizationParams(response.data.visualization_params);
        setLogs(prev => [...prev, 'Parameters inferred successfully.']);
        setStatus('idle');
      } else {
        const errorMsg = `Parameter inference failed: ${response.data.message}`;
        setLogs(prev => [...prev, errorMsg]);
        console.error(errorMsg);
        setStatus('failed');
      }
    } catch (error) {
      const errorMsg = `API Error during inference: ${error.response?.data?.message || error.message}`;
      setLogs(prev => [...prev, errorMsg]);
      console.error(errorMsg);
      setStatus('failed');
    }
  };

  const handleRunPreview = async () => {
    setLogs(['Generating preview...']);
    setStatus('previewing');
    setPreviewFrames([]); // Clear frames
    setCurrentFrameIndex(0); // Reset slider
    try {
      const response = await axios.post(`${API_BASE_URL}/run_preview`, {
        simulation_params: simulationParams,
        preview_settings: { // Include preview settings
          duration_frames: previewDurationFrames,
        },
      });
      if (response.data.status === 'success') {
        setPreviewFrames(response.data.preview_data.frames);
        setLogs(prev => [...prev, 'Preview frames generated successfully.']);
        setStatus('idle');
      } else {
        const errorMsg = `Preview generation failed: ${response.data.message}`;
        setLogs(prev => [...prev, errorMsg]);
        console.error(errorMsg);
        setStatus('failed');
      }
    } catch (error) {
      const errorMsg = `API Error during preview: ${error.response?.data?.message || error.message}`;
      setLogs(prev => [...prev, errorMsg]);
      console.error(errorMsg);
      setStatus('failed');
    }
  };

  const handleSliderChange = (event) => {
    setCurrentFrameIndex(parseInt(event.target.value, 10));
  };

  return (
    <div className="page-content">
      <h2>1. Define & Preview Effect</h2>
      <div className="main-container">
        <div className="controls-panel">
          <h3>Effect Description</h3>
          <p>Describe the visual effect you want to create.</p>
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
          <button onClick={handleInferParams} disabled={status === 'inferring' || status === 'previewing'}>
            Infer Parameters from LLM
          </button>

          <h3>Simulation Parameters</h3>
          <p>Adjust the physical properties of the fluid simulation.</p>
          <ParameterEditor params={simulationParams} setParams={setSimulationParams} />

          <div style={{ marginTop: '20px' }}>
            <label htmlFor="previewDurationFrames">Preview Duration (Frames):</label>
            <input
              id="previewDurationFrames"
              type="number"
              value={previewDurationFrames}
              onChange={(e) => setPreviewDurationFrames(parseInt(e.target.value, 10))}
              min="1"
              max="100" // Set a reasonable max for frontend input
              style={{ marginLeft: '10px', width: '80px' }}
            />
          </div>

          <button onClick={handleRunPreview} disabled={status === 'inferring' || status === 'previewing'}>
            Generate Preview
          </button>
        </div>

        <div className="results-container">
          <div className="status-panel">
            <h3>Logs</h3>
            <div className="log-console" style={{ height: '150px', overflowY: 'scroll', border: '1px solid #ccc', padding: '10px', backgroundColor: '#f5f5f5' }}>
              {logs.map((log, index) => (
                <p key={index} style={{ margin: '0', fontFamily: 'monospace', fontSize: '12px' }}>{log}</p>
              ))}
            </div>
          </div>

          <div className="results-panel">
            <h3>Preview</h3>
            {status === 'previewing' && <p>Generating preview frames...</p>}
            {previewFrames.length > 0 ? (
              <>
                <img src={`data:image/png;base64,${previewFrames[currentFrameIndex]}`} alt="Simulation Preview" style={{ maxWidth: '100%', border: '1px solid #ddd' }} />
                <div style={{ marginTop: '10px' }}>
                  <input
                    type="range"
                    min="0"
                    max={previewFrames.length - 1}
                    value={currentFrameIndex}
                    onChange={handleSliderChange}
                    style={{ width: '100%' }}
                  />
                  <p>Frame: {currentFrameIndex + 1} / {previewFrames.length}</p>
                </div>
              </>
            ) : (
              <p>No preview generated yet. Click "Generate Preview" to see the simulation result.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PreviewPage;