import base64
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from creds import get_local_credentials
import datetime

from message_processor import process_message

import time
from ratelimit import limits, sleep_and_retry


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


@sleep_and_retry
@limits(calls=2, period=1)  # per 2 seconds
def api_list_messages(query, service, page_token=None):
    results = (
        service.users()
        .messages()
        .list(userId="me", q=query, pageToken=page_token)
        .execute()
    )
    return results


def list_messages(query, service):
    results = api_list_messages(query, service)
    messages = results.get("messages", [])

    next_page_token = results.get("nextPageToken")
    while next_page_token:
        results = api_list_messages(query, service, next_page_token)
        messages.extend(results.get("messages", []))
        next_page_token = results.get("nextPageToken")

    if not messages:
        print("No messages found.")
        return []

    return messages


QUOTA_LIMIT = 250
BATCH_SIZE = 50
COST_PER_BATCH = 5 * BATCH_SIZE


@sleep_and_retry
@limits(calls=QUOTA_LIMIT / COST_PER_BATCH, period=2)  # per 2 seconds
def rate_limited_batch_execute(batch):
    batch.execute()


def get_messages_this_week(service):
    start_of_week = (
        datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
    ).strftime("%Y/%m/%d")
    query = f"after:{start_of_week}"

    messages = list_messages(query, service)

    processed_messages = 0
    for i in range(0, len(messages), BATCH_SIZE):
        batch = service.new_batch_http_request(callback=process_message)
        for message in messages[i : i + BATCH_SIZE]:
            processed_messages += 1
            batch.add(service.users().messages().get(userId="me", id=message["id"]))
        rate_limited_batch_execute(batch)
        time.sleep(1)  # Add a small delay between batches

    print(f"Done. We processed {processed_messages} messages.")


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = get_local_credentials()

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        get_messages_this_week(service)
    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
