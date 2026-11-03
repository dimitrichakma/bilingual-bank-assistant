# PLAN.md: Build plan

## Local model choices (Ollama, MacBook M4 16 GB)
1. qwen3.5:9b-mlx (main, already downloaded). Test with thinking off and on, report speed.
2. One smaller model for a speed versus accuracy comparison (check what Ollama has: a 3B or 4B).
Pick by testing on the 40 questions, not by guessing. Record speed and hardware for each.
Embedding model: bge-m3 only (ollama pull bge-m3).
Vector store: ChromaDB. Store faq_id, topic, English question and answer as metadata.

## Pipeline (fixed steps)
1. detect_language: Bangla script means bn. If banglish, also make a rewritten search query
   (options tested in Step 3). It is used for retrieval only. The reply stays banglish.
   Language rules (decided in Step 3): Bangla script means bn, checked in code. Latin letters:
   qwen decides en or banglish (word lists fail on new spellings). Any other answer means
   unknown, which hands off. Banglish retrieval uses option C: search the original question
   and a Bangla rewrite, keep the best score per FAQ entry.
2. retrieve: embed the question, find top 3 FAQ entries (question plus answer text).
3. gate: if the best score is below a threshold, hand off. Tune the threshold on the
   40 questions and report it. Also hand off for privacy topics (other people's accounts).
4. generate: small model gets ONLY the top entry, the customer question and the language.
   Prompt: answer only from this text, same language as the customer, short, polite.
   Banglish means Bangla written in English letters.
5. check: every number in the reply must appear in the FAQ entry. Reply language must match.
   If a check fails, hand off.
6. handoff reply, written in the customer language:
   en: I don't know, let me connect you to a person.
   bn: আমি জানি না, আপনাকে একজন প্রতিনিধির সাথে যুক্ত করে দিচ্ছি।
   banglish: Ami jani na, apnake ekjon protinidhir shathe jukto kore dichhi.

## Step 3 retrieval experiments (before adding the generator)
Report hit rate on the 30 covered questions, split by en, bn and banglish.
Embedding model is bge-m3 only. For the 13 banglish questions compare: no rewrite,
rewrite to Bangla, rewrite to English. Choose the best by data. Show the table in the note
and in the Loom. Not doing: embedding model comparison, multi vector index.

## Evaluation (eval/expected.csv)
Columns: id, question, language, expected_faq_id (or NONE), note.
I made a first draft. I must check it by hand, especially question 37 and question 13.
Metrics to report:
- Retrieval hit rate: right FAQ entry in top 1 (30 covered questions)
- Answer correct: facts match the FAQ entry (check by hand, mark in the csv)
- Correct "I don't know": out of the 10 NONE questions
- False handoff: covered questions wrongly handed off
- Language match rate (en, bn, banglish separately)
- Speed: average and slowest seconds per reply, and the hardware used
- Same 40 questions on one online model (see CLAUDE.md) with the SAME FAQ, prompt rules and scoring.
  Compare accuracy, "I don't know" behaviour, speed, and what the online model got wrong.
- Show the 3 to 5 worst failures honestly.

## Optional extra (only if time is left)
Fine tune the small model (LoRA, Unsloth on Colab) on Banglish bank questions and replies.
Make training data that does NOT use the 40 test questions. Compare before and after.
If skipped, say so in the note and list it under next steps.

## Deliverables checklist
- [ ] Local assistant works on all three languages
- [ ] Results on 40 questions, local versus online comparison table
- [ ] README: setup (Ollama, models), run, eval, folder map
- [ ] docs/NOTE.md one page: built, tested, results, what fails, next steps
- [ ] docs/LOOM_SCRIPT.md: 5 minute script for non technical viewers
- [ ] Optional: small demo UI (Streamlit or Gradio) with a language label on each reply

## Known failures to report in the note (found before the full run)
- Test Q20 (bn, minimum savings balance): retrieval ranks FAQ 1 (opening documents) above FAQ 2.
- Dimitri Q309 ("acc statement tulte chai"): retrieval ranks FAQ 29 (close account) above FAQ 11.
- Gate threshold 0.50 is fragile: highest no_match score and lowest covered score are both 0.486.
- Related but unanswered questions score like covered ones, so the score gate cannot stop them.
  They rely on CANNOT_ANSWER from the generator.
