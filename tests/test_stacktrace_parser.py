from app.parsers.stacktrace_parser import parse_stacktrace


def main():
    file_path = "data/incidents/incident_001.stacktrace"

    result = parse_stacktrace(file_path)

    print("\n" + "=" * 60)
    print("TRACEAI STACK TRACE PARSER")
    print("=" * 60)

    print("\nException:")
    print(f"  Type    : {result['exception_type']}")
    print(f"  Message : {result['exception_message']}")

    print("\nStack Frames:")

    for frame in result["frames"]:
        print(f"  File     : {frame['file']}")
        print(f"  Line     : {frame['line']}")
        print(f"  Function : {frame['function']}")
        print(f"  Code     : {frame['code']}")
        print()

    print("Metadata:")

    for key, value in result["metadata"].items():
        print(f"  {key} : {value}")

    print("=" * 60)


if __name__ == "__main__":
    main()