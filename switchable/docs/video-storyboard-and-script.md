# Demo Video Storyboard and Narration Script (60–90 Seconds)

**Target Video Duration**: 75–85 Seconds  
**Format**: 1080p, 60fps, 16:9 Screen Recording + Narration + Subtitles  
**Voice Narration**: ElevenLabs (Voice: "Adam" or "Rachel", Model: Eleven Multilingual v2)

---

## Scene-by-Scene Storyboard

### Scene 1: The Hook & The Problem (0:00 – 0:12)
- **Visual**: Camera starts on an actual cloud provider invoice dashboard showing ~$1,200/month LLM API spend, then zooms into a Slack message: *"Can we switch from GPT-4o-mini to an open model like Gemma 2 without breaking triage?"*
- **On-Screen Text**: *The $1,200/month question nobody can answer with public benchmarks.*
- **Spoken Voiceover**:  
  > "Every team wants to switch from expensive closed LLM APIs to open-weight models. But public leaderboards won't tell you how Gemma or Llama perform on *your* customer data—and a 2% drop could silently break production. This is Open-Switch."

---

### Scene 2: Upload & The Provenance Guard (0:12 – 0:26)
- **Visual**: Browser at `https://openswitch.tech`. User drags and drops `dataset.jsonl` (150 customer tickets). Instantly, the upload completes with line-by-line validation and a PII scan. When pointing to closed-API references, a red shield alerts: `[PROVENANCE GUARD] closed_api outputs detected. Training blocked.` User clicks **Regenerate via Open Teacher** (`gemma-9b`). The shield turns green.
- **On-Screen Text**: *Default-deny Provenance Guard. Comply with Terms of Service.*
- **Spoken Voiceover**:  
  > "Upload your proprietary dataset in JSONL or CSV. Open-Switch validates the schema, scans for sensitive PII, and enforces our default-deny Provenance Guard—preventing legal risk by blocking fine-tuning on closed API outputs until regenerated with an open teacher."

---

### Scene 3: Multi-Model Evaluation & Live Telemetry (0:26 – 0:42)
- **Visual**: User selects candidate models: Gemma 2 2B, Gemma 2 9B, Llama 3.2 3B, Qwen 2.5 7B. Sets baseline price ($0.25/1k) and monthly volume (65,000 reqs). Live progress bar updates via Server-Sent Events with real-time TTFT and latency meters.
- **On-Screen Text**: *Live SSE Streaming. Position-swapped automated judge.*
- **Spoken Voiceover**:  
  > "Select open models across local Ollama, DigitalOcean serverless, or Backboard. Open-Switch runs parallel evaluations with swapped-order judging to eliminate position bias, streaming live progress directly to the browser."

---

### Scene 4: Honest Statistics & The Break-Even Discovery (0:42 – 1:02)
- **Visual**: The standalone report renders. Camera pans across the interactive Pareto frontier SVG, the 10,000-resample bootstrap 95% confidence intervals, and the fine-tune vs k-shot comparison table. User drags the interactive monthly savings slider from 10k to 100k requests.
- **On-Screen Text**: *10k Bootstrap 95% CIs. Break-even: 10,238 requests/month.*
- **Spoken Voiceover**:  
  > "No single-point hype: every accuracy score carries an empirical 95% bootstrap confidence interval. And here's the breakthrough: while 3-shot prompting quadrupled inference cost from prompt bloat, a $1.03 Tinker LoRA fine-tune broke even in just 10,238 requests."

---

### Scene 5: Blind Judge Calibration & Local Mode (1:02 – 1:18)
- **Visual**: Screen shows the Calibration UI with 20 blind human labels, showing Cohen's kappa \(\kappa = 0.8479\) and the green `RELIABLE` badge. Terminal cuts to `openswitch serve --mode local` running 100% offline with Ollama at 82 tokens per second.
- **On-Screen Text**: *Calibrated Judge (Cohen's kappa = 0.848). 100% Offline Local Mode.*
- **Spoken Voiceover**:  
  > "Automated judges are calibrated against blind human ground truth to guarantee reliability. And for maximum privacy, run 100% offline with Ollama on your own workstation—zero bytes leave your laptop."

---

### Scene 6: Outro & Call to Action (1:18 – 1:25)
- **Visual**: Clean splash screen with live demo URL and GitHub link.
- **On-Screen Text**:  
  *Open-Switch: Know before you switch.*  
  *Live Demo: https://openswitch.tech*  
  *GitHub: github.com/adityagoyal/open-switch*
- **Spoken Voiceover**:  
  > "Stop guessing your migration risk. Audit your LLM bill with Open-Switch today. Live at openswitch.tech."

---

## Narration Generation Instructions (ElevenLabs)

1. Navigate to the ElevenLabs Speech Synthesis dashboard.
2. Select Voice: **Adam** (deep, crisp, authoritative engineering cadence).
3. Settings:
   - Stability: `55%`
   - Clarity + Similarity: `75%`
   - Style Exaggeration: `0%`
4. Copy the voiceover text from Scenes 1–6 above.
5. Export as `audio/demo_narration.mp3` and sync with video cuts.
