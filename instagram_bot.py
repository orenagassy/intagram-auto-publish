#!/usr/bin/env python3
"""
Complete Instagram Bot with Automatic Token Management
Automatically posts images and videos from local directory to Instagram
"""

import time
import random
import os
import requests
import pysftp
import re
import urllib.parse
import json
from datetime import datetime, timedelta

# Import all configuration from config.py
from config import *

# Import security configuration (API keys, passwords, etc.)
try:
    from config_security import *
except ImportError:
    print("WARNING: config_security.py not found. Please create it with your API credentials.")
    print("See config_security.py.example for template.")

def debug_print(message, category="general", verbosity_level=1):
    """
    Print debug messages based on configuration settings
    
    Args:
        message (str): The debug message to print
        category (str): Category of debug message (file_ops, api, caption, network, token, general)
        verbosity_level (int): Required verbosity level (1=basic, 2=detailed, 3=verbose)
    """
    # Check if overall verbosity level allows this message
    if DEBUG_VERBOSITY < verbosity_level:
        return
    
    # Check category-specific debug flags
    category_flags = {
        'file_ops': DEBUG_FILE_OPERATIONS,
        'api': DEBUG_API_CALLS, 
        'caption': DEBUG_CAPTION_GENERATION,
        'network': DEBUG_NETWORK_OPERATIONS,
        'token': DEBUG_TOKEN_MANAGEMENT,
        'general': True  # General messages always allowed if verbosity permits
    }
    
    if category in category_flags and not category_flags[category]:
        return
    
    # Add timestamp and category prefix
    timestamp = datetime.now().strftime('%H:%M:%S')
    category_prefix = f"[{category.upper()}]" if category != "general" else ""
    print(f"{timestamp} {category_prefix} DEBUG: {message}")

###################
## TOKEN MANAGEMENT CLASS
###################

class InstagramTokenManager:
    def __init__(self, app_id, app_secret, initial_token=None, token_file=TOKEN_FILE_PATH):
        self.app_id = app_id
        self.app_secret = app_secret
        self.token_file = token_file
        self.current_token = None
        self.token_expires_at = None
        
        # Load existing token or use initial token
        if os.path.exists(self.token_file):
            self.load_token_from_file()
        elif initial_token:
            self.current_token = initial_token
            self.get_token_info()
            self.save_token_to_file()
    
    def load_token_from_file(self):
        """Load token from file"""
        try:
            with open(self.token_file, 'r') as f:
                data = json.load(f)
                self.current_token = data.get('access_token')
                expires_str = data.get('expires_at')
                if expires_str:
                    self.token_expires_at = datetime.fromisoformat(expires_str)
            print(f"DEBUG: Loaded token from file, expires at: {self.token_expires_at}")
        except Exception as e:
            print(f"ERROR: Could not load token from file: {e}")
    
    def save_token_to_file(self):
        """Save token to file"""
        try:
            data = {
                'access_token': self.current_token,
                'expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.token_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"DEBUG: Token saved to file")
        except Exception as e:
            print(f"ERROR: Could not save token to file: {e}")
    
    def get_token_info(self):
        """Get information about current token"""
        if not self.current_token:
            print("ERROR: No token available")
            return None
        
        try:
            url = f"{GRAPH_URL}me"
            params = {'access_token': self.current_token}
            
            response = requests.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
            print(f"DEBUG: Token validation response: {response.status_code}")
            
            if response.status_code == HTTP_SUCCESS_CODE:
                # Token is valid, estimate expiration (60 days from now for long-lived)
                self.token_expires_at = datetime.now() + timedelta(days=LONG_LIVED_TOKEN_DURATION_DAYS)
                return response.json()
            else:
                print(f"ERROR: Token validation failed: {response.json()}")
                return None
                
        except Exception as e:
            print(f"ERROR: Token validation error: {e}")
            return None
    
    def exchange_for_long_lived_token(self, short_lived_token):
        """Exchange short-lived token for long-lived token"""
        print("DEBUG: Exchanging for long-lived token...")
        
        url = f"{GRAPH_URL}oauth/access_token"
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'fb_exchange_token': short_lived_token
        }
        
        try:
            response = requests.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
            print(f"DEBUG: Exchange response status: {response.status_code}")
            
            if response.status_code == HTTP_SUCCESS_CODE:
                data = response.json()
                self.current_token = data['access_token']
                
                # Long-lived tokens last 60 days
                self.token_expires_at = datetime.now() + timedelta(days=LONG_LIVED_TOKEN_DURATION_DAYS)
                
                self.save_token_to_file()
                print(f"DEBUG: Long-lived token obtained, expires: {self.token_expires_at}")
                return True
            else:
                print(f"ERROR: Token exchange failed: {response.json()}")
                return False
                
        except Exception as e:
            print(f"ERROR: Token exchange error: {e}")
            return False
    
    def is_token_valid(self):
        """Check if current token is valid and not expired"""
        if not self.current_token:
            return False
        
        if not self.token_expires_at:
            # Try to get token info
            return self.get_token_info() is not None
        
        # Check if token expires within warning days (refresh early)
        warning_time = datetime.now() + timedelta(days=TOKEN_EXPIRY_WARNING_DAYS)
        if self.token_expires_at <= warning_time:
            print(f"WARNING: Token expires soon: {self.token_expires_at}")
            return False
        
        return True
    
    def get_valid_token(self):
        """Get a valid token, refreshing if necessary"""
        if self.is_token_valid():
            return self.current_token
        
        print("ERROR: Token invalid or expiring soon. Please generate a new token manually.")
        print("Go to: https://developers.facebook.com/tools/explorer/")
        return None

