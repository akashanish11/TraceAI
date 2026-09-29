import re


PYTHON_EXCEPTION_PATTERN = re.compile(
    r"^(?P<exception>[A-Za-z_][A-Za-z0-9_.]*):\s*(?P<message>.*)$"
)

JAVA_EXCEPTION_PATTERN = re.compile(
    r"^(?:Exception in thread .*?\s+)?"
    r"(?P<exception>(?:[A-Za-z_][A-Za-z0-9_]*\.)*[A-Za-z_][A-Za-z0-9_]*(?:Exception|Error))"
    r":\s*(?P<message>.*)$"
)

PYTHON_FRAME_PATTERN = re.compile(
    r'^\s*File\s+"(?P<file>[^"]+)",\s*'
    r"line\s+(?P<line>\d+),\s*in\s+(?P<function>.+)$"
)

JAVA_FRAME_PATTERN = re.compile(
    r"^\s*at\s+"
    r"(?P<class_method>[A-Za-z_][A-Za-z0-9_.$]*)"
    r"\((?P<location>[^)]*)\)"
)

METADATA_PATTERN = re.compile(
    r"^\s*(?P<key>[A-Za-z_][A-Za-z0-9 _-]*)\s*:\s*(?P<value>.+?)\s*$"
)


def _parse_python_frame(lines: list[str], index: int) -> tuple[dict | None, int]:
    """
    Parse a Python traceback frame.

    Example:

        File "services/payment_service.py", line 142, in process_payment
            connection = database_pool.acquire()
    """

    match = PYTHON_FRAME_PATTERN.match(lines[index])

    if not match:
        return None, index

    code = ""

    if index + 1 < len(lines):
        next_line = lines[index + 1]

        if next_line.startswith("    ") or next_line.startswith("\t"):
            code = next_line.strip()

    frame = {
        "file": match.group("file"),
        "line": int(match.group("line")),
        "function": match.group("function").strip(),
        "code": code,
    }

    return frame, index + 1


def _parse_java_frame(lines: list[str], index: int) -> tuple[dict | None, int]:
    """
    Parse a Java stack trace frame.

    Example:

        at com.example.recommendation.FeatureBuilder.buildMatrix(
            FeatureBuilder.java:214
        )
    """

    match = JAVA_FRAME_PATTERN.match(lines[index])

    if not match:
        return None, index

    class_method = match.group("class_method")
    location = match.group("location")

    file_name = location
    line_number = None

    if ":" in location:
        possible_file, possible_line = location.rsplit(":", 1)

        if possible_line.isdigit():
            file_name = possible_file
            line_number = int(possible_line)

    if "." in class_method:
        class_name, function_name = class_method.rsplit(".", 1)
    else:
        class_name = ""
        function_name = class_method

    code = f"{class_method}({location})"

    frame = {
        "file": file_name,
        "line": line_number,
        "function": function_name,
        "code": code,
        "class": class_name,
    }

    return frame, index + 1


def _extract_exception(lines: list[str]) -> tuple[str | None, str | None]:
    """
    Detect Python-style and Java-style exception declarations.
    """

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        # Java:
        # java.lang.NullPointerException: ...
        # java.lang.OutOfMemoryError: ...
        java_match = JAVA_EXCEPTION_PATTERN.match(stripped)

        if java_match:
            return (
                java_match.group("exception"),
                java_match.group("message").strip(),
            )

        # Python:
        # ConnectionPoolExhaustedError: ...
        python_match = PYTHON_EXCEPTION_PATTERN.match(stripped)

        if python_match:
            exception_name = python_match.group("exception")

            # Avoid interpreting metadata as exceptions.
            if (
                exception_name.endswith("Exception")
                or exception_name.endswith("Error")
            ):
                return (
                    exception_name,
                    python_match.group("message").strip(),
                )

    return None, None


def _extract_metadata(lines: list[str]) -> dict:
    """
    Extract metadata such as:

        Service: PaymentService
        Operation: process_payment
        User ID: USER-123
    """

    metadata = {}

    for line in lines:
        match = METADATA_PATTERN.match(line)

        if not match:
            continue

        key = match.group("key").strip().lower()
        value = match.group("value").strip()

        normalized_key = key.replace(" ", "_").replace("-", "_")

        metadata[normalized_key] = value

    return metadata


def parse_stacktrace(file_path: str) -> dict:
    """
    Parse Python and Java stack traces into a common structure.

    Supported:

    Python:
        Traceback (most recent call last):
          File "...", line 10, in function
            code
        ValueError: message

    Java:
        java.lang.NullPointerException: message
            at package.Class.method(File.java:87)
    """

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    lines = content.splitlines()

    exception_type, exception_message = _extract_exception(lines)

    frames = []

    index = 0

    while index < len(lines):

        # Python frame
        frame, next_index = _parse_python_frame(
            lines,
            index,
        )

        if frame:
            frames.append(frame)
            index = next_index
            continue

        # Java frame
        frame, next_index = _parse_java_frame(
            lines,
            index,
        )

        if frame:
            frames.append(frame)
            index = next_index
            continue

        index += 1

    metadata = _extract_metadata(lines)

    return {
        "source_file": file_path,
        "exception_type": exception_type,
        "exception_message": exception_message,
        "frames": frames,
        "metadata": {
            "service": metadata.get("service"),
            "operation": metadata.get("operation"),
            "order_id": metadata.get("order_id"),
            "user_id": metadata.get("user_id"),
            "dependency": metadata.get("dependency"),
        },
    }