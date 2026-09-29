from app.retrieval.multi_source_loader import MultiSourceLoader


def main():
    loader = MultiSourceLoader(
        "data/incidents"
    )

    incident = loader.load_incident()

    print("\n" + "=" * 60)
    print("TRACEAI MULTI-SOURCE INCIDENT LOADER")
    print("=" * 60)

    print("\nLog Events:")
    print(f"  {len(incident['logs'])} events loaded")

    print("\nStack Trace:")

    if incident["stacktrace"]:
        stacktrace = incident["stacktrace"]

        print(
            f"  Exception: "
            f"{stacktrace['exception_type']}"
        )

        print(
            f"  Message  : "
            f"{stacktrace['exception_message']}"
        )

        print(
            f"  Frames   : "
            f"{len(stacktrace['frames'])}"
        )

    else:
        print("  No stack trace found")

    print("\nDocumentation:")

    if incident["documentation"]:
        print(
            f"  Source : "
            f"{incident['documentation']['source_file']}"
        )

        print(
            f"  Size   : "
            f"{len(incident['documentation']['content'])} characters"
        )

    else:
        print("  No documentation found")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()