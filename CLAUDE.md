# Project: Offline Bilingual Bank Assistant (BIAI Round 2, Task 2)

I am Dimitri. I direct the design and read your code, so explain why you wrote things.
Keep answers in simple English. Do not use dashes or hyphens in prose.
Read PLAN.md before you start. Read docs/BRIEF.md for the official task text.

## Goal
A chat assistant for a fictional bank (Nirbhor Bank). Customers write in English, Bangla
or Banglish (Bangla in English letters). It answers ONLY from data/bank-faq.csv, replies in
the SAME language the customer used, and runs on a small open model on my own computer
(or free Colab or Kaggle GPU). No customer data may go to online AI services.
If the FAQ has no answer, it says "I don't know, let me connect you to a person"
in the customer's language.

## My computer and models
MacBook M4, 16 GB RAM, Apple Silicon. Ollama installed.
Main local model: qwen3.5:9b-mlx. Turn off thinking mode (think false) for speed and clean replies.
Embedding model: bge-m3 only (via Ollama).
Online comparison model: claude-sonnet-5-5 (comparison only). Key in .env as ONLINE_API_KEY (ANTHROPIC_API_KEY also works).

## Hard rules (from the company brief)
1. The main assistant must run locally on a small open model (Qwen, Gemma, Llama or Phi).
2. Answer only from the FAQ. Never use outside knowledge. Never guess.
3. Reply language must match the question language (en, bn, banglish).
4. Test on the 40 questions in data/test-questions.csv. Some are NOT in the FAQ on purpose.
5. Run the same 40 questions on one online model and compare (online model is for the
   comparison only, never inside the assistant).
6. Report honestly: correct answers, correct "I don't know" rate, speed, and what fails.

## Design decisions (do not change without asking me)
- Pipeline in fixed steps: detect language, retrieve FAQ entries, confidence gate,
  generate answer from the retrieved entry, check answer, reply or hand off.
- Retrieval uses a multilingual embedding model so Bangla and Banglish match English FAQ.
- For banglish questions, test a rewritten search query (Bangla, English, or none). The rewrite is
  for retrieval only. The reply stays in the customer's own language.
- Do NOT build a multi vector index. I skip it. Never change the 40 test questions.
- The confidence gate is code (a score threshold), not the small model's opinion.
- The small model only writes the final reply from the retrieved FAQ text.
- Numbers, fees and phone numbers in the reply must appear in the retrieved FAQ entry.
  If not, hand off to a person. Never show a made up number.
- Banking data about other people (for example a friend's balance) always hands off.
- Fine tuning is optional. Do it only if the base results are done and time is left.

## Folder layout
- data/ : bank-faq.csv, test-questions.csv
- src/ : lang.py, retrieve.py, gate.py, generate.py, check.py, assistant.py, cli.py
- eval/ : expected.csv (my hand checked labels), run_eval.py, run_online.py
- outputs/ : results_local.csv, results_online.csv, comparison.md
- docs/ : BRIEF.md, NOTE.md (one page note), LOOM_SCRIPT.md

## Commands
- Use uv for everything. No pip. Add packages with: uv add <package>. Install with: uv sync
- Chat: uv run python -m src.cli
- Eval local: uv run python eval/run_eval.py
- Eval online: uv run python eval/run_online.py
- Tests: uv run pytest -q

## Working style
- Work in small steps. After each step, run it and show me the result.
- Put API keys in .env, never in code. Keep .env out of git.
- Add short comments that explain why, not what.
- When something is unclear, ask me. Do not invent an interpretation.
- Keep this file under 80 lines. Put detail in PLAN.md.
