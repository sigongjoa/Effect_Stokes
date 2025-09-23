import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css'; // Keep App.css for general styling
import { ParameterProvider } from './context/ParameterContext';
import NavigationBar from './components/NavigationBar';
import PreviewPage from './pages/PreviewPage';
import FullPipelinePage from './pages/FullPipelinePage';

function App() {
  return (
    <Router>
      <ParameterProvider>
        <div className="App">
          <header className="App-header">
            <h1>VFX Pipeline Control</h1>
            <NavigationBar />
          </header>
          <div className="App-content">
            <Routes>
              <Route path="/" element={<Navigate to="/preview" replace />} />
              <Route path="/preview" element={<PreviewPage />} />
              <Route path="/full-pipeline" element={<FullPipelinePage />} />
            </Routes>
          </div>
        </div>
      </ParameterProvider>
    </Router>
  );
}

export default App;
