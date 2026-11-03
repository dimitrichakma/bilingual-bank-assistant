import sys

from src.assistant import Assistant
from src.generate import GEN_MODEL
from src.llm import OllamaProblem, check_ollama
from src.retrieve import EMBED_MODEL


def main() -> None:
    try:
        check_ollama(sorted({GEN_MODEL, EMBED_MODEL}))
        bot = Assistant()
    except OllamaProblem as e:
        sys.exit(f"Problem: {e}")
    print("Nirbhor Bank assistant (runs locally). Type 'quit' to exit.")
    while True:
        try:
            q = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in {"quit", "exit"}:
            break
        if not q:
            continue
        try:
            r = bot.ask(q)
        except Exception as e:
            # Example: Ollama stopped mid chat, or the 16 GB machine ran out of memory.
            # Keep the chat alive and say what to try, instead of crashing with a long traceback.
            print("Bot: Sorry, the local model failed on this question. Check that Ollama is running, "
                  "then try again.")
            print(f"     [error: {str(e).splitlines()[0][:150]}]")
            continue
        print(f"Bot: {r.reply}")
        print(f"     [{r.lang} | {r.status}:{r.reason} | faq {r.faq_id} | score {r.score} | {r.seconds}s]")


if __name__ == "__main__":
    main()
