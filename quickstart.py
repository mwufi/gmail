import base64
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from cleaner import clean_html
from convert_to_markdown import to_markdown_file

from creds import get_local_credentials
import datetime


def get_filters(service):
    """
    A list of filters of the form
    {'id': 'ANe1BmjnSzX46Crf6gt7p1dMZEIg4pqCn4yaJA', 'criteria': {'from': 'mail@change.org'}, 'action': {'addLabelIds': ['TRASH']}}
    """
    filters = service.users().settings().filters().list(userId="me").execute()
    filters = filters.get("filter", [])
    if not filters:
        print("No filters found.")
        return
    print("Filters:")
    for i, t in enumerate(filters):
        del t["id"]
        print(f"{i}: {t}")


def get_labels(service):
    """
    A list of labels of the form
    {'id': 'UNREAD', 'name': 'Unread', 'type': 'system'}
    """
    labels = service.users().labels().list(userId="me").execute()
    labels = labels.get("labels", [])
    if not labels:
        print("No labels found.")
        return
    print("Labels:")
    for i, t in enumerate(labels):
        del t["id"]
        print(f"{i}: {t}")


def get_messages_today(service):
    # Get today's date in the format YYYY/MM/DD
    today = datetime.date.today().strftime("%Y/%m/%d")

    # Create the query string to filter messages from today
    query = f"after:{today}"

    # Request messages with the query
    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])

    if not messages:
        print("No messages found.")
        return

    print("Messages:")

    # Create a batch request
    batch = service.new_batch_http_request(callback=process_message)

    for message in messages:
        batch.add(service.users().messages().get(userId="me", id=message["id"]))

    # Execute the batch request
    batch.execute()


def process_message(request_id, response, exception):
    if exception is not None:
        print(f"An error occurred: {exception}")
        return

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
            filename = f"msg_{request_id}_{content_type}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            filesize = len(content) // 6
            print(
                f"{content_type.capitalize()} content saved to {filename} ({filesize} length)"
            )

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
        to_markdown_file(cleaned_html, f"msg_{request_id}_html.md", with_images=False)
        # save_content(cleaned_html, "html", request_id)
    elif plain_content:
        save_content(plain_content, "plain", request_id)
    else:
        print("No message body found")

    print(f"Subject: {subject}")
    print(f"From: {sender}")
    print("--------------------")


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = get_local_credentials()

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        get_messages_today(service)
    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
