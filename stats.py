import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from textblob import TextBlob
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
import nltk

nltk.download('punkt')
nltk.download('stopwords')

def read_csv_data(file_name):
    messages_df = pd.read_csv(file_name, parse_dates=['timestamp'])
    return messages_df

def most_active_users_chart(messages_df):
    user_message_counts = messages_df['username'].value_counts()
    user_message_counts = user_message_counts[user_message_counts >= 5]
    return user_message_counts

def most_active_channels_chart(messages_df):
    channel_message_counts = messages_df['channel'].value_counts()
    channel_message_counts = channel_message_counts[channel_message_counts >= 10]
    return channel_message_counts


def peak_activity_times_chart(messages_df):
    messages_df['hour'] = messages_df['timestamp'].dt.hour
    hourly_message_counts = messages_df.groupby('hour')['message'].count()
    return hourly_message_counts

def message_sentiment_chart(messages_df, filtered_channels):
    messages_df = messages_df[messages_df['channel'].isin(filtered_channels)].copy()
    messages_df['message'] = messages_df['message'].astype(str)
    messages_df['sentiment'] = messages_df['message'].apply(lambda text: TextBlob(text).sentiment.polarity)
    channel_sentiments = messages_df.groupby('channel')['sentiment'].mean().sort_values()
    return channel_sentiments


def top_keywords_chart(messages_df):
    stop_words = set(stopwords.words('english'))
    messages_df['message'] = messages_df['message'].astype(str)
    all_messages = ' '.join(messages_df['message'].tolist())
    words = word_tokenize(all_messages)
    filtered_words = [word for word in words if word.isalnum() and word.lower() not in stop_words]
    word_frequencies = Counter(filtered_words).most_common(20)
    return word_frequencies


def generate_charts(csv_file, output_file):
    messages_df = read_csv_data(csv_file)

    # Generate charts
    user_message_counts = most_active_users_chart(messages_df)
    channel_message_counts = most_active_channels_chart(messages_df)
    hourly_message_counts = peak_activity_times_chart(messages_df)
    filtered_channels = channel_message_counts.index
    channel_sentiments = message_sentiment_chart(messages_df, filtered_channels)
    word_frequencies = top_keywords_chart(messages_df)

    # Plot the charts
    with PdfPages(output_file) as pdf:
        fig, ax = plt.subplots()
        fig.subplots_adjust(bottom=0.2)  # Add room at bottom
        user_message_counts.plot(kind='bar', ax=ax)
        ax.set_title('Most Active Users')
        ax.set_xlabel('User')
        ax.set_ylabel('Number of Messages')
        pdf.savefig()
        plt.close()

        fig, ax = plt.subplots()
        fig.subplots_adjust(bottom=0.3)  # Add room at bottom
        channel_message_counts.plot(kind='bar', ax=ax)
        ax.set_title('Most Active Channels')
        ax.set_xlabel('Channel')
        ax.set_ylabel('Number of Messages')
        pdf.savefig()
        plt.close()

        fig, ax = plt.subplots()
        hourly_message_counts.plot(kind='bar', ax=ax)
        ax.set_title('Peak Activity Times')
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Number of Messages')
        pdf.savefig()
        plt.close()

        # Plot the Message Sentiment chart
        fig, ax = plt.subplots()
        fig.subplots_adjust(bottom=0.3)  # Add room at bottom
        channel_sentiments.plot(kind='bar', ax=ax)
        ax.set_title('Message Sentiment by Channel')
        ax.set_xlabel('Channel')
        ax.set_ylabel('Sentiment Score')
        pdf.savefig()
        plt.close()

        fig, ax = plt.subplots()
        fig.subplots_adjust(bottom=0.2)  # Add room at bottom
        word_freq_df = pd.DataFrame(word_frequencies, columns=['Word', 'Frequency'])
        word_freq_df.plot(kind='bar', x='Word', y='Frequency', ax=ax)
        ax.set_title('Top Keywords')
        ax.set_xlabel('Keyword')
        ax.set_ylabel('Frequency')
        pdf.savefig()
        plt.close()


if __name__ == '__main__':
    csv_file = 'all_channel_conversations.csv'
    output_file = 'slack_stats_charts.pdf'
    generate_charts(csv_file, output_file)