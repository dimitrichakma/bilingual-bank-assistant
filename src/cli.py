from src.assistant import Assistant


def main() -> None:
    bot = Assistant()
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
        r = bot.ask(q)
        print(f"Bot: {r.reply}")
        print(f"     [{r.lang} | {r.status}:{r.reason} | faq {r.faq_id} | score {r.score} | {r.seconds}s]")


if __name__ == "__main__":
    main()
