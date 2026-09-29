from app.rag.chunker import DocumentChunker


def main():

    document = """
# Payment Service Database Connection Pool

## System Overview

The PaymentService uses a shared database connection pool.

The connection pool has a maximum capacity of 20 active connections.

## Connection Acquisition

Before processing a payment, PaymentService requests a connection
from DatabasePool.

If all 20 connections are already active, a new request cannot acquire
a connection until an existing connection is released.

## Failure Behavior

When no database connection is available, the request times out
after 3000 milliseconds.

The payment transaction then fails and is retried.
"""

    chunker = DocumentChunker(
        max_characters=300
    )

    chunks = chunker.chunk(
        document
    )

    print("\n" + "=" * 60)
    print("TRACEAI DOCUMENT CHUNKER")
    print("=" * 60)

    print(
        f"\nTotal chunks: {len(chunks)}"
    )

    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        print("\n" + "-" * 60)
        print(f"Chunk {index}")
        print(f"Characters: {len(chunk)}")
        print(chunk)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()