import requests
import re
import logging

def fetch_page_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logging.error(f"Error fetching page: {e}")
        return None

def extract_sessions(html_content):
    sessions = []
    session_type = None
    # Try to find "Next Sessions:" first (for multiple)
    match = re.search(r'Next\s+Sessions?:', html_content, re.IGNORECASE)
    if match:
        session_type = 'next'
        start_pos = match.end()
        # Find the end of this section (next heading or double newline or end)
        end_match = re.search(r'<h\d[^>]*>', html_content[start_pos:], re.IGNORECASE)
        end_pos = end_match.start() if end_match else len(html_content) - start_pos
        block = html_content[start_pos:start_pos + end_pos]
        # Replace <br> with \n to handle line breaks
        block = re.sub(r'<br\s*/?>', '\n', block, flags=re.IGNORECASE)
        # Remove HTML tags
        text_block = re.sub(r'<[^>]+>', '', block).strip()
        # Split by newlines or common separators to avoid concatenation
        potential_sessions = re.split(r'\n|Next|Power Tower', text_block)
        for part in potential_sessions:
            part = part.strip()
            if part:
                # Use regex findall to extract valid session strings from each part
                found = re.findall(r'\d+(?:am|pm)?-\d+(?:am|pm)?,\s*\w+\s*\d+(?:st|nd|rd|th)?\s*\w+', part, re.IGNORECASE)
                sessions.extend(found)
    else:
        # Check for "Last Session:"
        match = re.search(r'Last\s+Session:', html_content, re.IGNORECASE)
        if match:
            session_type = 'last'
            start_pos = match.end()
            # Find the end (next heading, "Next Power Tower", or end)
            end_match = re.search(r'<h\d[^>]*>|Next Power Tower', html_content[start_pos:], re.IGNORECASE)
            end_pos = end_match.start() if end_match else len(html_content) - start_pos
            block = html_content[start_pos:start_pos + end_pos]
            # Replace <br> with \n
            block = re.sub(r'<br\s*/?>', '\n', block, flags=re.IGNORECASE)
            # Remove HTML tags
            text_block = re.sub(r'<[^>]+>', '', block).strip()
            # Extract session string
            found = re.findall(r'\d+(?:am|pm)?-\d+(?:am|pm)?,\s*\w+\s*\d+(?:st|nd|rd|th)?\s*\w+', text_block, re.IGNORECASE)
            sessions.extend(found)
        else:
            # Fallback to old single session logic
            match = re.search(r'Next(?:\s+\w+)*\s+Sessions?:\s*([^<\n]+)', html_content, re.IGNORECASE)
            if match:
                session_type = 'next'
                session_raw = match.group(1).strip()
                session_clean = re.sub(r'<[^>]+>', '', session_raw)
                # Split if multiple are concatenated
                found = re.findall(r'\d+(?:am|pm)?-\d+(?:am|pm)?,\s*\w+\s*\d+(?:st|nd|rd|th)?\s*\w+', session_clean, re.IGNORECASE)
                sessions.extend(found)
    # Remove duplicates and clean
    sessions = list(set(sessions))
    return session_type, sessions