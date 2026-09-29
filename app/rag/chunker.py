class DocumentChunker:
    """
    Splits long documentation into smaller,
    semantically meaningful chunks.
    """

    def __init__(self, max_characters: int = 500):
        self.max_characters = max_characters

    def chunk(self, text: str) -> list[str]:

        sections = text.split("\n## ")

        chunks = []

        for index, section in enumerate(sections):

            if index == 0:
                chunk = section.strip()
            else:
                chunk = "## " + section.strip()

            if not chunk:
                continue

            if len(chunk) <= self.max_characters:
                chunks.append(chunk)
                continue

            # Split oversized sections by paragraphs
            paragraphs = chunk.split("\n\n")

            current = ""

            for paragraph in paragraphs:

                paragraph = paragraph.strip()

                if not paragraph:
                    continue

                if (
                    len(current)
                    + len(paragraph)
                    + 2
                    <= self.max_characters
                ):
                    if current:
                        current += "\n\n"

                    current += paragraph

                else:

                    if current:
                        chunks.append(
                            current.strip()
                        )

                    current = paragraph

            if current:
                chunks.append(
                    current.strip()
                )

        return chunks