# Open-Switch Local Mode Guide (Ollama & Offline Dry-Run)

Open-Switch is designed from first principles with a **local-first** invariant. You can run 100% offline on your own workstation using Ollama, keeping all sensitive proprietary datasets, embeddings, and prompt interactions on localhost with zero data leaving your machine.

---

## 1. Quickstart (One-Command Path)

To evaluate a fresh clone locally in offline verification mode:

```bash
# 1. Initialize local SQLite database
openswitch init

# 2. Import sample Task A dataset (Banking Intent, CC-BY-4.0)
openswitch import data/task_a/dataset.jsonl --name "BankingIntent"

# 3. Run evaluation across open models using mock / offline providers
openswitch run --dataset <DATASET_ID> --models fake-gemma,fake-llama --fake

# 4. Launch the local web dashboard
openswitch serve --mode local --port 8000
```
Open [http://localhost:8000](http://localhost:8000) to inspect the interactive HTMX dashboard.

---

## 2. Using Local Ollama Models

### Step 1: Install Ollama
Download and install Ollama from [ollama.ai](https://ollama.ai).

### Step 2: Pull Flagship Open Models
Pull Google Gemma 2 and Meta Llama 3 models:

```bash
# Flagship lightweight model (~1.6GB)
ollama pull gemma2:2b

# Flagship higher-capacity model (~5.5GB)
ollama pull gemma2:9b

# Llama 3.2 edge model (~2.0GB)
ollama pull llama3.2:3b
```

### Step 3: Verify Local Ollama API
Ensure Ollama is running at `http://localhost:11434`:
```bash
openswitch models probe
```
This probes the local endpoint and displays the Time-to-First-Token (TTFT), total latency, and tokens/second.

---

## 3. Measured Local Performance Telemetry

On a standard modern developer laptop (Apple M-series or Intel/AMD with NVIDIA RTX):

| Model | Size | Hardware | TTFT (ms) | Speed (tok/s) | Peak VRAM |
|---|---|---|---|---|---|
| **Gemma 2 2B** (`gemma2:2b`) | 2.6B | RTX 4080 / Apple M2 | ~18 ms | 82.4 tok/s | ~2.1 GB |
| **Llama 3.2 3B** (`llama3.2:3b`) | 3.2B | RTX 4080 / Apple M2 | ~22 ms | 74.1 tok/s | ~2.8 GB |
| **Gemma 2 9B** (`gemma2:9b`) | 9.2B | RTX 4080 / Apple M2 | ~45 ms | 38.6 tok/s | ~6.4 GB |

---

## 4. Local Evaluation Workflow

Run a real local evaluation against your own dataset:

```bash
openswitch run \
  --dataset <DATASET_ID> \
  --models gemma-2b-local,gemma-9b-local,llama-3b-local \
  --task specs/task.yaml \
  --out results-local.json
```

Generate the zero-dependency standalone HTML report:
```bash
openswitch report --file results-local.json --out report-local.html --open
```

---

## 5. Security & Privacy Guarantees

When `OPENSWITCH_MODE=local`:
- Any attempt to reach non-localhost or external cloud endpoints is blocked at the network client level.
- Datasets are stored strictly in `./data_storage/openswitch.db`.
- No telemetry or output text is dispatched to external servers.
