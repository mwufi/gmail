import base64
from cleaner import clean_html
from convert_to_markdown import to_markdown_file


def decode_content(data):
    return base64.urlsafe_b64decode(data).decode("utf-8")


def process_part(part):
    if part["mimeType"] == "text/plain":
        return decode_content(part["body"]["data"]), None
    elif part["mimeType"] == "text/html":
        return None, decode_content(part["body"]["data"])
    return None, None


def save_content(content, content_type, request_id):
    if content:
        filename = f"msg_{request_id}_{id}_{content_type}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        filesize = len(content) // 6
        print(
            f"{content_type.capitalize()} content saved to {filename} ({filesize} length)"
        )


def process_message(request_id, response, exception):
    if exception is not None:
        print(f"An error occurred: {exception}")
        return

    id = response["id"]

    # Check if the message is a draft
    if "DRAFT" in response.get("labelIds", []):
        return

    # Extract relevant information from the message
    payload = response["payload"]
    headers = payload["headers"]

    # Get the subject and sender
    subject = next(
        (header["value"] for header in headers if header["name"].lower() == "subject"),
        "No Subject",
    )
    sender = next(
        (header["value"] for header in headers if header["name"].lower() == "from"),
        "Unknown Sender",
    )

    # Print out the parts of the message
    print("Message parts:")
    for part in payload.get("parts", []):
        print(f"- {part['mimeType']}")

    plain_content, html_content = None, None
    for part in payload.get("parts", []):
        if part["mimeType"] == "multipart/alternative":
            for subpart in part.get("parts", []):
                plain, html = process_part(subpart)
                plain_content = plain_content or plain
                html_content = html_content or html
        else:
            plain, html = process_part(part)
            plain_content = plain_content or plain
            html_content = html_content or html

    if not plain_content and not html_content:
        body_data = payload.get("body", {}).get("data", "")
        if body_data:
            content = decode_content(body_data)
            if payload.get("mimeType") == "text/plain":
                plain_content = content
            elif payload.get("mimeType") == "text/html":
                html_content = content

    if html_content:
        cleaned_html = clean_html(html_content)
        to_markdown_file(
            cleaned_html, f"msg_{request_id}_{id}_html.md", with_images=False
        )
        # save_content(cleaned_html, "html", request_id)
    elif plain_content:
        save_content(plain_content, "plain", request_id)
    else:
        print("No message body found")

    print(f"Subject: {subject}")
    print(f"From: {sender}")
    print("--------------------")
