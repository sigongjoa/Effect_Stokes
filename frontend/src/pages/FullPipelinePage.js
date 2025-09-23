import React, { useState, useEffect } from 'react';
import axios from 'axios';
import io from 'socket.io-client';
import { useParameters } from '../context/ParameterContext';
import ParameterEditor from '../components/ParameterEditor';

const API_BASE_URL = 'http://localhost:5000/api';
const SOCKET_IO_URL = 'http://localhost:5000';

const socket = io(SOCKET_IO_URL);

const FullPipelinePage = () => {
  const { simulationParams, visualizationParams } = useParameters();
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [outputUrl, setOutputUrl] = useState('');
  const [gifUrl, setGifUrl] = useState('');

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

  const handleRunPipeline = async () => {
    setLogs([]);
    setStatus('running');
    setProgress(0);
    setOutputUrl('');
    setGifUrl('');
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
    <div className="page-content">
      <h2>Run Full Pipeline</h2>
      <p>Parameters are inherited from the Preview page.</p>
      <div className="controls-panel">
        <button onClick={handleRunPipeline} disabled={status === 'running'}>
          Run Pipeline
        </button>
        <button onClick={handleStopPipeline} disabled={status !== 'running'}>
          Stop Pipeline
        </button>
      </div>

      <div className="status-panel">
        <h3>Status: {status}</h3>
        <p>Current Step: {currentStep}</p>
        <p>Progress: {progress.toFixed(2)}%</p>
        <div className="log-console" style={{ height: '200px', overflowY: 'scroll', border: '1px solid #ccc', padding: '10px' }}>
          <h3>Logs</h3>
          {logs.map((log, index) => (
            <p key={index} style={{ margin: '0' }}>{log}</p>
          ))}
        </div>
      </div>

      <div className="results-panel">
        <h3>Results</h3>
        {outputUrl && (
          <div>
            <h4>Rendered Frames</h4>
            <p>Output available at: {outputUrl}</p>
            <img src={`${outputUrl}/frame_0000.png`} alt="Rendered Frame" style={{ maxWidth: '100%', height: 'auto' }} />
          </div>
        )}
        {gifUrl && (
          <div>
            <h4>Generated GIF</h4>
            <img src={gifUrl} alt="Generated GIF" style={{ maxWidth: '100%', height: 'auto' }} />
          </div>
        )}
      </div>
    </div>
  );
};

export default FullPipelinePage;
