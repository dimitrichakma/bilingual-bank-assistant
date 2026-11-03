# One page note: Nirbhor Bank offline assistant

Dimitri, BIAI Round 2, Task 2 | Code: https://github.com/dimitrichakma/bilingual-bank-assistant

## What I built
A chat assistant that answers in English, Bangla or Banglish using only the 30 entry bank FAQ. It runs
fully on my MacBook M4 (16 GB) with `qwen3.5:9b-mlx` through Ollama, built with LangChain and LangGraph.
The steps are fixed: detect language, check for questions about other people, find the best FAQ entry
(bge-m3 and ChromaDB), a code gate (score 0.50), the model writes the reply from that one entry, then a
check that every number is in the FAQ and the language matches. Anything unsure hands off with "I don't
know, let me connect you to a person" in the customer's language.

## How I tested it
The 40 official questions (30 covered, 10 not), unchanged. I marked every answer by hand; a wrong or
garbled word counts as wrong. I also used 49 extra practice questions, 122 for language detection and 16
for privacy. The same 40 ran on `claude-sonnet-5-5` with the same FAQ, prompt, checks and scoring.

## Results (40 questions)
| | Local qwen 9B | Online Sonnet 5.5 |
|---|---|---|
| Correct, 30 covered (hand marked) | 22 of 30 | 27 of 30 |
| English / Bangla / Banglish | 10/10, 7/9, 5/11 | 10/10, 6/9, 11/11 |
| Correct "I don't know" (10 not covered) | 10 of 10 | 10 of 10 |
| Covered questions wrongly handed off | 2 of 30 | 3 of 30 |
| Speed, average and slowest | 4.7 s and 11.4 s | 2.4 s and 4.0 s |

Local time is the whole pipeline, online time the reply step only. The right FAQ entry was found for
29 of 30 covered. Language detection by the model was 122 of 122 (a word list: 119). Privacy check 16 of
16. A Bangla rewrite for Banglish search got 25 of 25 against 22 of 25 without it.

Model choice: thinking mode took about 300 s per reply, a 4B qwen wrote worse Banglish, Gemma 3 often
replied in English, and Gemma 4 was 4 times faster but wrongly handed off 9 of 38 extra questions.
I kept qwen 9B.

## What does not work well
1. **Banglish quality.** Only 5 of 11 right locally: odd words ("pekhonshor"), and Q38 said the SMS
   comes after the deadline, not before. Sonnet got 11 of 11.
2. **Meaning errors the checks miss.** Q6 said payment is due next month, the FAQ says the same month.
   The number check passes because 25 is in the FAQ.
3. **One retrieval miss.** Q20 picked the account opening entry, and the local model gave the wrong fact.
4. **A thin gate.** The top score of an uncovered question and the lowest of a covered one are both 0.486,
   with the threshold at 0.50. Related but unanswered questions score 0.51 to 0.60, so Q11, Q36 and Q37
   rely on the model saying `CANNOT_ANSWER`, which is not guaranteed.
5. **Not repeatable.** Wording changed between runs even at temperature 0, so my marks fit the final
   run only. The 16 GB machine stalled twice (207 s and 390 s) when memory was full.
6. **Testing limits.** I tuned prompts after seeing the practice and test results, so the numbers are
   probably a little optimistic. 40 questions is small. Fine tuning (optional) was not done.

## Next steps
Test on fresh unseen questions. Fine tune on Banglish bank text (LoRA) and compare. Add a check for
meaning errors such as before against after. Try a larger local model. Add multi turn memory.
