## Export your slack history, for free, using slack API calls.

### What this does
- joins all unarchived public channels in your workspace
- pulls all conversations in all channels, and writes it to a csv file (all_channel_conversations.csv)

### Usage
`SLACK_API_TOKEN=<your token> python export.py`

### Required Scopes 
```
channels:history
channels:join
users:read
```