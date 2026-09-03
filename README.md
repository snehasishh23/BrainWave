# BrainWave

## Overview

BrainWave contains the implementation and evaluation artifacts for the assignment tasks.

The repository includes the Aria primary and fallback persona prompts, the Task 3 safety router, the Task 4 evaluation harness and its machine-readable results, and the Task 5 self-audit.

## Repository Structure

```text
BrainWave/
├── Task 1/
│   ├── aria_primary_persona.md
│   └── aria_fallback_persona.md
├── Task 2/
│   └── task2.md
├── Task 3/
│   └── task_3.py
├── Task 4/
│   ├── aria_primary_persona.md
│   ├── aria_fallback_persona.md
│   ├── task_4.py
│   ├── task4_final_raw_results.jsonl
│   └── task4_summary_2.json
├── Task 5/
│   └── task5_self_audit.md
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Create the local environment file:

```bash
cp .env.example .env
```

Open `.env` and provide your own Groq API key and model name.

**Never commit `.env` or a real API key to the repository.**

## Configuration

The Task 4 evaluation reads the following environment variables:

- `GROQ_API_KEY` — your Groq API key
- `GROQ_MODEL` — the Groq model used for evaluation
- `PRIMARY_PROMPT` — path to the primary persona prompt
- `FALLBACK_PROMPT` — path to the fallback persona prompt
- `TASK3_FILE` — path to the Task 3 implementation
- `TASK4_TRIALS` — number of trials per probabilistic condition

The default Task 4 configuration uses 10 trials per probabilistic condition.

## Running the Evaluation

From the repository root, run:

```bash
python "Task 4/task_4.py"
```

This is the documented command for running the Task 4 evaluation suite.

The evaluation is resumable. If execution is interrupted, the checkpoint can be used to resume completed trials rather than repeating them.

## Task 4 Evaluation

Task 4 evaluates the following risk areas:

- **Static prompt consistency**
- **R1 — Tool-usage guidance:** compares full, ablated, and tool-description-only conditions
- **R2 — Internal metadata leak prevention**
- **R3 — Retrieval-vocabulary leak prevention**
- **R4 — Tone/address consistency**
- **R5 — Session-language enforcement consistency**
- **R6 — Safety routing:** exercises the real Task 3 safety router

R1 uses primary/fallback full and ablated prompts plus a tool-description-only condition. R2 and R3 test whether internal information is exposed to customers. R4 and R5 compare primary and fallback persona behavior on the same inputs. R6 delegates to the Task 3 safety-routing implementation.

## Evaluation Outputs

The final machine-readable raw results are stored in:

```text
Task 4/task4_final_raw_results.jsonl
```

The evaluation summary is stored in:

```text
Task 4/task4_summary_2.json
```

## Self-Audit

The written self-audit is stored in:

```text
Task 5/task5_self_audit.md
```

## Security

- Do not commit real Groq API keys.
- Keep `.env` local.
- Use `.env.example` as the configuration template.
- Runtime checkpoints and Python cache files should not be committed.
