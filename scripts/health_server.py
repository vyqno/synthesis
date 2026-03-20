"""Simple health check HTTP server, runs alongside the agent."""
from fastapi import FastAPI
import uvicorn
import threading

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "agent": "nexus", "version": "1.0.0"}

def start_health_server():
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="error")

if __name__ == "__main__":
    start_health_server()
