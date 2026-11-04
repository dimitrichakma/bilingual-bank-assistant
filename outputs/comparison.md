# Local vs online comparison (40 test questions)

Local: qwen3.5:9b-mlx, thinking off, Ollama on a MacBook M4 with 16 GB.
Online: claude-sonnet-5-5 (Claude Sonnet 5.5, Anthropic API). Used for this comparison only. The assistant never calls it.

## What was the same
Same FAQ, same 40 questions, same language detection, retrieval and gate (the local ones, cached),
same reply prompt and rules, same number check and language check. Only the model that writes the
reply is different. So retrieval mistakes (for example Q20) hit both models equally.

## What was different
- The online call has no temperature setting, because this SDK version rejects it. The online run is
  not forced to be repeatable. The local run uses temperature 0.
- Thinking is off for both. The online API needs `thinking: between_tools` to do that.
- The online model saw the same FAQ entry the local model saw, and nothing else.

## Results
Automatic numbers come from the scripts. Correct answers are hand marked by Dimitri for both runs (eval/expected.csv: answer_correct for local,
answer_correct_online for online).

| | Local: qwen3.5:9b-mlx | Online: claude-sonnet-5-5 |
|---|---|---|
| Covered questions answered (right FAQ entry) | 27/30 | 27/30 |
| False handoffs (covered, handed off) | 2/30 | 3/30 |
| Correct "I don't know" (NONE handed off) | 10/10 | 10/10 |
| Answer correct, hand marked, covered | 22/30 | 27/30 |
| English | 10/10 | 10/10 |
| Bangla | 7/9 | 6/9 |
| Banglish | 5/11 | 11/11 |
| Average seconds per reply | 4.7 (whole pipeline) | 2.4 (reply step only) |
| Slowest seconds | 11.4 (whole pipeline) | 4.0 (reply step only) |

The local numbers are from the final run of the assistant (the LangGraph version). The local time covers
everything: language check, privacy check, search, writing and checking the reply. The online time covers only the
step where the model writes the reply, so the two are not exactly equal. The online time also includes the network
and depends on the internet connection.

## Where the models differ
1. **Banglish quality is the big gap.** Local qwen 9B wrote garbled words ("pekhonshor"), and in Q38 said
   the SMS comes "poro" (after) the deadline. Sonnet wrote natural banglish in all 11 covered banglish
   questions and said "age" (before) correctly in Q38. This is why local is 5/11 and online is 11/11.
2. **Both models say "I don't know" correctly on all 10 NONE questions.** That includes the traps
   Q11, Q36 and Q37 (CANNOT_ANSWER) and the privacy question Q13 (stopped by the code rule).
3. **Local is cheaper and private.** No customer text leaves the computer. Online sends the question
   and one FAQ entry to an API.

## What the online model got wrong
- **Q10 and Q22 (Bangla): handed off by the number check.** Sonnet wrote a first draft, then "Wait... correction
  per rule 6" and a second draft in the same reply. The extra text broke the check, so the customer got
  "I don't know". The check worked as designed, but it shows the online model is not always clean about
  following a strict output rule. This is a real failure under these rules.
- **Q20 (Bangla): CANNOT_ANSWER.** Retrieval picked FAQ 1 (opening documents) instead of FAQ 2. Local also
  retrieved FAQ 1 and answered with the opening deposit, which is the wrong fact (marked 0). Sonnet refused.
  Here refusing is the safer behaviour, and it is the same retrieval error underneath.

## What the local model got wrong (hand marked 0)
Q3, Q6, Q7, Q20, Q23, Q25, Q31 and Q38. That is 8 of the 30 questions in the FAQ, so 22 of 30 are right.
* Banglish: Q7, Q23, Q31 and Q38 had garbled or wrong words, and Q38 put the SMS reminder after the deadline.
  Q3 and Q25 were handed off by mistake (the model said it could not answer, or replied in English).
* Q6 (Bangla) said the bill is due next month. The FAQ says the same month. The number check cannot see this.
* Q20 (Bangla) got the wrong FAQ entry, so it answered with the opening deposit.
See eval/expected.csv for the hand marks.

## Honest limits of this comparison
- 40 questions is a small sample. A difference of one or two questions is not meaningful.
- The prompts were tuned on qwen, not on Sonnet. This favours the local model.
- The online run is not repeatable at temperature 0, so rerunning may change a few replies.
- One online model was tested. Haiku 4.5 was not run.
