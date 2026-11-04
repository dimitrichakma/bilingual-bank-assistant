# One page note: Nirbhor Bank offline assistant

Dimitri, BIAI Round 2, Task 2 | Code: https://github.com/dimitrichakma/bilingual-bank-assistant

## What I built
I built a chat assistant for a bank. Customers write in English, Bangla or Banglish (Bangla typed with English letters), and the assistant replies in the same language. It answers only from the bank's list of 30 questions and answers (the FAQ), and it runs on my own MacBook M4 (16 GB), so no customer text goes to an outside service. The model is `qwen3.5:9b-mlx`, run through Ollama. Search uses `bge-m3` and ChromaDB, and LangChain and LangGraph connect the steps.

Every question goes through the same steps, in this order:
1. Find the language, and check if the customer asks about someone else's account. If yes, pass them to a person.
2. Find the best matching FAQ entry. If the match is weak, my code passes the customer to a person.
3. The model writes a reply using only that one FAQ entry.
4. I check the reply: every number must be in the FAQ entry, and the language must match. If anything looks wrong, the customer gets "I don't know, let me connect you to a person" in their own language.

## How I tested it
I used the 40 official questions unchanged: 30 are in the FAQ and 10 are not. I marked every answer by hand, and a wrong or strange word counts as wrong. I also made 49 practice questions, 122 for language detection and 16 for privacy. The online model `claude-sonnet-5-5` got the same 40 questions, FAQ, prompt and marking.

## Results
| | Local: qwen3.5:9b-mlx | Online: claude-sonnet-5-5 |
|---|---|---|
| Correct answers (30 questions in the FAQ, hand marked) | 22 of 30 | 27 of 30 |
| Correct answers by language: English / Bangla / Banglish | 10/10, 7/9, 5/11 | 10/10, 6/9, 11/11 |
| Correct "I don't know" (10 questions not in the FAQ) | 10 of 10 | 10 of 10 |
| In the FAQ but wrongly passed to a person | 2 of 30 | 3 of 30 |
| Time per reply, average and slowest | 4.7 s and 11.4 s | 2.4 s and 4.0 s |

Local time covers the whole assistant. Online time covers only the reply writing step. Other things I measured:
* Finding the right FAQ entry worked for 29 of 30 FAQ questions.
* Finding the language was right for all 122 test questions (a simple word list got 119), and the check for someone else's account was right for all 16.
* For Banglish, I also translate the question into Bangla and search with both versions. This found the right entry for 25 of 25 questions, against 22 of 25 with the original only.

I tried other local models for writing replies. `qwen3.5:9b-mlx` with thinking on took about 300 seconds per reply, `qwen3.5:4b` wrote worse Banglish, `gemma3:4b` often answered in English, and `gemma4:e4b-mlx` was faster but wrongly passed 9 of 38 extra questions to a person. I kept `qwen3.5:9b-mlx` with thinking off.

## What does not work well
1. **Banglish answers are often poor.** The local model got only 5 of 11 Banglish questions right. It sometimes used strange words, like "pekhonshor", and in Q38 it put the SMS reminder after the deadline, not before. The online model got all 11.
2. **A wrong reply can slip through.** In Q6 the reply said the bill is due next month, but the FAQ says the same month. My check only looks at numbers, and 25 was right, so it got through.
3. **Once it looked at the wrong FAQ entry.** For Q20 (minimum savings balance) the search picked the account opening entry, so the answer gave the opening deposit instead.
4. **The "I don't know" score rule is not a clean line.** Every question gets a match score from 0 to 1 for how close it is to an FAQ entry. If the best score is below 0.50, the assistant says "I don't know". This works for unrelated questions, like the gold price, which scored 0.486 or less. But one real practice question, written in slang, also scored 0.486 and was blocked by mistake. The bigger problem is questions that sound like an FAQ topic but are not answered by it. Q11, Q36 and Q37 scored 0.51 to 0.60, so the score could not stop them. Only the model saying it could not answer did, which is not guaranteed.
5. **My testing has limits.** The wording changed between runs even with randomness off, so my marks match the final run only. I changed prompts after seeing the test results, so my scores may look a bit better than on new questions. 40 questions is a small sample, I did not do the optional fine tuning, and the laptop froze twice (207 s and 390 s).

**What I would do next:** test on new questions, fine tune on Banglish banking text, check for meaning mistakes like before and after, try a bigger model, and add chat memory.
