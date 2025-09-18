class RenderAgent:
    def finalize_render(self, final_render_path: str):
        print(f"[Mock] Finalizing render for: {final_render_path}")
        return "mock/final_video.mp4"