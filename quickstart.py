import base64
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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
    # Get the message body
    plain_content = ""
    html_content = ""
    for part in payload.get("parts", []):
        if part["mimeType"] == "multipart/alternative":
            for subpart in part.get("parts", []):
                if subpart["mimeType"] == "text/plain":
                    plain_content += base64.urlsafe_b64decode(subpart["body"]["data"]).decode("utf-8")
                elif subpart["mimeType"] == "text/html":
                    html_content += base64.urlsafe_b64decode(subpart["body"]["data"]).decode("utf-8")
        elif part["mimeType"] == "text/plain":
            plain_content += base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
        elif part["mimeType"] == "text/html":
            html_content += base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")

    # If there are no parts, try to get the body from the payload directly
    if not plain_content and not html_content:
        body_data = payload.get("body", {}).get("data", "")
        if body_data:
            decoded_content = base64.urlsafe_b64decode(body_data).decode("utf-8")
            if payload.get("mimeType") == "text/plain":
                plain_content = decoded_content
            elif payload.get("mimeType") == "text/html":
                html_content = decoded_content

    # Save the content to files
    if plain_content:
        filename = f"msg_{request_id}_plain.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(plain_content)
        print(f"Plain text content saved to {filename}")
    
    if html_content:
        filename = f"msg_{request_id}_html.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"HTML content saved to {filename}")
    
    if not plain_content and not html_content:
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
