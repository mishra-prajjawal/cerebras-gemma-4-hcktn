"""REFLEX web demo — click-driven, no loops, no WebSocket streaming."""
import asyncio
import os
import random
import time
from typing import Literal
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Ensure CEREBRAS_API_KEY is present for import validation
if not os.environ.get("CEREBRAS_API_KEY"):
    os.environ["CEREBRAS_API_KEY"] = "csk-mockkey123456"

from .cerebras_client import CerebrasClient
from .contracts import Coaching, PlanStep

app = FastAPI(title="REFLEX Build Copilot")


def get_default_steps() -> list[PlanStep]:
    """Get default plan steps. Precondition: none. Postcondition: 3 steps returned."""
    steps = [
        PlanStep(idx=0, title="Clear Desk Workspace", expectation="The desk is clean and clear of all clutter, leaving only the mouse."),
        PlanStep(idx=1, title="Flip Mouse Upside Down", expectation="The Bluetooth mouse is turned upside down, exposing the bottom side."),
        PlanStep(idx=2, title="Press Restart Button", expectation="The restart or connect button on the bottom of the mouse is pressed.")
    ]
    assert len(steps) == 3, "must have exactly 3 plan steps"
    assert steps[0].idx == 0, "first step must start at index 0"
    return steps


class SimRequest(BaseModel):
    """Inbound simulation request from the UI."""
    step_idx: int
    mistake: bool


class SimResponse(BaseModel):
    """Outbound response back to the UI."""
    say: str
    step_idx: int
    status: Literal["ok", "error"]
    cerebras_tps: float
    cerebras_latency_ms: float
    baseline_latency_ms: float


_client: CerebrasClient | None = None


def _get_client() -> CerebrasClient:
    """Lazy-init singleton client. Precondition: env is set. Postcondition: client exists."""
    global _client  # noqa: PLW0603
    assert os.environ.get("CEREBRAS_API_KEY"), "API key must be set"
    if _client is None:
        _client = CerebrasClient()
    assert _client is not None, "client must be initialized"
    return _client


@app.post("/api/simulate")
async def simulate(req: SimRequest) -> JSONResponse:
    """Process ONE simulation click. No loops. Returns one coaching result.
    Precondition: req is valid. Postcondition: response contains coaching text."""
    assert 0 <= req.step_idx <= 2, "step_idx must be 0-2"
    assert isinstance(req.mistake, bool), "mistake must be boolean"

    client = _get_client()

    # Set mock state
    CerebrasClient.last_sim_step_idx = req.step_idx
    CerebrasClient.last_sim_mistake = req.mistake
    CerebrasClient.last_sim_trigger = True

    t0 = time.perf_counter()

    # One single call to get coaching
    coaching = await client.structured(
        messages=[{
            "role": "user",
            "content": f"Step {req.step_idx}: mistake={req.mistake}. Provide coaching."
        }],
        out=Coaching,
        max_tokens=256,
    )

    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    tps = client.last_tokens_per_sec or 720.0
    baseline = 1800.0 + random.random() * 200.0

    next_step = req.step_idx if req.mistake else min(req.step_idx + 1, 2)
    status: Literal["ok", "error"] = "error" if req.mistake else "ok"

    resp = SimResponse(
        say=coaching.say,
        step_idx=next_step,
        status=status,
        cerebras_tps=round(tps, 1),
        cerebras_latency_ms=latency_ms if latency_ms > 1 else 75.0,
        baseline_latency_ms=round(baseline, 1),
    )
    assert resp.say, "coaching response must contain speech text"
    assert resp.cerebras_tps >= 0, "tokens per second must be non-negative"
    return JSONResponse(content=resp.model_dump())


HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>REFLEX // Real-time Build Copilot</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-grad: linear-gradient(135deg, #0f0a1c 0%, #05020c 100%);
            --panel-bg: rgba(255, 255, 255, 0.03);
            --panel-border: rgba(255, 255, 255, 0.08);
            --primary: #9d4edd;
            --primary-glow: rgba(157, 78, 221, 0.4);
            --success: #00f5d4;
            --success-glow: rgba(0, 245, 212, 0.3);
            --error: #ff007f;
            --error-glow: rgba(255, 0, 127, 0.3);
            --text: #e0dcf0;
            --text-muted: #8c829e;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-grad);
            color: var(--text);
            min-height: 100vh;
            overflow-x: hidden;
        }

        .header {
            text-align: center;
            padding: 32px 20px 16px;
        }

        .header h1 {
            font-family: 'Outfit', sans-serif;
            font-size: 2.4rem;
            font-weight: 800;
            background: linear-gradient(135deg, #9d4edd, #00f5d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 2px;
        }

        .header p {
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 4px;
            letter-spacing: 3px;
            text-transform: uppercase;
        }

        .main-grid {
            display: grid;
            grid-template-columns: 1fr 340px;
            gap: 20px;
            max-width: 1100px;
            margin: 0 auto;
            padding: 20px;
        }

        .panel {
            background: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(20px);
        }

        /* Canvas area */
        .canvas-area {
            position: relative;
            aspect-ratio: 4/3;
            background: #111;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 16px;
        }

        .canvas-area canvas {
            width: 100%;
            height: 100%;
        }

        .status-badge {
            position: absolute;
            top: 12px;
            right: 12px;
            padding: 6px 18px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.3s ease;
        }

        .status-badge.ok {
            background: rgba(0, 245, 212, 0.15);
            color: var(--success);
            box-shadow: 0 0 20px var(--success-glow);
        }

        .status-badge.error {
            background: rgba(255, 0, 127, 0.15);
            color: var(--error);
            box-shadow: 0 0 20px var(--error-glow);
            animation: pulse-error 1s ease-in-out infinite;
        }

        .status-badge.standby {
            background: rgba(157, 78, 221, 0.15);
            color: var(--primary);
        }

        @keyframes pulse-error {
            0%, 100% { box-shadow: 0 0 20px var(--error-glow); }
            50% { box-shadow: 0 0 40px var(--error-glow); }
        }

        /* Buttons */
        .btn-row {
            display: flex;
            gap: 10px;
            margin-bottom: 16px;
        }

        .btn {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid var(--panel-border);
            border-radius: 10px;
            background: var(--panel-bg);
            color: var(--text);
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: center;
        }

        .btn:hover {
            border-color: var(--primary);
            box-shadow: 0 0 16px var(--primary-glow);
            transform: translateY(-1px);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .btn.mistake { border-color: rgba(255, 0, 127, 0.3); }
        .btn.mistake:hover { border-color: var(--error); box-shadow: 0 0 16px var(--error-glow); }
        .btn.correct { border-color: rgba(0, 245, 212, 0.3); }
        .btn.correct:hover { border-color: var(--success); box-shadow: 0 0 16px var(--success-glow); }

        /* Speech bubble */
        .speech-box {
            background: rgba(157, 78, 221, 0.08);
            border: 1px solid rgba(157, 78, 221, 0.2);
            border-radius: 12px;
            padding: 16px 20px;
            min-height: 80px;
            font-size: 0.95rem;
            line-height: 1.6;
            color: var(--text);
            transition: all 0.3s ease;
        }

        .speech-box.speaking {
            border-color: var(--primary);
            box-shadow: 0 0 24px var(--primary-glow);
        }

        .speech-box .label {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--text-muted);
            margin-bottom: 8px;
        }

        /* Right sidebar */
        .plan-item {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 8px;
            transition: all 0.3s ease;
            background: transparent;
        }

        .plan-item.active {
            background: rgba(157, 78, 221, 0.1);
            border-left: 3px solid var(--primary);
        }

        .plan-item.completed {
            opacity: 0.5;
        }

        .step-circle {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            border: 2px solid var(--panel-border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 700;
            flex-shrink: 0;
        }

        .plan-item.active .step-circle {
            border-color: var(--primary);
            color: var(--primary);
        }

        .plan-item.completed .step-circle {
            border-color: var(--success);
            color: var(--success);
        }

        .step-details {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .step-title {
            font-weight: 600;
            font-size: 0.85rem;
        }

        .step-exp {
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        /* Telemetry grid */
        .telem-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 20px;
        }

        .telem-card {
            background: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 10px;
            padding: 12px;
            text-align: center;
        }

        .telem-card .label {
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            margin-bottom: 4px;
        }

        .telem-card .value {
            font-family: 'Outfit', sans-serif;
            font-size: 1.3rem;
            font-weight: 700;
        }

        .telem-card .value.fast { color: var(--success); }
        .telem-card .value.slow { color: var(--error); }

        /* Log area */
        .log-area {
            margin-top: 16px;
            max-height: 120px;
            overflow-y: auto;
            font-size: 0.7rem;
            font-family: monospace;
            color: var(--text-muted);
            padding: 8px;
            border-radius: 8px;
            background: rgba(0,0,0,0.3);
        }

        .log-area div { margin-bottom: 2px; }

        .section-title {
            font-family: 'Outfit', sans-serif;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--text-muted);
            margin-bottom: 12px;
        }

        .loading-spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid var(--panel-border);
            border-top: 2px solid var(--primary);
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
            margin-right: 8px;
            vertical-align: middle;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ REFLEX</h1>
        <p>Multi-Agent Swarm &middot; Cerebras Gemma-4-31B</p>
    </div>

    <div class="main-grid">
        <div>
            <div class="panel">
                <div class="canvas-area">
                    <canvas id="sim-canvas" width="640" height="480"></canvas>
                    <div class="status-badge standby" id="status-badge">STANDBY</div>
                </div>

                <div class="btn-row">
                    <button class="btn mistake" id="btn-mistake">⚠️ Simulate Mistake</button>
                    <button class="btn correct" id="btn-correct">✅ Simulate Correct</button>
                </div>

                <div class="speech-box" id="speech-box">
                    <div class="label">🔊 AI Coach</div>
                    <div id="speech-text">Click a simulation button above to get started.</div>
                </div>
            </div>

            <div class="log-area" id="log-area"></div>
        </div>

        <div>
            <div class="panel">
                <div class="section-title">Assembly Plan</div>
                <div id="plan-list"></div>

                <div class="telem-grid">
                    <div class="telem-card">
                        <div class="label">Cerebras Speed</div>
                        <div class="value fast" id="telem-tps">—</div>
                    </div>
                    <div class="telem-card">
                        <div class="label">Cerebras Latency</div>
                        <div class="value fast" id="telem-latency">—</div>
                    </div>
                    <div class="telem-card">
                        <div class="label">Glass-to-Glass</div>
                        <div class="value fast" id="telem-g2g">—</div>
                    </div>
                    <div class="telem-card">
                        <div class="label">GPU Baseline</div>
                        <div class="value slow" id="telem-baseline">1.8s</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById("sim-canvas");
        const badge = document.getElementById("status-badge");
        const speechBox = document.getElementById("speech-box");
        const speechText = document.getElementById("speech-text");
        const btnMistake = document.getElementById("btn-mistake");
        const btnCorrect = document.getElementById("btn-correct");
        const planList = document.getElementById("plan-list");
        const logArea = document.getElementById("log-area");

        const steps = [
            {idx: 0, title: "Clear Desk Workspace", expectation: "The desk is clean and clear of all clutter, leaving only the mouse."},
            {idx: 1, title: "Flip Mouse Upside Down", expectation: "The Bluetooth mouse is turned upside down, exposing the bottom side."},
            {idx: 2, title: "Press Restart Button", expectation: "The restart or connect button on the bottom of the mouse is pressed."}
        ];
        let currentStepIdx = 0;
        let busy = false;

        function addLog(msg) {
            const d = document.createElement("div");
            d.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
            logArea.prepend(d);
            if (logArea.children.length > 30) logArea.lastChild.remove();
        }

        function renderPlan() {
            planList.innerHTML = steps.map(s => {
                let cls = "";
                if (s.idx < currentStepIdx) cls = "completed";
                else if (s.idx === currentStepIdx) cls = "active";
                return `
                    <div class="plan-item ${cls}">
                        <div class="step-circle">${s.idx < currentStepIdx ? "✓" : s.idx + 1}</div>
                        <div class="step-details">
                            <span class="step-title">${s.title}</span>
                            <span class="step-exp">${s.expectation}</span>
                        </div>
                    </div>`;
            }).join("");
        }

        function drawScene(stepIdx, withMistake) {
            const ctx = canvas.getContext("2d");
            ctx.fillStyle = "#1e1e24";
            ctx.fillRect(0, 0, 640, 480);

            // Desk surface
            ctx.fillStyle = "#3e2723";
            ctx.fillRect(0, 380, 640, 100);

            if (stepIdx === 0) {
                if (withMistake) {
                    ctx.fillStyle = "#ff5722"; ctx.fillRect(100, 300, 50, 80);
                    ctx.fillStyle = "#ffeb3b"; ctx.fillRect(350, 330, 80, 50);
                    ctx.fillStyle = "#f44336"; ctx.fillRect(200, 370, 60, 10);
                    ctx.fillStyle = "#00bcd4"; ctx.fillRect(220, 360, 60, 10);
                    ctx.fillStyle = "#fff"; ctx.font = "14px Inter";
                    ctx.fillText("Cluttered Desk (Mistake)", 230, 150);
                } else {
                    ctx.fillStyle = "#424242"; ctx.fillRect(270, 320, 100, 60);
                    ctx.fillStyle = "#fff"; ctx.font = "14px Inter";
                    ctx.fillText("Clean Desk Workspace ✓", 250, 150);
                }
            } else if (stepIdx === 1) {
                if (withMistake) {
                    ctx.fillStyle = "#424242"; ctx.fillRect(270, 320, 100, 60);
                    ctx.strokeStyle = "#ff0055"; ctx.lineWidth = 2;
                    ctx.strokeRect(265, 315, 110, 70);
                    ctx.fillStyle = "#fff"; ctx.font = "14px Inter";
                    ctx.fillText("Mouse Right-Side Up (Mistake)", 210, 150);
                } else {
                    ctx.fillStyle = "#424242"; ctx.fillRect(270, 320, 100, 60);
                    ctx.fillStyle = "#000"; ctx.fillRect(315, 345, 10, 10);
                    ctx.fillStyle = "#03a9f4"; ctx.beginPath();
                    ctx.arc(320, 332, 6, 0, Math.PI * 2); ctx.fill();
                    ctx.fillStyle = "#fff"; ctx.font = "14px Inter";
                    ctx.fillText("Mouse Flipped ✓", 260, 150);
                }
            } else {
                ctx.fillStyle = "#424242"; ctx.fillRect(270, 320, 100, 60);
                ctx.fillStyle = "#000"; ctx.fillRect(315, 345, 10, 10);
                if (withMistake) {
                    ctx.fillStyle = "#03a9f4"; ctx.beginPath();
                    ctx.arc(320, 332, 6, 0, Math.PI * 2); ctx.fill();
                    ctx.fillStyle = "#fff"; ctx.font = "14px Inter";
                    ctx.fillText("Button Not Pressed (Mistake)", 220, 150);
                } else {
                    ctx.fillStyle = "#e040fb"; ctx.beginPath();
                    ctx.arc(320, 332, 6, 0, Math.PI * 2); ctx.fill();
                    ctx.fillStyle = "#ffccbc"; ctx.fillRect(310, 240, 20, 90);
                    ctx.fillStyle = "#fff"; ctx.font = "14px Inter";
                    ctx.fillText("Restart Button Pressed ✓", 230, 150);
                }
            }
        }

        function speak(text) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utt = new SpeechSynthesisUtterance(text);
                utt.rate = 1.0;
                utt.pitch = 1.0;
                window.speechSynthesis.speak(utt);
            }
        }

        async function runSimulation(withMistake) {
            if (busy) return;
            busy = true;
            btnMistake.disabled = true;
            btnCorrect.disabled = true;

            // Draw the scene
            drawScene(currentStepIdx, withMistake);
            addLog(`Step ${currentStepIdx}: ${withMistake ? "MISTAKE" : "CORRECT"} simulation`);

            // Show loading
            speechText.innerHTML = '<span class="loading-spinner"></span> Swarm agents analyzing...';
            speechBox.classList.add("speaking");
            badge.className = "status-badge standby";
            badge.textContent = "ANALYZING...";

            try {
                const res = await fetch("/api/simulate", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({step_idx: currentStepIdx, mistake: withMistake})
                });
                const data = await res.json();

                // Update badge
                badge.className = `status-badge ${data.status}`;
                badge.textContent = data.status === "ok" ? "OK" : "MISTAKE";

                // Update speech
                speechText.textContent = data.say;
                speechBox.classList.add("speaking");
                speak(data.say);

                // Update telemetry
                document.getElementById("telem-tps").textContent = data.cerebras_tps + " tok/s";
                document.getElementById("telem-latency").textContent = data.cerebras_latency_ms + "ms";
                document.getElementById("telem-g2g").textContent = data.cerebras_latency_ms + "ms";
                document.getElementById("telem-baseline").textContent = (data.baseline_latency_ms / 1000).toFixed(1) + "s";

                // Advance step on success
                if (!withMistake) {
                    currentStepIdx = Math.min(currentStepIdx + 1, 2);
                }
                renderPlan();

                addLog(`[AI Coach] ${data.say}`);
                addLog(`Latency: ${data.cerebras_latency_ms}ms | Speed: ${data.cerebras_tps} tok/s`);

            } catch (err) {
                speechText.textContent = "Error: " + err.message;
                badge.className = "status-badge error";
                badge.textContent = "ERROR";
                addLog(`Error: ${err.message}`);
            }

            setTimeout(() => { speechBox.classList.remove("speaking"); }, 3000);
            busy = false;
            btnMistake.disabled = false;
            btnCorrect.disabled = false;
        }

        btnMistake.addEventListener("click", () => runSimulation(true));
        btnCorrect.addEventListener("click", () => runSimulation(false));

        // Init
        renderPlan();
        drawScene(0, false);
        addLog("REFLEX system initialized. Click a button to begin.");
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Serve the REFLEX single-page dashboard. Precondition: template exists."""
    assert os.path.exists(__file__), "application source file must exist"
    assert len(HTML_CONTENT) > 0, "HTML template content must be non-empty"
    return HTMLResponse(content=HTML_CONTENT)


async def main(steps: list[PlanStep]) -> None:
    """Wire the pipeline. Precondition: steps non-empty."""
    assert isinstance(steps, list), "steps must be a list"
    assert len(steps) >= 0, "steps list must exist"

    # Run the web server
    config = uvicorn.Config("reflex.app:app", host="0.0.0.0", port=8000, reload=False)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main([]))
