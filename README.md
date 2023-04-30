## Export your Slack history, for free, using Slack API calls.

### What this does
- joins all unarchived public channels in your workspace
- pulls all conversations in all channels, and writes everything to a single csv file (`all_channel_conversations.csv`)

### Usage
`SLACK_API_TOKEN=<your token> python export.py`

### Required Scopes 
```
channels:history
channels:join
users:read
```