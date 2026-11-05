# Local model against online model: the 40 test questions

I ran the bank's 40 test questions on two models and compared them. The first is my local model, `qwen3.5:9b-mlx`, which runs on my MacBook M4 with 16 GB through Ollama. The second is an online model, `claude-sonnet-5-5` (Claude Sonnet 5.5), which I reach through the Anthropic API. The online model is only for this comparison. The assistant never calls it.

## How I made the comparison fair
Everything is the same except the model that writes the reply. Both runs use the same FAQ, the same 40 questions, the same language detection, the same search and gate, the same reply prompt, and the same number and language checks. Because the search is shared, a search mistake (like Q20) hurts both models equally.

Three small differences you should know about:
* The online model has no temperature setting. The newest Claude models reject it, so the online run is not forced to be repeatable. The local run uses temperature 0.
* Thinking is off for both. For the online model this means sending `thinking: between_tools`.
* The online model saw only the one FAQ entry that the local model saw.

## Results
I marked every answer by hand. A reply with a wrong or strange word counts as wrong. My marks are in `eval/expected.csv`, in the columns `answer_correct` (local) and `answer_correct_online` (online).

| | Local: qwen3.5:9b-mlx | Online: claude-sonnet-5-5 |
|---|---|---|
| Correct answers (30 questions in the FAQ) | 22 of 30 | 27 of 30 |
| English | 10 of 10 | 10 of 10 |
| Bangla | 7 of 9 | 6 of 9 |
| Banglish | 5 of 11 | 11 of 11 |
| Correct "I don't know" (10 questions not in the FAQ) | 10 of 10 | 10 of 10 |
| FAQ questions wrongly passed to a person | 2 of 30 | 3 of 30 |
| Reply step, average and slowest | 5.0 s and 10.7 s | 2.4 s and 4.0 s |
| Whole assistant, average and slowest | 4.7 s and 11.4 s | not measured |

**How to read the speed rows.** The reply step is the fair comparison: it is the time the model needs to write the reply, plus the checks, for the same 33 questions. The local number comes from my model comparison run, which used the same prompt and checks. The online number includes the network, so it depends on the internet connection. The whole assistant row is the local time for everything, including the language check, the privacy check and the search. Questions stopped by the gate are very fast, which pulls that average down. The online run reused the local language check, privacy check and search, so there is no online number for that row.

## Where the two models differ
**Banglish is the big gap.** The local model got 5 of 11 right. It used strange words, like "pekhonshor", and in Q38 it said the SMS reminder comes after the deadline. The online model wrote natural Banglish in all 11 and said "age" (before) correctly in Q38. In English the two are equal.

**Both models handed off correctly on all 10 questions that are not in the FAQ.** That includes the tricky ones. Q11, Q36 and Q37 sound close to an FAQ entry, and the model stopped them by answering CANNOT_ANSWER. Q13 asks about a friend's balance, and my privacy rule stopped it.

**The local model keeps the data at home.** No customer text leaves the computer, and there is no fee per message. The online model gets the question and one FAQ entry through an API. I did not measure the cost of either.

## What the online model got wrong
* **Q10 and Q22 (Bangla).** Sonnet wrote a first draft, then wrote "Wait... correction per rule 6" and a second draft in the same reply. The extra text made the number check fail, so the customer got "I don't know". The check did its job, but it shows that the online model does not always follow a strict output rule.
* **Q20 (Bangla).** The search picked the account opening entry instead of the minimum balance entry. Sonnet answered CANNOT_ANSWER. The local model gave the opening deposit, which is the wrong fact. Here refusing was the safer choice, and the search mistake is the same for both.

## What the local model got wrong
It got 8 of the 30 FAQ questions wrong: Q3, Q6, Q7, Q20, Q23, Q25, Q31 and Q38.
* **Strange Banglish words:** Q7 ("otho"), Q23 ("pekhonshor"), Q31 ("onno") and Q38 ("poro", which also put the SMS reminder after the deadline).
* **Handed off by mistake:** Q3, where the model said it could not answer, and Q25, where the model replied in English so the language check stopped it.
* **A wrong meaning:** Q6 said the bill is due next month, but the FAQ says the same month. My number check cannot see this, because the number was right.
* **A wrong entry:** Q20, as described above.

## Other local models I tried
For these runs only the reply model changed, and the language check, search and gate stayed the same. They come from an earlier version of the assistant, written in plain Python, and they measure the reply step only.

| Model | Right entry answered (30 in the FAQ) | Wrongly handed off | Average and slowest | What happened |
|---|---|---|---|---|
| `qwen3.5:9b-mlx`, thinking off (my choice) | 27 of 30 | 2 | 5.0 s and 10.7 s | the cleanest Banglish of the local models, but still with odd words |
| `qwen3.5:9b-mlx`, thinking on | 8 of 30 | 21 | 305.7 s and 591.9 s | far too slow, and most replies did not finish |
| `qwen3.5:4b` | 29 of 30 | 0 | 8.6 s and 12.1 s | never handed off, but wrote worse Banglish |
| `qwen3.5:4b-mlx` | 29 of 30 | 0 | 7.1 s and 11.3 s | the same, a little faster |
| `gemma3:4b` | 21 of 30 | 8 | 3.9 s and 10.4 s | often answered Banglish in English (9 language failures) |
| `gemma4:e4b-mlx` | 28 of 30 | 1 | 1.0 s and 2.5 s | fast, see below |

I also ran the whole assistant on `gemma4:e4b-mlx`, so it did the language detection and the privacy check too. It was about four times faster, but its language detection was right on 119 of 122 questions (qwen 9B: 122), its privacy check on 13 of 16 (qwen 9B: 16), it wrongly handed off 9 of 38 extra practice questions that are in the FAQ (qwen 9B: 2), and it answered one question that is not in the FAQ. I tuned my prompts on qwen, which favours qwen. In the end I kept `qwen3.5:9b-mlx`.

## Limits of this comparison
* 40 questions is a small sample. A difference of one or two questions does not mean much.
* I tuned the prompts on qwen, not on Sonnet, so the comparison favours the local model.
* The online run is not repeatable, so running it again may change a few replies.
* I tested only one online model. I did not run Claude Haiku 4.5.
* My marks are from one run. If the local model is run again, some wording will change and the marks would need checking again.
