import base64
import mimetypes
import os
from email.message import EmailMessage

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from creds import get_local_credentials


def attach(message, filename):
    # guessing the MIME type
    type_subtype, _ = mimetypes.guess_type(filename)
    print("Guessing attachment type", type_subtype)
    maintype, subtype = type_subtype.split("/")

    with open(filename, "rb") as fp:
        attachment_data = fp.read()
    message.add_attachment(attachment_data, maintype, subtype, filename=filename)
    return message


def gmail_create_draft_with_attachment():
    """Create and insert a draft email with attachment.
     Print the returned draft's message and id.
    Returns: Draft object, including draft id and message meta data.

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    creds = get_local_credentials()

    try:
        # create gmail api client
        service = build("gmail", "v1", credentials=creds)
        mime_message = EmailMessage()

        # headers
        mime_message["To"] = "gduser1@workspacesamples.dev"
        mime_message["From"] = "gduser2@workspacesamples.dev"
        mime_message["Subject"] = "coding help"

        # Make a message
        files = ["photo.webp", "quickstart.py"]
        mime_message.set_content("Here are the files: " + ", ".join(files))
        for file in files:
            attach(mime_message, file)

        encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

        create_draft_request_body = {"message": {"raw": encoded_message}}
        # pylint: disable=E1101
        draft = (
            service.users()
            .drafts()
            .create(userId="me", body=create_draft_request_body)
            .execute()
        )
        print(f'Draft id: {draft["id"]}\nDraft message: {draft["message"]}')
    except HttpError as error:
        print(f"An error occurred: {error}")
        draft = None
    return draft


if __name__ == "__main__":
    gmail_create_draft_with_attachment()
