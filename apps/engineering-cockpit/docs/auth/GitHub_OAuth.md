# GitHub OAuth Setup Guide

This guide walks you through setting up GitHub Sign-In for your application.

## Prerequisites

- GitHub account
- Application deployed or running locally
- Backend and frontend running or configured to run
- Familiarity with GitHub Developer Settings

## Step 1: Create a GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
   - Or: GitHub → Settings → Developer settings (bottom left) → OAuth Apps

2. Click **"New OAuth App"** button

3. Fill in the application details:
   - **Application name**: Your application name (e.g., "Full Stack App")
   - **Homepage URL**:
     - For local development: `http://localhost:5173`
     - For production: `https://yourdomain.com`

   - **Application description** (optional): Description of your app

   - **Authorization callback URL**:
     - For local development: `http://localhost:5173/auth/github/callback`
     - For production: `https://yourdomain.com/auth/github/callback`

4. Click **"Register application"**

5. You'll see your OAuth app details page. You need:
   - **Client ID**: Copy this value
   - **Client Secret**: Click **"Generate a new client secret"** and copy it
     - ⚠️ **Important**: Save the secret immediately—GitHub won't show it again

## Step 2: Configure Your Application

### Backend Configuration

Create or update your `.env` file in the project root:

```bash
# GitHub OAuth
GITHUB_CLIENT_ID=your-client-id-here
GITHUB_CLIENT_SECRET=your-client-secret-here
```

The `GITHUB_CLIENT_ID` should look like:
```
1a2b3c4d5e6f7g8h9i0j
```

The `GITHUB_CLIENT_SECRET` should look like:
```
gho_1234567890abcdefghijklmnopqrstuvwxyz
```

