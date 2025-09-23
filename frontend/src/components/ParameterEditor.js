
import React from 'react';

const ParameterEditor = ({ params, setParams, path = [] }) => {
  const handleParamChange = (key, value) => {
    // Create a deep copy of the params object to avoid direct mutation
    const newParams = JSON.parse(JSON.stringify(params));

    // Use a reference to navigate to the correct nesting level
    let current = newParams;
    for (let i = 0; i < path.length; i++) {
      current = current[path[i]];
    }

    // Update the value
    current[key] = value;

    // Update the state
    setParams(newParams);
  };

  const renderParameters = (currentParams, currentPath) => {
    return Object.entries(currentParams).map(([key, value]) => {
      const newPath = [...currentPath, key];
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        return (
          <div key={newPath.join('.')} style={{ marginLeft: '20px' }}>
            <h4>{key}</h4>
            {renderParameters(value, newPath)}
          </div>
        );
      }

      return (
        <div key={newPath.join('.')}>
          <label>{key}:</label>
          <input
            type={typeof value === 'number' ? 'number' : 'text'}
            value={value}
            onChange={(e) => {
              const newValue = typeof value === 'number' ? parseFloat(e.target.value) : e.target.value;
              handleParamChange(key, newValue);
            }}
          />
        </div>
      );
    });
  };

  return <div>{renderParameters(params, [])}</div>;
};

export default ParameterEditor;
