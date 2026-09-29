from app.rag.ollama_client import OllamaClient


def main():

    client = OllamaClient()

    prompt = """
You are a software debugging assistant.

Explain briefly why a database connection pool
can become exhausted.
"""

    response = client.generate(
        prompt
    )

    print("\n" + "=" * 60)
    print("TRACEAI LOCAL LLM TEST")
    print("=" * 60)

    print("\nModel:")
    print(client.model)

    print("\nResponse:")
    print(response)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()