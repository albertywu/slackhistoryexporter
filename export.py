import os
import time
import csv
from functools import wraps
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime


# Get the Slack API token from the environment variable
SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')

if not SLACK_API_TOKEN:
    print("SLACK_API_TOKEN environment variable not set. Please set the environment variable with your Slack API "
          "token and try again.")
    exit(1)

# Initialize a Web API client
slack_client = WebClient(token=SLACK_API_TOKEN)


def retry_on_slack_error(max_retries=5):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return function(*args, **kwargs)
                except SlackApiError as e:
                    if retries == max_retries:
                        raise e
                    sleep_duration = 2 ** retries
                    print(f"[{function.__name__}] Slack API error: {e}. Retrying in {sleep_duration} seconds...")
                    time.sleep(sleep_duration)
                    retries += 1

        return wrapper

    return decorator


@retry_on_slack_error()
def get_all_channels():
    response = slack_client.conversations_list()
    channels = response['channels']
    return channels


def read_channel_messages(channel_id):
    messages = []
    next_cursor = None

    while True:
        try:
            result = slack_client.conversations_history(
                channel=channel_id,
                cursor=next_cursor,
                limit=200
            )
            main_messages = result['messages']

            for message in main_messages:
                if 'reply_count' in message:
                    thread_ts = message['ts']
                    replies = get_thread_replies(channel_id, thread_ts)
                    message['thread_messages'] = replies

            messages.extend(main_messages)
            next_cursor = result.get('response_metadata', {}).get('next_cursor')

            if not next_cursor:
                break

        except SlackApiError as e:
            print(f"[read_channel_messages] Error: {e}")
            break

    # Flatten the messages list and include threaded messages
    all_messages = []
    for message in messages:
        all_messages.append(message)
        if 'thread_messages' in message:
            all_messages.extend(message['thread_messages'])

    # Convert timestamps to datetime objects and sort messages by timestamp in reverse order
    for message in all_messages:
        message['ts'] = datetime.fromtimestamp(float(message['ts']))
    all_messages.sort(key=lambda msg: msg['ts'], reverse=True)

    return all_messages


@retry_on_slack_error()
def get_thread_replies(channel_id: str, thread_ts: str):
    replies = []
    next_cursor = None

    while True:
        try:
            result = slack_client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                cursor=next_cursor,
                limit=200
            )
            replies.extend(result['messages'][1:])  # Skip the first message, which is the parent message
            next_cursor = result.get('response_metadata', {}).get('next_cursor')

            if not next_cursor:
                break

        except SlackApiError as e:
            print(f"[get_thread_replies] Error: {e}")
            break

    return replies


@retry_on_slack_error()
def get_username(user_id):
    response = slack_client.users_info(user=user_id)
    return response['user']['name']


@retry_on_slack_error()
def join_all_public_channels():
    channels = get_all_channels()

    for channel in channels:
        if not channel["is_member"]:
            try:
                print(f"Joining channel: {channel['name']} (ID: {channel['id']})")
                slack_client.conversations_join(channel=channel["id"])
            except SlackApiError as e:
                print(f"[join_all_public_channels] Error joining channel {channel['name']} (ID: {channel['id']}): {e}")


def save_messages_to_csv(file_name, messages):
    with open(file_name, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['timestamp', 'channel', 'username', 'location', 'message'])

        for message in messages:
            location = 'thread' if 'thread_ts' in message and message['ts'] != datetime.fromtimestamp(float(message['thread_ts'])) else 'main'
            writer.writerow([
                message['ts'].strftime('%Y-%m-%d %H:%M:%S'),  # Format timestamp as a string
                message['channel'],
                message['username'],
                location,
                message['text']
            ])


def main():
    all_messages = []

    print("Fetching channel list...")
    channels = get_all_channels()
    total_channels = len(channels)
    print(f"Total channels: {total_channels}")

    print("Joining all public channels...")
    join_all_public_channels()

    for i, channel in enumerate(channels):
        print(f"Fetching messages from channel {i + 1}/{total_channels}: {channel['name']} (ID: {channel['id']})")
        messages = read_channel_messages(channel['id'])

        for message in messages:
            if 'user' in message:
                username = get_username(message['user'])
                if username:
                    message['username'] = username
                else:
                    message['username'] = 'unknown'
                message['channel'] = channel['name']
                all_messages.append(message)

    print("Saving messages to CSV...")
    save_messages_to_csv('all_channel_conversations.csv', all_messages)
    print("Done.")


if __name__ == "__main__":
    main()
