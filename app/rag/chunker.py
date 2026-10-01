import re


class DocumentChunker:
    """
    Splits long documentation into smaller,
    semantically meaningful chunks.

    Markdown presentation syntax is normalized so that
    retrieved evidence contains clean text rather than
    raw Markdown formatting.
    """

    def __init__(self, max_characters: int = 500):
        self.max_characters = max_characters

    @staticmethod
    def _clean_markdown(text: str) -> str:
        """Remove lightweight Markdown presentation syntax."""
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"__(.*?)__", r"\1", text)
        return text.strip()

    def chunk(self, text: str) -> list[str]:

        sections = text.split("\n## ")

        chunks = []

        for index, section in enumerate(sections):

            chunk = section.strip()

            if not chunk:
                continue

            if len(chunk) <= self.max_characters:
                chunks.append(
                    self._clean_markdown(chunk)
                )
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
                            self._clean_markdown(
                                current.strip()
                            )
                        )

                    current = paragraph

            if current:
                chunks.append(
                    self._clean_markdown(
                        current.strip()
                    )
                )

        return chunks