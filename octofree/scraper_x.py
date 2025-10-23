import re
import logging
import os
import requests
from dotenv import load_dotenv

load_dotenv('settings.env')

def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """
    bearer_token = os.getenv('BEARER_TOKEN')
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2RecentSearchPython"
    return r

def connect_to_endpoint(url, params):
    response = requests.request("GET", url, auth=bearer_oauth, params=params, timeout=30)
    if response.status_code != 200:
        logging.error(f"Request returned an error: {response.status_code} {response.text}")
        return None
    return response.json()

def fetch_tweets_with_hashtag():
    bearer_token = os.getenv('BEARER_TOKEN')
    if not bearer_token:
        logging.error("BEARER_TOKEN not set in environment variables.")
        return []
    
    search_url = "https://api.twitter.com/2/tweets/search/recent"
    query_params = {
        'query': 'from:Savingsessions #savingsessions',
        'max_results': 10,
        'tweet.fields': 'text'
    }
    
    json_response = connect_to_endpoint(search_url, query_params)
    if json_response and 'data' in json_response:
        # Limit to latest 2 tweets
        tweets = json_response['data'][:2]
        return [tweet['text'] for tweet in tweets]
    else:
        return []

def extract_sessions_from_tweets(tweet_texts):
    sessions = []
    for text in tweet_texts:
        # Look for patterns like time-date in the tweet
        # Assuming format like "2pm-4pm, Saturday 26th October" or similar
        found = re.findall(r'\d+(?:am|pm)?-\d+(?:am|pm)?,\s*\w+\s*\d+(?:st|nd|rd|th)?\s*\w+', text, re.IGNORECASE)
        sessions.extend(found)
    # Remove duplicates
    sessions = list(set(sessions))
    return 'next', sessions  # Assume they are next sessions

def fetch_and_extract_sessions():
    tweet_texts = fetch_tweets_with_hashtag()
    session_type, sessions = extract_sessions_from_tweets(tweet_texts)
    return session_type, sessions