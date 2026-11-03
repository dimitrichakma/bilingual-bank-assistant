Read CLAUDE.md, PLAN.md and docs/BRIEF.md first. Then look at everything in data/ and eval/.

Task: build the offline bilingual bank assistant described in PLAN.md.

Do it in this order. Stop after each step so I can review:
Step 1. Do not write code. Read the FAQ and the 40 questions. Show me a short table of the 10
        questions you think are NOT covered, and why. Check eval/expected.csv and tell me where
        you disagree. My computer details are in CLAUDE.md. Run ollama list and confirm the models are there.
        List any unclear points.
Step 2. Set up the project skeleton with uv (uv init --bare in this folder, then uv add for packages,
        pyproject.toml and uv.lock instead of requirements.txt). Tell me exactly what you ran. Make a first working CLI that loads the FAQ.
Step 3. Build detect_language and retrieve. Run the retrieval experiment in PLAN.md (banglish
        rewrite options, using bge-m3). Show me the hit rate tables before we add the generator.
Step 4. Build the gate. Show the score of every question so we can pick the threshold together.
Step 5. Build generate, check and the full assistant. Run the 40 questions. Show the results table.
Step 6. Compare qwen3.5:9b-mlx (thinking on and off) with one smaller model. Show me a speed and accuracy table. We pick one together.
Step 7. Build eval/run_online.py for the online model and write outputs/comparison.md.
Step 8. Write README.md, docs/NOTE.md and docs/LOOM_SCRIPT.md using the real results only.
Step 9. Only if time is left: the optional fine tuning.

Rules: the assistant answers only from the FAQ. The online model is for comparison only.
Unsure means hand off to a person. Explain briefly why you chose each design in simple English.
