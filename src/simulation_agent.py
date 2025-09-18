class SimulationAgent:
    def run_simulation(self, params: dict):
        print(f"[Mock] Running simulation with params: {params}")
        # Return a dictionary with 'sim_cache' key as expected by style_agent.apply_style
        return {"sim_cache": "mock/sim_data"}