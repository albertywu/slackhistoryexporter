import os
import time
import csv
from functools import wraps
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

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


@retry_on_slack_error()
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
            messages.extend(result['messages'])
            next_cursor = result.get('response_metadata', {}).get('next_cursor')

            if not next_cursor:
                break

        except SlackApiError as e:
            print(f"[read_channel_messages] Error: {e}")
            break

    return messages


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
        writer.writerow(['timestamp', 'channel', 'username', 'message'])

        for message in messages:
            writer.writerow([
                message['ts'],
                message['channel'],
                message['username'],
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
