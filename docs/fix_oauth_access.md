# Fix Google OAuth Access Denied Error

## Quick Fix Steps:

1. **Go to Google Cloud Console:**
   - Open https://console.cloud.google.com/
   - Make sure you're in the correct project (should match your credentials.json)

2. **Navigate to OAuth consent screen:**
   - In the left menu, go to "APIs & Services" > "OAuth consent screen"

3. **Add Test Users:**
   - Scroll down to the "Test users" section
   - Click "+ ADD USERS"
   - Add your email address: andrewhting@gmail.com
   - Click "SAVE"

4. **Alternative: Set to Internal (if using Google Workspace):**
   - If you have a Google Workspace account, you can set the app to "Internal"
   - This allows all users in your organization to use it without verification

5. **Try authentication again:**
   - Run `python test_gmail.py` again
   - The authentication should now work

## If you need to create a new OAuth app:

1. Go to "APIs & Services" > "Credentials"
2. Click "+ CREATE CREDENTIALS" > "OAuth client ID"
3. Choose "Desktop app" as application type
4. Download the new credentials and replace credentials.json

## Note:
For personal automation tools, keeping the app in "Testing" mode with your email as a test user is perfectly fine. You don't need to go through the full verification process.