###################
## UTILITY FUNCTIONS
###################

def is_video_file(file_name):
    """Check if file is a video based on extension"""
    file_extension = file_name[file_name.rfind('.'):]
    return file_extension.lower() in VIDEO_EXTENSIONS

def sanitize_filename(filename):
    """
    Sanitize filename by removing special characters and leading/trailing spaces
    """
    print(f"DEBUG: Original filename: '{filename}'")
    
    # Remove leading and trailing whitespace
    filename = filename.strip()
    print(f"DEBUG: After strip: '{filename}'")
    
    # Split filename and extension
    name, ext = os.path.splitext(filename)
    print(f"DEBUG: Name: '{name}', Extension: '{ext}'")
    
    # Remove leading/trailing spaces from name part
    name = name.strip()
    
    # Replace spaces and special characters with underscores
    # Keep only alphanumeric, dots, hyphens, and underscores
    sanitized_name = re.sub(r'[^\w\.-]', '_', name)
    
    # Remove multiple consecutive underscores
    sanitized_name = re.sub(r'_+', '_', sanitized_name)
    
    # Remove leading/trailing underscores
    sanitized_name = sanitized_name.strip('_')
    
    # Reconstruct filename
    sanitized_filename = sanitized_name + ext.lower()
    
    print(f"DEBUG: Sanitized filename: '{sanitized_filename}'")
    return sanitized_filename

