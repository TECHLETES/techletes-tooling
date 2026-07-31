# Google OAuth Setup Guide

This guide walks you through setting up Google Sign-In for your application.

## Prerequisites

- Google account with access to Google Cloud Console
- Application deployed or running locally
- Backend and frontend running or configured to run

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Click on the project dropdown at the top and select **"New Project"**
4. Enter a project name (e.g., "Full Stack App")
5. Click **"Create"**
6. Wait for the project to be created and select it

## Step 2: Enable Google+ API

1. In the Google Cloud Console, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google+ API"**
3. Click on **"Google+ API"**
4. Click the **"Enable"** button

Note: You might see deprecation warnings about Google+ API. That's okay—the `Google+ API` is still used for OAuth.

## Step 3: Create OAuth 2.0 Credentials

1. Go to **"APIs & Services"** → **"Credentials"** (left sidebar)
2. Click **"+ Create Credentials"** button
3. Select **"OAuth client ID"**
4. If prompted to create an OAuth consent screen:
   - Select **"External"** for user type
   - Fill in the required app information:
     - App name: Your application name
     - User support email: Your email
     - Developer contact: Your email
   - Click **"Save and Continue"**
   - For scopes, you don't need to add any (Google Sign-In works with default scopes)
   - Add test users if needed (optional)
   - Click **"Save and Continue"**

5. Back to credentials creation:
   - Application type: **"Web application"**
   - Name: e.g., "Web Client"
   - Under **"Authorized JavaScript origins"**, add:
     - `http://localhost:5173` (for local development)
     - `http://localhost:3000` (if using different port)
     - Your production domain (e.g., `https://myapp.com`)

   - Under **"Authorized redirect URIs"**, add:
     - `http://localhost:5173/` (for local development)
     - `http://localhost:5173/login` (login page)
     - Your production URLs following same pattern

6. Click **"Create"**
7. A dialog shows your credentials:
   - Copy the **"Client ID"** — you'll need this for the frontend
   - Copy the **"Client Secret"** — you'll need this for the backend

## Step 4: Configure Your Application

### Backend Configuration

Create or update your `.env` file in the project root:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
```

The `GOOGLE_CLIENT_ID` should look like:
```
123456789-abc1def2ghi3jkl4mno5pqr6stu7.apps.googleusercontent.com

```

## Step 5: Start the Application

Start both backend and frontend:

```bash
# Terminal 1 - Backend
cd backend
uv sync
./scripts/run-dev.sh

# Terminal 2 - Frontend
cd frontend
bun install  # if not already done
bun run dev
```

The frontend will fetch the Google config from the backend on startup.

## Step 6: Test Google Sign-In

1. Open `http://localhost:5173/login` in your browser
2. You should see a **"Sign in with Google"** button
3. Click the button
4. You'll be redirected to Google's login
5. Sign in with your Google account
6. You should be redirected back and logged in to the app

## Common Issues & Troubleshooting

### "Sign in with Google" button doesn't appear

**Cause**: Google OAuth is not configured or initialization failed

**Solution**:
1. Check that `GOOGLE_CLIENT_ID` is set in `.env`
2. Restart the backend: `uv run fastapi dev main.py`
3. Open browser console and check for errors
4. Verify the backend endpoint: `curl http://localhost:8000/api/v1/auth/google/config`
   - Should return: `{"enabled": true, "client_id": "your-client-id"}`

### "Failed to sign in with Google" error

**Cause**: Token validation failed or credentials mismatch

**Solutions**:
1. Verify `GOOGLE_CLIENT_ID` matches exactly in `.env`
2. Check `GOOGLE_CLIENT_SECRET` is correct
3. Verify the authorized JavaScript origins in Google Cloud Console include `localhost:5173`
4. Check backend logs for token validation errors

### "Redirect URI mismatch"

**Cause**: The redirect URI used by the frontend doesn't match authorized URIs

**Solution**:
1. Go to Google Cloud Console → Credentials
2. Click on your OAuth 2.0 Client ID
3. Under **"Authorized redirect URIs"**, ensure both are listed:
   - `http://localhost:5173`
   - `http://localhost:5173/login`

### Token validation fails with 400 error

**Cause**: Google token is invalid, expired, or audience mismatch

**Solutions**:
1. Clear browser cache and cookies for the site
2. Try signing in again with a fresh Google session
3. Check backend logs for token validation errors:
   ```bash
   # The logs will show which validation step failed
   ```
4. Verify `GOOGLE_CLIENT_ID` exactly matches in `.env` and Google Cloud Console

## Production Deployment

### Before Deploying

1. **Update Google Cloud Console**:
   - Add your production domain to "Authorized JavaScript origins"
   - Add production URLs to "Authorized redirect URIs"

   Example for `https://myapp.com`:
   ```
   Authorized JavaScript origins:
   - https://myapp.com

   Authorized redirect URIs:
   - https://myapp.com/
   - https://myapp.com/login
   ```

2. **Set Environment Variables**:
   - Use a secrets manager (AWS Secrets, Azure Key Vault, etc.)
   - Never commit `GOOGLE_CLIENT_SECRET` to git

3. **Update Frontend Configuration** (if needed):
   - Ensure `VITE_API_URL` points to your production backend

### Testing in Production

After deployment:
1. Visit `https://myapp.com/login`
2. Click "Sign in with Google"
3. Test the complete flow end-to-end
4. Monitor logs for any errors

## Security Best Practices

- ✅ Never commit secrets to version control
- ✅ Use environment variables for all credentials
- ✅ Keep `GOOGLE_CLIENT_SECRET` private (only on backend)
- ✅ Validate tokens on the backend before creating JWT
- ✅ Use HTTPS in production
- ✅ Regularly rotate OAuth credentials if compromised
- ✅ Monitor failed login attempts

## Optional: Customize User Data

The implementation automatically:
- Creates new users with Google email
- Links Google ID to existing users with same email
- Syncs name and email on each login
- Does NOT assign special roles (use admin panel if needed)

To customize behavior, edit `backend/api/routes/auth_google.py` in the `google_login()` function.

## Disabling Google Sign-In

To disable Google OAuth without removing the code:
1. Remove or leave blank `GOOGLE_CLIENT_ID` in `.env`
2. Restart the backend
3. The "Sign in with Google" button won't appear on the frontend

## Support & Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Sign-In for Web](https://developers.google.com/identity/sign-in/web)
- [@react-oauth/google Library](https://github.com/react-oauth/react-oauth.google)
- [Full-Stack Template Documentation](../README.md)

---

**Last Updated**: May 2026
**Status**: ✅ Google OAuth is fully integrated and tested
