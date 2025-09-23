import React, { createContext, useState, useContext } from 'react';

const ParameterContext = createContext();

export const ParameterProvider = ({ children }) => {
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
        camera_location: [0, -5, 2],
        light_energy: 3.0,
        render_samples: 128,
    });

    return (
        <ParameterContext.Provider value={{
            effectDescription,
            setEffectDescription,
            simulationParams,
            setSimulationParams,
            visualizationParams,
            setVisualizationParams,
        }}>
            {children}
        </ParameterContext.Provider>
    );
};

export const useParameters = () => useContext(ParameterContext);
