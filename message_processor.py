import base64
import re
from cleaner import clean_html
from convert_to_markdown import html_to_markdown
import tiktoken


def decode_content(data):
    return base64.urlsafe_b64decode(data).decode("utf-8")


def process_part(part):
    if part["mimeType"] == "text/plain":
        return decode_content(part["body"]["data"]), None
    elif part["mimeType"] == "text/html":
        return None, decode_content(part["body"]["data"])
    return None, None


def sanitize_filename(filename):
    return re.sub(r"[^\w\-_\. ]", "_", filename)


def count_tokens(text: str):
    return len(tiktoken.encoding_for_model("gpt-4o").encode(text))


def extract_email_metadata(response):
    payload = response["payload"]
    headers = payload["headers"]
    sender_header = next(
        (header["value"] for header in headers if header["name"].lower() == "from"),
        "Unknown Sender <unknown@example.com>",
    )
    sender_match = re.match(r"^(.*?)\s*(?:<(.+@.+)>)?$", sender_header)
    sender_name = sender_match.group(1).strip() if sender_match else "Unknown Sender"
    sender_email = (
        sender_match.group(2)
        if sender_match and sender_match.group(2)
        else "unknown@example.com"
    )

    metadata = {
        "id": response["id"],
        "time_received": next(
            (header["value"] for header in headers if header["name"].lower() == "date"),
            "Unknown",
        ),
        "is_read": "UNREAD" not in response["labelIds"],
        "sender_name": sender_name,
        "sender_email": sender_email,
        "subject": next(
            (
                header["value"]
                for header in headers
                if header["name"].lower() == "subject"
            ),
            "No Subject",
        ),
        "original_html": None,
        "clean_html": None,
        "clean_markdown": None,
        "attachments": [],
    }

    plain_content, html_content = None, None
    for part in payload.get("parts", []):
        if part["mimeType"] == "multipart/alternative":
            for subpart in part.get("parts", []):
                plain, html = process_part(subpart)
                plain_content = plain_content or plain
                html_content = html_content or html
        elif part["mimeType"].startswith("application/") or part["mimeType"].startswith(
            "image/"
        ):
            metadata["attachments"].append(
                {
                    "filename": part.get("filename", "unnamed_attachment"),
                    "mimeType": part["mimeType"],
                    "data": part["body"].get("attachmentId", ""),
                }
            )
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

    metadata["original_html"] = html_content
    if html_content:
        metadata["clean_html"] = clean_html(html_content)
        metadata["clean_markdown"] = html_to_markdown(metadata["clean_html"])
    elif plain_content:
        metadata["clean_markdown"] = plain_content

    return metadata


def save_to_file(content, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    filesize = len(content)
    # TODO: log this!!
    # print(f"Content saved to {filename} ({filesize} bytes)")


def print_side_by_side(*items):
    formatted_items = []
    for item in items:
        if isinstance(item, tuple):
            key, value = item
        else:
            key = item
            value = ""
        value = str(value)
        truncated_value = f"{value[:30]}..." if len(value) > 30 else value
        formatted_items.append(f"{key}: {truncated_value}")
    print(" | ".join(formatted_items))


def process_message(request_id, response, exception):
    if exception is not None:
        print(f"An error occurred: {exception}")
        return

    if "DRAFT" in response.get("labelIds", []):
        return

    metadata = extract_email_metadata(response)

    if metadata["clean_markdown"]:
        sanitized_subject = sanitize_filename(metadata["subject"])[:50]
        sender_email = sanitize_filename(metadata["sender_email"])[:50]
        filename = f"email{request_id}_{sender_email}_{sanitized_subject}.md"
        metadata["num_tokens"] = count_tokens(metadata["clean_markdown"])
        save_to_file(metadata["clean_markdown"], filename)
    else:
        print("No message body found")

    print_side_by_side(
        ("Tokens", metadata.get("num_tokens")),
        ("Date", metadata["time_received"][:22]),
        ("Subject", metadata["subject"]),
        ("Addr", metadata["sender_email"]),
        ("From", metadata["sender_name"]),
    )
