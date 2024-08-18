import html2text
import requests
from bs4 import BeautifulSoup


def html_to_markdown(html_content, base_url=None, with_images=False):
    # Create an instance of HTML2Text
    h = html2text.HTML2Text()

    # Configure the converter
    h.ignore_links = True
    h.ignore_images = not with_images
    h.ignore_emphasis = False
    h.body_width = 0  # Don't wrap lines

    if base_url:
        h.baseurl = base_url

    # Convert HTML to Markdown
    markdown = h.handle(html_content)

    # Remove "|"
    markdown = markdown.replace("|", "")

    # Remove excessive "---" (and longer)
    markdown = markdown.replace("---", "")

    # Remove too many spaces
    markdown = markdown.replace("   ", "")

    return markdown


def clean_html(html_content):
    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text
    text = soup.get_text()

    # Break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())

    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

    # Drop blank lines
    text = "\n".join(chunk for chunk in chunks if chunk)

    return text


def convert_html_file_to_markdown(file_path, output_path):
    with open(file_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    markdown = html_to_markdown(html_content)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(markdown)


def to_markdown_file(html_string, output_path):
    markdown = html_to_markdown(html_string)
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(markdown)
    print(f"Markdown file created at {output_path}")


def convert_url_to_markdown(url, output_path):
    response = requests.get(url)
    html_content = response.text

    markdown = html_to_markdown(html_content, base_url=url)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(markdown)


# Example usage
if __name__ == "__main__":
    # Convert HTML file to Markdown
    convert_html_file_to_markdown("msg_6_html.txt", "output.md")

    # Convert URL to Markdown
    convert_url_to_markdown("https://example.com", "example_com.md")

    # Convert HTML string to Markdown
    html_string = "<h1>Hello, World!</h1><p>This is a <b>test</b>.</p>"
    markdown_string = html_to_markdown(html_string)
    print(markdown_string)

    # Clean HTML and convert to plain text
    cleaned_text = clean_html(html_string)
    print(cleaned_text)
