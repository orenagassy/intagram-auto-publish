# One-time setup script
from instagram_bot import InstagramTokenManager

# Get short-lived token from: https://developers.facebook.com/tools/explorer/
short_lived_token = "EAAFcxv72G1IBPI6iRKcF6ZAyRmqpkO8CZCvDvAZBGtm1dZAJhmhRUQI23oGH2Mn95ez25R3BwfXYAZBQZBpuCVD1eUypGnrAmQqOZCCaDFeVXvSkriyYlhyZCtZCkuKcsutXpAyVk1Wdyr2cnZC5aQMJ680WBtVfSgnambYbpSsqaGVUi9gyTd4SsqCA1fBXZAnJrA95lunflvBRsJKIMsiYftmDpZCZASM5fZBsqWN73FFgIF1E1zAgZDZD"

token_manager = InstagramTokenManager("383484727532370", "01e48f513f977cd911a0315f3f247b44")
success = token_manager.exchange_for_long_lived_token(short_lived_token)

if success:
    print("✅ Long-lived token saved! You can now run the bot.")
else:
    print("❌ Token exchange failed. Check your app credentials.")