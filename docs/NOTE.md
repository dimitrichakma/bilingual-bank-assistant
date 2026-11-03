# One page note: Nirbhor Bank offline assistant

## What I built
A chat assistant that answers customers in English, Bangla or Banglish using only the 30 entry bank FAQ.
It runs fully on my MacBook M4 (16 GB) with a small open model, `qwen3.5:9b-mlx`, through Ollama.
The steps are fixed: detect language, check for questions about other people, find the best FAQ entry
(bge-m3 and ChromaDB), a confidence gate in code (score 0.50), the model writes the reply from that one
entry, then a check that every number is in the FAQ and the language matches. Anything unsure hands off
with "I don't know, let me connect you to a person" in the customer's language. Built with LangChain and
LangGraph.

## How I tested it
The 40 official questions (30 covered, 10 not covered on purpose), unchanged. I marked each answer
correct or wrong by hand, and counted a reply with a wrong or garbled word as wrong. I also made 49 extra
practice questions, 122 questions for language detection and 16 for the privacy check. The same 40
questions ran on one online model, `claude-sonnet-5-5`, with the same FAQ, prompt, checks and scoring.

## Results (40 questions)
| | Local qwen 9B | Online Sonnet 5.5 |
|---|---|---|
| Correct, 30 covered (hand marked) | 22 of 30 | 27 of 30 |
| English / Bangla / Banglish | 10/10, 7/9, 5/11 | 10/10, 6/9, 11/11 |
| Correct "I don't know" (10 not covered) | 10 of 10 | 10 of 10 |
| Covered questions wrongly handed off | 2 of 30 | 3 of 30 |
| Speed, average and slowest | 4.7 s and 11.4 s | 2.4 s and 4.0 s |

The local time is the whole pipeline. The online time is the reply step only. Retrieval found the right
FAQ entry for 29 of 30 covered questions. Language detection was 122 of 122 with the model (a word list
got 119). The privacy check was 16 of 16. Searching a Banglish question with a Bangla rewrite got 25 of
25, against 22 of 25 with no rewrite.

Model choice: thinking mode was unusable (about 300 s per reply, 21 of 30 wrongly handed off). A 4B qwen
never handed off but wrote worse Banglish. Gemma3 4B often answered Banglish in English. Gemma 4 was
four times faster but handed off 9 of 38 extra questions and gave one wrong answer, so I kept qwen 9B.

## What does not work well
1. **Banglish quality.** The local model got only 5 of 11 Banglish answers right. Wrong or odd words
   ("pekhonshor"), and Q38 said the SMS comes after the deadline instead of before. Sonnet got 11 of 11.
2. **Meaning errors the checks cannot see.** Q6 said payment is due in the next month, but the FAQ says
   the same month. The number check passes because 25 is in the FAQ. Code cannot catch this.
3. **One retrieval miss.** Q20 (minimum savings balance) picked the account opening entry. The local
   model answered with the opening deposit, which is the wrong fact. Sonnet refused.
4. **A thin gate.** The highest score of a question not in the FAQ and the lowest score of a covered one
   are both 0.486. Threshold 0.50 sits just above. Related but unanswered questions score like covered
   ones (0.51 to 0.60), so they rely on the model saying `CANNOT_ANSWER`. It did for Q11, Q36 and Q37, but
   that is not a guarantee. The fourth, Q19, was stopped by its low score.
5. **Not fully repeatable.** Reply wording changed slightly between runs even at temperature 0, so my
   hand marks apply to the final run only. The 16 GB machine also stalled twice (207 s and 390 s on single
   calls) when memory was full.
6. **Honest limits of testing.** I tuned prompts after seeing the practice and test results, so the
   numbers are likely a little optimistic. 40 questions is small. Fine tuning (optional) was not done.

## Next steps
Collect fresh unseen questions for a fair final number. Fine tune the model on Banglish bank text with
LoRA and compare before and after. Add a check for meaning errors (for example before against after).
Try a larger local model on a bigger GPU. Add multi turn memory so follow up questions work.
