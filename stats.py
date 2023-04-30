import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Read the CSV file
df = pd.read_csv('all_channel_conversations.csv')

# Convert timestamp to datetime objects
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Calculate the stats
messages_per_user_month = df.groupby([df['username'], df['timestamp'].dt.to_period('M')]).size().unstack().fillna(0)
average_message_length_per_user_month = df.groupby([df['username'], df['timestamp'].dt.to_period('M')])['message'].apply(lambda x: x.str.len().mean()).unstack().fillna(0)
average_messages_per_day_month = messages_per_user_month.div(messages_per_user_month.columns.to_timestamp().days_in_month, axis=1)

# Remove users with less than 1 message in each month
messages_per_user_month = messages_per_user_month[messages_per_user_month.gt(0).all(axis=1)]
average_message_length_per_user_month = average_message_length_per_user_month.loc[messages_per_user_month.index]
average_messages_per_day_month = average_messages_per_day_month.loc[messages_per_user_month.index]

# Create a 3-row, 1-column grid of plots
fig, ax = plt.subplots(3, 1, figsize=(10, 15), gridspec_kw={'height_ratios': [3, 3, 4]})
fig.subplots_adjust(hspace=0.5)  # Add extra padding between subplots

# Plot number of messages per user per month
messages_per_user_month.T.plot(ax=ax[0], kind='bar', stacked=True)
ax[0].set_title('Number of Messages per User per Month')
ax[0].set_xlabel('Month')
ax[0].set_ylabel('Number of Messages')
ax[0].legend(loc='upper left', bbox_to_anchor=(1, 1))

# Plot average message length per user per month
average_message_length_per_user_month.T.plot(ax=ax[1], kind='bar')
ax[1].set_title('Average Message Length per User per Month')
ax[1].set_xlabel('Month')
ax[1].set_ylabel('Average Message Length')
ax[1].legend(loc='upper left', bbox_to_anchor=(1, 1))

# Plot average messages per day for each user per month (line chart)
average_messages_per_day_month.T.plot(ax=ax[2])
ax[2].set_title('Average Messages per Day for Each User per Month (Line Chart)')
ax[2].set_xlabel('Month')
ax[2].set_ylabel('Average Number of Messages per Day')
ax[2].legend(loc='upper left', bbox_to_anchor=(1, 1))

# Save the plots as a PDF
with PdfPages('user_stats_monthly.pdf') as pdf:
    pdf.savefig(fig, bbox_inches='tight')