def validate_media_file(file_path):
    """
    Validate media file meets Instagram requirements
    """
    print(f"DEBUG: Validating file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"DEBUG: File does not exist: {file_path}")
        return False, "File does not exist"
    
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / MB_TO_BYTES
    print(f"DEBUG: File size: {file_size} bytes ({file_size_mb:.2f} MB)")
    
    if is_video_file(file_path):
        max_size = MAX_VIDEO_SIZE_MB * MB_TO_BYTES
        if file_size > max_size:
            print(f"DEBUG: Video file too large: {file_size} bytes")
            return False, f"Video too large (max {MAX_VIDEO_SIZE_MB}MB)"
        print(f"DEBUG: Video file size OK")
    else:
        max_size = MAX_IMAGE_SIZE_MB * MB_TO_BYTES
        if file_size > max_size:
            print(f"DEBUG: Image file too large: {file_size} bytes")
            return False, f"Image too large (max {MAX_IMAGE_SIZE_MB}MB)"
        print(f"DEBUG: Image file size OK")
    
    return True, "Valid"

def test_url_accessibility(url):
    """
    Test if URL is accessible to Instagram
    """
    print(f"DEBUG: Testing URL accessibility: {url}")
    
    try:
        response = requests.head(url, timeout=HTTP_TIMEOUT_SECONDS)
        print(f"DEBUG: HTTP Status Code: {response.status_code}")
        #print(f"DEBUG: Response Headers: {dict(response.headers)}")
        
        if response.status_code == HTTP_SUCCESS_CODE:
            content_type = response.headers.get('content-type', 'unknown')
            content_length = response.headers.get('content-length', 'unknown')
            print(f"DEBUG: Content-Type: {content_type}")
            print(f"DEBUG: Content-Length: {content_length}")
            
            # Additional test with GET request
            print(f"DEBUG: Testing with GET request...")
            get_response = requests.get(url, timeout=HTTP_TIMEOUT_SECONDS, stream=True)
            print(f"DEBUG: GET Status Code: {get_response.status_code}")
            get_response.close()
            
            return True
        else:
            print(f"DEBUG: URL not accessible, status: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"DEBUG: Timeout accessing URL")
        return False
    except requests.exceptions.RequestException as e:
        print(f"DEBUG: Error accessing URL: {e}")
        return False

def calculate_next_execution_time(min_minutes, max_minutes):
    """Calculate next execution time as absolute timestamp"""
    delay_minutes = random.randint(min_minutes, max_minutes)
    next_execution = datetime.now() + timedelta(minutes=delay_minutes)
    print(f"DEBUG: Next execution scheduled for: {next_execution.strftime('%Y-%m-%d %H:%M:%S')} ({delay_minutes} minutes from now)")
    return next_execution

def wait_until_scheduled_time(scheduled_time, caption):
    """Wait until scheduled execution time, checking every minute"""
    while datetime.now() < scheduled_time:
        remaining = scheduled_time - datetime.now()
        remaining_minutes = int(remaining.total_seconds() / 60)
        remaining_seconds = int(remaining.total_seconds() % 60)
        
        if remaining_minutes > 0:
            print(f"{caption} Next execution at {scheduled_time.strftime('%H:%M:%S')} (in {remaining_minutes}m {remaining_seconds}s)", end="\r")
        else:
            print(f"{caption} Next execution at {scheduled_time.strftime('%H:%M:%S')} (in {remaining_seconds}s)", end="\r")
        
        time.sleep(WAIT_CHECK_INTERVAL_SECONDS)  # Check every minute instead of every second
    
    # Clear the line after waiting is done
    print(" " * TERMINAL_CLEAR_SPACES, end="\r")

def random_file_info(directory_path):
    """Select random file from directory"""
    print(f"DEBUG: Looking for files in: {directory_path}")
    
    if not os.path.isdir(directory_path):
        print(f"ERROR: {directory_path} is not a valid directory.")
        return None, None, None

    files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    print(f"DEBUG: Found {len(files)} files in directory")

    if not files:
        print(f"ERROR: No files found in {directory_path}.")
        return None, None, None

    selected_file = random.choice(files)
    print(f"DEBUG: Selected random file: {selected_file}")

    file_name_without_extension, _ = os.path.splitext(selected_file)
    print(f"DEBUG: File name without extension: {file_name_without_extension}")

    full_path = os.path.join(directory_path, selected_file)
    print(f"DEBUG: Full path: {full_path}")

    return file_name_without_extension, selected_file, full_path

def clean_filename_for_caption(filename):
    """
    Remove common filename suffixes like _1, _2, etc. from caption
    
    This function cleans up filenames to make them more suitable for Instagram captions
    by removing common suffixes that are often added when files are duplicated or 
    saved multiple times.
    
    Args:
        filename (str): The original filename without extension
        
    Returns:
        str: Cleaned filename suitable for use in caption
        
    Examples:
        'photo_1' -> 'photo'
        'video_2' -> 'video' 
        'image_copy' -> 'image'
        'document_final' -> 'document'
        'normal_filename' -> 'normal_filename' (unchanged)
    """
    import re
    
    # Remove numeric suffixes like _1, _2, _3, etc. at the end of filename
    # Pattern explanation: _ followed by one or more digits at end of string
    cleaned = re.sub(r'_\d+$', '', filename)
    
    # Remove common word suffixes like _copy, _final, _new, _old, _backup
    # Pattern explanation: _ followed by specific words at end of string (case-insensitive)
    cleaned = re.sub(r'_(copy|final|new|old|backup)$', '', cleaned, flags=re.IGNORECASE)
    
    return cleaned

def delete_file(file_path):
    """Delete local file"""
    print(f"DEBUG: Attempting to delete local file: {file_path}")
    try:
        os.remove(file_path)
        print(f"DEBUG: File '{file_path}' deleted successfully.")
    except OSError as e:
        print(f"ERROR: Error deleting file '{file_path}': {e}")

def get_current_access_token():
    """Get current valid access token"""
    token_manager = InstagramTokenManager(APP_ID, APP_SECRET)
    return token_manager.get_valid_token()

###################
## HASHTAG MANAGER CLASS
###################

class HashtagManager:
    def __init__(self, file_path=HASHTAGS_FILE_PATH):
        self.hashtags = self.load_hashtags(file_path)

    def load_hashtags(self, file_path):
        try:
            with open(file_path, 'r') as file:
                hashtags = [line.strip() for line in file.readlines() if line.strip().startswith("#")]
            print(f"DEBUG: Loaded {len(hashtags)} hashtags from {file_path}")
            return hashtags
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
            return []
        except Exception as e:
            print(f"Error reading file: {e}")
            return []

    def get_random_hashtags(self, num_hashtags=DEFAULT_HASHTAG_COUNT):
        if not self.hashtags:
            return ""
        
        selected_hashtags = random.sample(self.hashtags, min(num_hashtags, len(self.hashtags)))
        hashtags_string = " ".join(selected_hashtags)
        print(f"DEBUG: Selected hashtags: {hashtags_string}")
        return hashtags_string

###################
## INSTAGRAM API FUNCTIONS
###################

def post_video(caption='', video_url=''):
    """Upload video to Instagram as Reels"""
    print(f"DEBUG: Posting video to Instagram")
    print(f"DEBUG: Caption: {caption[:100]}..." if len(caption) > 100 else f"DEBUG: Caption: {caption}")
    print(f"DEBUG: Video URL: {video_url}")
    
    access_token = get_current_access_token()
    if not access_token:
        return {'error': {'message': 'No valid access token available'}}
    
    url = GRAPH_URL + IG_ACCOUNT_ID + '/media'
    param = {
        'access_token': access_token,
        'caption': caption,
        'video_url': video_url,
        'media_type': 'REELS',
        'thumb_offset': REELS_THUMB_OFFSET
    }
    
    #print(f"DEBUG: API URL: {url}")
    #print(f"DEBUG: Parameters: {param}")
    
    try:
        response = requests.post(url, params=param, timeout=HTTP_TIMEOUT_SECONDS)
        print(f"DEBUG: Response status code: {response.status_code}")
        #print(f"DEBUG: Response headers: {dict(response.headers)}")
        
        response_json = response.json()
        print(f"DEBUG: Response JSON: {response_json}")
        
        return response_json
    except Exception as e:
        print(f"ERROR: Video post request failed: {e}")
        return {'error': {'message': f'Request failed: {e}'}}

def post_image(caption='', image_url=''):
    """Upload image to Instagram"""
    print(f"DEBUG: Posting image to Instagram")
    print(f"DEBUG: Caption: {caption[:100]}..." if len(caption) > 100 else f"DEBUG: Caption: {caption}")
    print(f"DEBUG: Image URL: {image_url}")
    
    access_token = get_current_access_token()
    if not access_token:
        return {'error': {'message': 'No valid access token available'}}
    
    url = GRAPH_URL + IG_ACCOUNT_ID + '/media'
    param = {
        'access_token': access_token,
        'caption': caption,
        'image_url': image_url
    }
    
    #print(f"DEBUG: API URL: {url}")
    #print(f"DEBUG: Parameters: {param}")
    
    try:
        response = requests.post(url, params=param, timeout=HTTP_TIMEOUT_SECONDS)
        print(f"DEBUG: Response status code: {response.status_code}")
        #print(f"DEBUG: Response headers: {dict(response.headers)}")
        
        response_json = response.json()
        print(f"DEBUG: Response JSON: {response_json}")
        
        return response_json
    except Exception as e:
        print(f"ERROR: Image post request failed: {e}")
        return {'error': {'message': f'Request failed: {e}'}}

def post_story(caption='', image_url=''):
    """Upload story to Instagram"""
    print(f"DEBUG: Posting story to Instagram")
    print(f"DEBUG: Caption: {caption[:100]}..." if len(caption) > 100 else f"DEBUG: Caption: {caption}")
    print(f"DEBUG: Image URL: {image_url}")
    
    access_token = get_current_access_token()
    if not access_token:
        return {'error': {'message': 'No valid access token available'}}
    
    url = GRAPH_URL + IG_ACCOUNT_ID + '/media'
    param = {
        'access_token': access_token,
        'image_url': image_url,
        'media_type': 'STORIES'
    }
    
    #print(f"DEBUG: API URL: {url}")
    #print(f"DEBUG: Parameters: {param}")
    
    try:
        response = requests.post(url, params=param, timeout=HTTP_TIMEOUT_SECONDS)
        print(f"DEBUG: Response status code: {response.status_code}")
        #print(f"DEBUG: Response headers: {dict(response.headers)}")
        
        response_json = response.json()
        print(f"DEBUG: Response JSON: {response_json}")
        
        return response_json
    except Exception as e:
        print(f"ERROR: Story post request failed: {e}")
        return {'error': {'message': f'Request failed: {e}'}}

def publish_container(creation_id=''):
    """Publish uploaded media container"""
    print(f"DEBUG: Publishing container with ID: {creation_id}")
    
    access_token = get_current_access_token()
    if not access_token:
        return {'error': {'message': 'No valid access token available'}}
    
    url = GRAPH_URL + IG_ACCOUNT_ID + '/media_publish'
    param = {
        'access_token': access_token,
        'creation_id': creation_id
    }
    
    #print(f"DEBUG: Publish URL: {url}")
    #print(f"DEBUG: Publish parameters: {param}")
    
    try:
        response = requests.post(url, params=param, timeout=HTTP_TIMEOUT_SECONDS)
        print(f"DEBUG: Publish response status: {response.status_code}")
        
        response_json = response.json()
        print(f"DEBUG: Publish response JSON: {response_json}")
        
        return response_json
    except Exception as e:
        print(f"ERROR: Publish request failed: {e}")
        return {'error': {'message': f'Request failed: {e}'}}

###################
## SFTP FUNCTIONS
###################

def upload_to_sftp(full_file_path):
    """
    Upload file to SFTP with sanitized filename
    Returns the sanitized filename used on the server
    """
    print(f"DEBUG: Starting SFTP upload for: {full_file_path}")
    
    original_filename = os.path.basename(full_file_path)
    print(f"DEBUG: Original filename: {original_filename}")
    
    sanitized_filename = sanitize_filename(original_filename)
    print(f"DEBUG: Sanitized filename: {sanitized_filename}")
    
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None  # Skip host key verification

    try:
        with pysftp.Connection(
            host=SFTP_SERVER, username=SFTP_USER, password=SFTP_PASS, cnopts=cnopts
        ) as sftp:
            print(f"DEBUG: Connected to SFTP server: {SFTP_SERVER}")
            
            sftp.chdir(SFTP_REMOTE_DIR_PATH)
            print(f"DEBUG: Changed to remote directory: {SFTP_REMOTE_DIR_PATH}")
            
            dir_listing_before = sftp.listdir()
            print(f"DEBUG: Files in directory before upload: {len(dir_listing_before)} files")
            
            print(f"DEBUG: Uploading {full_file_path} as {sanitized_filename}")
            sftp.put(full_file_path, sanitized_filename)
            print(f"DEBUG: Upload completed successfully")
            
            dir_listing_after = sftp.listdir()
            print(f"DEBUG: Files in directory after upload: {len(dir_listing_after)} files")
            
            if sanitized_filename in dir_listing_after:
                print(f"DEBUG: File {sanitized_filename} confirmed on server")
            else:
                print(f"DEBUG: WARNING - File {sanitized_filename} not found on server!")
                
        return sanitized_filename
        
    except Exception as e:
        print(f"DEBUG: SFTP upload error: {e}")
        raise

def delete_from_sftp(file_name):
    """Delete file from SFTP server"""
    print(f"DEBUG: Deleting from SFTP: {file_name}")

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None  # Skip host key verification

    try:
        with pysftp.Connection(
            host=SFTP_SERVER, username=SFTP_USER, password=SFTP_PASS, cnopts=cnopts
        ) as sftp:
            print(f"DEBUG: Connected to SFTP for deletion")
            
            sftp.chdir(SFTP_REMOTE_DIR_PATH)
            print(f"DEBUG: Changed to remote directory: {SFTP_REMOTE_DIR_PATH}")
            
            dir_listing_before = sftp.listdir()
            print(f"DEBUG: Files before deletion: {len(dir_listing_before)} files")
            
            if file_name in dir_listing_before:
                sftp.remove(file_name)
                print(f"DEBUG: File {file_name} deleted successfully")
                
                dir_listing_after = sftp.listdir()
                if file_name not in dir_listing_after:
                    print(f"DEBUG: File {file_name} confirmed deleted")
                else:
                    print(f"DEBUG: WARNING - File {file_name} still exists after deletion!")
            else:
                print(f"DEBUG: File {file_name} not found on server, skipping deletion")
                
    except Exception as e:
        print(f"DEBUG: SFTP deletion error: {e}")

###################
## MAIN EXECUTION
###################

def main():
    """Main execution function"""
    print("DEBUG: Starting Instagram Bot")
    print(f"DEBUG: Configuration loaded:")
    print(f"  - Local directory: {LOCAL_DIRECTORY_PATH}")
    print(f"  - Delay range: {MIN_DELAY_MINUTES}-{MAX_DELAY_MINUTES} minutes")
    print(f"  - Max image size: {MAX_IMAGE_SIZE_MB}MB")
    print(f"  - Max video size: {MAX_VIDEO_SIZE_MB}MB")
    
    hashtag_manager = HashtagManager()
    
    # Test token on startup
    test_token = get_current_access_token()
    if not test_token:
        print("ERROR: No valid access token available. Please set up token first.")
        print("Instructions:")
        print("1. Go to https://developers.facebook.com/tools/explorer/")
        print("2. Generate a short-lived token")
        print("3. Run this code to exchange for long-lived token:")
        print(f"   token_manager = InstagramTokenManager('{APP_ID}', '{APP_SECRET}')")
        print("   token_manager.exchange_for_long_lived_token('your-short-lived-token')")
        return
    
    print(f"DEBUG: Valid token available: {test_token[:20]}...")

    while True:
        print("-----------------------------------------------------------------------")
        print("DEBUG: Starting new cycle")
        
        # Get local random file
        file_name_without_extension, file_name_with_extension, full_path = random_file_info(LOCAL_DIRECTORY_PATH)

        if file_name_without_extension and file_name_with_extension and full_path:
            print(f"DEBUG: Processing file: {file_name_with_extension}")
            
            # Validate media file
            is_valid, validation_message = validate_media_file(full_path)
            if not is_valid:
                print(f"ERROR: File validation failed: {validation_message}")
                print("DEBUG: Skipping this file and continuing to next")
                continue
            
            print(f"DEBUG: File validation passed: {validation_message}")
            
            # Upload the file to public server (with sanitized name)
            print("DEBUG: Starting SFTP upload...")
            try:
                sanitized_server_filename = upload_to_sftp(full_path)
                print(f"DEBUG: SFTP upload successful, server filename: {sanitized_server_filename}")
            except Exception as e:
                print(f"ERROR: SFTP upload failed: {e}")
                continue
            
            # Construct web URL with sanitized filename
            web_url = WEB_DIR_PATH + sanitized_server_filename
            print(f"DEBUG: Constructed web URL: {web_url}")
            
            # Test URL accessibility
            print("DEBUG: Testing URL accessibility...")
            if not test_url_accessibility(web_url):
                print("ERROR: URL is not accessible, skipping Instagram post")
                # Clean up - delete from server
                delete_from_sftp(sanitized_server_filename)
                continue
            
            print("DEBUG: URL accessibility test passed")
            
            # Prepare caption
            cleaned_filename = clean_filename_for_caption(file_name_without_extension)
            caption = cleaned_filename + "\n\n" + hashtag_manager.get_random_hashtags()
            debug_print(f"Cleaned filename: {cleaned_filename}", "caption", 2)
            debug_print(f"Prepared caption: {caption[:100]}..." if len(caption) > 100 else f"Prepared caption: {caption}", "caption", 1)
            
            # Upload to instagram
            if is_video_file(file_name_with_extension):
                print("DEBUG: Processing as video file")
                res = post_video(caption, web_url)
                if 'error' in res:
                    print(f"ERROR: Video upload failed: {res['error']}")
                else:
                    print("DEBUG: Video upload initiated successfully")
                    short_delay_time = calculate_next_execution_time(SHORT_DELAY_MIN_MINUTES, SHORT_DELAY_MAX_MINUTES)
                    wait_until_scheduled_time(short_delay_time, "Let instagram process the video")
            else:
                print("DEBUG: Processing as image file")
                
                # Post image
                print("-- uploading image to instagram for post--") 
                res = post_image(caption, web_url)
                
                if 'error' in res:
                    print(f"ERROR: Image upload failed: {res['error']}")
                else:
                    print("DEBUG: Image upload successful")
                    
                    # publish on post to instagram 
                    if "id" in res:
                        print("-- publish post to instagram --")    
                        publish_res = publish_container(res["id"])
                        
                        if 'error' in publish_res:
                            print(f"ERROR: Post publish failed: {publish_res['error']}")
                        else:
                            print("DEBUG: Post published successfully")

                            # Upload as story
                            print("-- uploading image to instagram for story--") 
                            story_res = post_story(caption, web_url)
                            
                            if 'error' in story_res:
                                print(f"ERROR: Story upload failed: {story_res['error']}")
                            else:
                                print("DEBUG: Story upload successful")
                                
                                # publish story to instagram 
                                if "id" in story_res:
                                    print("-- publish story to instagram --")    
                                    story_publish_res = publish_container(story_res["id"])
                                    
                                    if 'error' in story_publish_res:
                                        print(f"ERROR: Story publish failed: {story_publish_res['error']}")
                                    else:
                                        print("DEBUG: Story published successfully")
                    else:
                        print("ERROR: No ID returned from image upload, cannot publish")

            # Clean up - remove from public server
            print("DEBUG: Starting cleanup...")
            delete_from_sftp(sanitized_server_filename)
            
            # Delete local file
            print("-- delete local file --")
            delete_file(full_path)
            
            print("DEBUG: Cycle completed successfully")
        else:
            print("ERROR: Could not select a file to process")
        
        # Schedule next cycle
        print("DEBUG: Scheduling next cycle")
        next_cycle_time = calculate_next_execution_time(MIN_DELAY_MINUTES, MAX_DELAY_MINUTES)
        wait_until_scheduled_time(next_cycle_time, "Next cycle at")
        print("DEBUG: Starting next cycle")

def setup_token():
    """One-time setup to get long-lived token"""
    print("=== Instagram Bot Token Setup ===")
    print("1. Go to: https://developers.facebook.com/tools/explorer/")
    print("2. Select your app")
    print("3. Get User Access Token with these permissions:")
    print("   - instagram_graph_user_profile")
    print("   - instagram_graph_user_media")
    print("   - pages_show_list")
    print("   - pages_read_engagement")
    print("4. Copy the short-lived token below")
    print()
    
    short_lived_token = input("Enter your short-lived token: ").strip()
    
    if not short_lived_token:
        print("ERROR: No token provided")
        return
    
    if APP_ID == "your-app-id-here" or APP_SECRET == "your-app-secret-here":
        print("ERROR: Please update APP_ID and APP_SECRET in the configuration section")
        return
    
    token_manager = InstagramTokenManager(APP_ID, APP_SECRET)
    success = token_manager.exchange_for_long_lived_token(short_lived_token)
    
    if success:
        print("✅ Long-lived token saved to instagram_token.json!")
        print("✅ You can now run the bot normally.")
    else:
        print("❌ Token exchange failed. Check your app credentials.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_token()
    else:
        main()
