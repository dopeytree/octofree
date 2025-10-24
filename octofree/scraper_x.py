"""
X.com (Twitter) scraper for Octopus Energy free electricity sessions.

This module provides optional supplementary scraping of the @savingsessions
X.com (Twitter) account to catch session announcements that might be made
on social media before the website is updated.

Runs during scheduled windows (11am and 8pm) to minimize API usage.
Requires BEARER_TOKEN environment variable for X.com API v2 access.

The scraper searches for recent tweets from @savingsessions with the
#savingsessions hashtag and extracts session information using the same
regex patterns as the website scraper.
"""

import re
import logging
import os
import requests
from dotenv import load_dotenv

load_dotenv('settings.env')

def bearer_oauth(r):
    """
    Add bearer token authentication to X.com API request.
    
    Required authentication method for X.com API v2. Adds Authorization
    header with bearer token from BEARER_TOKEN environment variable.
    
    Args:
        r: requests.Request object to add authentication headers to.
    
    Returns:
        Modified request object with authentication headers.
    """
    bearer_token = os.getenv('BEARER_TOKEN')
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2RecentSearchPython"
    return r

def connect_to_endpoint(url, params):
    """
    Connect to X.com API endpoint and return JSON response.
    
    Makes authenticated GET request to X.com API v2 endpoint.
    
    Args:
        url (str): X.com API endpoint URL.
        params (dict): Query parameters for the request.
    
    Returns:
        dict or None: Parsed JSON response, or None if request fails.
            Logs error details on failure.
    """
    response = requests.request("GET", url, auth=bearer_oauth, params=params, timeout=30)
    if response.status_code != 200:
        logging.error(f"Request returned an error: {response.status_code} {response.text}")
        return None
    return response.json()

def fetch_tweets_with_hashtag():
    """
    Fetch recent tweets from @savingsessions account.
    
    Searches for recent tweets (last 7 days) from the @savingsessions
    account containing #savingsessions hashtag. Returns up to 2 most
    recent matching tweets.
    
    Requires BEARER_TOKEN environment variable to be set for API access.
    
    Returns:
        list: List of tweet text strings (up to 2), or empty list if:
            - BEARER_TOKEN not configured
            - API request fails
            - No matching tweets found
    """
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
    """
    Extract session information from tweet text content.
    
    Uses the same regex pattern as website scraper to find session strings
    in tweet text. Handles various formats including standard and special
    session announcements.
    
    Args:
        tweet_texts (list): List of tweet text strings to parse.
    
    Returns:
        tuple: (session_type, sessions)
            - session_type (str): Always 'next' (assumes tweets announce upcoming sessions)
            - sessions (list): Deduplicated list of extracted session strings
    """
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
    """
    Main entry point for X.com scraping - fetch tweets and extract sessions.
    
    Combines tweet fetching and session extraction into single operation.
    Called from main.py during scheduled X.com check windows (11am, 8pm).
    
    Returns:
        tuple: (session_type, sessions)
            - session_type (str): Type of sessions found ('next')
            - sessions (list): List of session strings extracted from tweets
    """
    tweet_texts = fetch_tweets_with_hashtag()
    session_type, sessions = extract_sessions_from_tweets(tweet_texts)
    return session_type, sessions