⚠️ **Security**: Never commit secrets to git. Use a `.env` file in your project root (it's in `.gitignore`).

## Step 3: Start the Application

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

The frontend will fetch the GitHub config from the backend on startup.

## Step 4: Test GitHub Sign-In

1. Open `http://localhost:5173/login` in your browser
2. You should see a **"Sign in with GitHub"** button
3. Click the button
4. You'll be redirected to GitHub's authorization page
5. Click **"Authorize [Your App Name]"**
6. You should be redirected back and logged in to the app

## How It Works

### Authentication Flow

1. **Frontend**: User clicks "Sign in with GitHub" button
2. **Redirect to GitHub**: Browser redirects to GitHub authorization URL
3. **GitHub Login**: User logs in with GitHub credentials (if not already)
4. **Authorization**: GitHub shows permissions request, user authorizes
5. **Callback**: GitHub redirects back to `http://localhost:5173/auth/github/callback` with authorization `code`
6. **Backend Exchange**: Frontend sends `code` to backend `/api/v1/auth/github/exchange-code`
7. **Token Exchange**: Backend exchanges `code` for GitHub access token
8. **User Lookup**: Backend fetches user info from GitHub API
9. **Account Linking**:
   - If user exists with same GitHub ID → Use existing account
   - If user exists with same email → Link GitHub account
   - Otherwise → Create new user
10. **JWT Response**: Backend returns JWT token to frontend
11. **Login Complete**: Frontend stores token and redirects to dashboard

### Permissions

GitHub OAuth requests the following scopes (automatically):
- **User email**: Read user's public and private email addresses
- **Public profile**: Read public profile information (username, avatar, etc.)

## Common Issues & Troubleshooting

### "Sign in with GitHub" button doesn't appear

**Cause**: GitHub OAuth is not configured or initialization failed

**Solution**:
1. Check that `GITHUB_CLIENT_ID` is set in `.env`
2. Restart the backend: `uv run fastapi dev main.py`
3. Open browser console (F12) and check for errors
4. Verify the backend endpoint returns config:
   ```bash
   curl http://localhost:8000/api/v1/auth/github/config
   ```
   Should return: `{"enabled": true, "client_id": "your-client-id"}`

### "Failed to sign in with GitHub" error

**Cause**: Token validation failed or credentials mismatch

**Solutions**:
1. Verify `GITHUB_CLIENT_ID` in `.env` matches exactly
2. Check `GITHUB_CLIENT_SECRET` is correct (regenerate if unsure)
3. Verify the Authorization callback URL in GitHub settings matches:
   - `http://localhost:5173/auth/github/callback` (local)
4. Check backend logs for detailed error messages

### "Could not retrieve email from GitHub account" error

**Cause**: GitHub account doesn't have an accessible email

**Solution**:
1. Ensure your GitHub account has a public email or primary email set:
   - GitHub → Settings → Emails
   - Set a primary email or make one public
2. Try signing in again

### "Authorization callback URL mismatch"

**Cause**: The redirect URL used by the frontend doesn't match GitHub settings

**Solution**:
1. Go to [GitHub Developer Settings → OAuth Apps](https://github.com/settings/developers)
2. Click your app
3. Update **"Authorization callback URL"** to match your frontend:
   - Local: `http://localhost:5173/auth/github/callback`
   - Production: `https://yourdomain.com/auth/github/callback`

### Token validation fails silently

**Cause**: Invalid or expired GitHub token

**Solutions**:
1. Clear browser cookies and try again
2. Check backend logs for token validation errors:
   ```bash
   # Look for: "Failed to validate GitHub token" or "Failed to exchange GitHub code"
   ```
3. Ensure your GitHub app credentials are correct in `.env`
4. Try regenerating the Client Secret in GitHub settings

### "State parameter mismatch" error

**Cause**: CSRF protection detected a mismatch (security feature)

**Solution**:
1. This is usually temporary. Try signing in again.
2. If persistent, clear browser local storage and cookies
3. Restart the frontend dev server

## Production Deployment

### Before Deploying

1. **Update GitHub OAuth App Settings**:
   - Go to your app settings
   - Update **"Homepage URL"**: `https://yourdomain.com`
   - Update **"Authorization callback URL"**: `https://yourdomain.com/auth/github/callback`

   Example:
   ```
   Homepage URL: https://myapp.com
   Authorization callback URL: https://myapp.com/auth/github/callback
   ```

2. **Set Environment Variables**:
   - Use a secrets manager (AWS Secrets, Azure Key Vault, etc.)
   - Never commit `GITHUB_CLIENT_SECRET` to git
   - Set in your production environment:
     ```bash
     GITHUB_CLIENT_ID=your-prod-client-id
     GITHUB_CLIENT_SECRET=your-prod-client-secret
     ```

3. **Verify Frontend Configuration**:
   - Ensure `VITE_API_URL` or equivalent points to your production backend
   - Or configure via environment: `http://yourdomain.com/api/v1`

### Testing in Production

After deployment:
1. Visit `https://yourdomain.com/login`
2. Click "Sign in with GitHub"
3. Authorize the application
4. Verify you're logged in and redirected to dashboard
5. Monitor logs for any errors

## Multi-Environment Setup

To use different OAuth apps for development and production:

1. **Create two GitHub OAuth Apps**:
   - One for local development (callback: `http://localhost:5173/auth/github/callback`)
   - One for production (callback: `https://yourdomain.com/auth/github/callback`)

2. **Use environment-specific `.env` files**:
   ```bash
   # .env.local (for local development)
   GITHUB_CLIENT_ID=dev-client-id
   GITHUB_CLIENT_SECRET=dev-client-secret

   # .env.production (for production)
   GITHUB_CLIENT_ID=prod-client-id
   GITHUB_CLIENT_SECRET=prod-client-secret
   ```

3. **Load the correct file**:
   - Backend automatically loads `.env` from root
   - Use `python-dotenv` with specific file paths if needed

## Security Best Practices

- ✅ Never commit `GITHUB_CLIENT_SECRET` to version control
- ✅ Use environment variables for all credentials
- ✅ Keep `GITHUB_CLIENT_SECRET` private (only on backend)
- ✅ Validate GitHub tokens on the backend before creating JWT
- ✅ Use HTTPS in production
- ✅ Regenerate Client Secret if compromised:
   - GitHub Settings → Developer settings → OAuth Apps → Your App → "Generate a new client secret"
- ✅ Monitor failed login attempts in logs
- ✅ Use CSRF protection (state parameter) in OAuth flow
- ✅ Don't request unnecessary scopes

## User Data Synchronization

The implementation automatically:
- Creates new users with GitHub email
- Links GitHub account to existing users with same email
- Updates user info (username, full name) on each login
- Stores GitHub user ID for account linking
- Does NOT assign special roles (use admin panel if needed)

To customize behavior, edit `backend/api/routes/auth_github.py` in the `github_login()` function.

## Account Linking Behavior

When a user signs in with GitHub:

1. **First-time login**:
   - GitHub account doesn't exist in database
   - Email check: If email exists in system → Link to existing account
   - If email is new → Create new user with GitHub account linked

2. **Existing GitHub account**:
   - User signs in again with same GitHub account
   - Application finds user by GitHub ID
   - User data is synced

3. **Email-based linking**:
   - User has existing account with email: `jane@example.com`
   - Logs in with GitHub using same email
   - GitHub account automatically linked to existing user
   - Future logins use GitHub authentication

## Disabling GitHub Sign-In

To disable GitHub OAuth without removing the code:

1. Remove or leave blank `GITHUB_CLIENT_ID` in `.env`:
   ```bash
   GITHUB_CLIENT_ID=
   GITHUB_CLIENT_SECRET=
   ```

2. Restart the backend

3. The "Sign in with GitHub" button won't appear on the frontend

4. Existing GitHub-linked accounts can still log in via email/password if configured

## Troubleshooting: GitHub API Limits

GitHub's OAuth endpoints have rate limits. If you hit them:

**Error**: `{"message": "API rate limit exceeded"}`

**Solution**:
1. Wait 1 hour (rate limit resets)
2. For development, use a personal GitHub account with higher limits
3. For production, GitHub doesn't rate-limit OAuth token exchange

## Support & Resources

- [GitHub OAuth Documentation](https://docs.github.com/en/developers/apps/building-oauth-apps)
- [GitHub OAuth Web Application Flow](https://docs.github.com/en/developers/apps/building-oauth-apps/authorizing-oauth-apps)
- [GitHub API - Get Authenticated User](https://docs.github.com/en/rest/users/users#get-the-authenticated-user)
- [GitHub API - Get User Emails](https://docs.github.com/en/rest/users/emails)
- [Full-Stack Template Documentation](../README.md)

## Comparing OAuth Providers

| Feature | Google | GitHub | Microsoft Entra |
|---------|--------|--------|-----------------|
| Roles/RBAC | ❌ No | ❌ No | ✅ Yes |
| Enterprise | ⚠️ Limited | ✅ Teams | ✅ Yes |
| Setup Complexity | Medium | Easy | Hard |
| Best For | Consumer apps | Developer apps | Enterprise |

---

**Last Updated**: May 2026
**Status**: ✅ GitHub OAuth is fully integrated and tested
