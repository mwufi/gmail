import re


def format_markdown(markdown_text):
    # Remove trailing spaces from each line
    lines = [line.strip() for line in markdown_text.split("\n")]

    # Remove multiple blank lines
    formatted_lines = []
    prev_line_blank = False
    for line in lines:
        if line.strip() or not prev_line_blank:
            formatted_lines.append(line)
        prev_line_blank = not line.strip()

    # Add proper spacing for headers
    for i, line in enumerate(formatted_lines):
        if line.startswith("#"):
            header_level = len(line) - len(line.lstrip("#"))
            formatted_lines[i] = "#" * header_level + " " + line.lstrip("#").strip()

    # Ensure single blank line before and after code blocks
    in_code_block = False
    for i, line in enumerate(formatted_lines):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if i > 0 and formatted_lines[i - 1].strip() != "":
                formatted_lines.insert(i, "")
                i += 1
            if i < len(formatted_lines) - 1 and formatted_lines[i + 1].strip() != "":
                formatted_lines.insert(i + 1, "")

    # Ensure proper spacing for list items
    for i, line in enumerate(formatted_lines):
        if re.match(r"^\s*[-*+]\s", line):
            formatted_lines[i] = re.sub(r"^\s*([-*+])\s+", r"\1 ", line)

    # Join the lines back together
    formatted_markdown = "\n".join(formatted_lines)

    return formatted_markdown


# test by reading msg_46_html.md
if __name__ == "__main__":
    with open("msg_45_html.md", "r") as f:
        markdown_text = f.read()
    formatted_markdown = format_markdown(markdown_text)
    with open("msg_45_html_formatted.md", "w") as f:
        f.write(formatted_markdown)
    print("Formatted markdown saved to msg_45_html_formatted.md")
