## Export your Slack history, for free, using Slack API calls.

### What this does
- joins all unarchived public channels in your workspace
- pulls all conversations in all channels (including threads!), and writes everything to a single csv file (`all_channel_conversations.csv`)

### Usage
`SLACK_API_TOKEN=<your token> python export.py`

### App Setup
You'll need to create a Slack app for this, with the following scope:
```
channels:history
channels:join
users:read
```

### Bonus
Generate a pdf of user stats by running `python stats.py`