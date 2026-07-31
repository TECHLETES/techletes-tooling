# Microsoft Entra Integration Setup Guide

This template supports Microsoft Entra (Azure AD) authentication. The feature is **opt-in** — leave `AZURE_CLIENT_ID` empty to disable.

## Quick Start

1. Register your app in Azure Entra (see "Azure Setup Instructions" below)
2. Set these environment variables in `.env`:
   ```bash
   AZURE_CLIENT_ID=<your-client-id>
   AZURE_CLIENT_SECRET=<your-client-secret>
   AZURE_TENANT_ID=<your-tenant-id>
   ```
3. Run migrations: `cd backend && alembic upgrade head`
4. Restart: `docker compose up --build`
5. "Sign in with Microsoft" button appears on login page

## Authentication Flow

```
1. User clicks "Sign in with Microsoft"
   ↓
2. Frontend (MSAL) redirects to Microsoft login
   ↓
3. User authenticates with their Microsoft account
   ↓
4. Microsoft returns access token + ID token (with app roles) to frontend
   ↓
5. Frontend extracts roles from ID token claims and sends to backend /auth/entra/login
   ↓
6. Backend validates access token via Microsoft Graph API to ensure it's valid
   ↓
7. Backend creates/updates user in database with app roles, returns JWT
   ↓
8. Frontend stores JWT and uses for all subsequent API calls
```

**Key Point:** App roles are assigned by your Azure tenant admin in the Azure Portal. When a user logs in, the roles are included in the ID token and sent to the backend. No extra Graph API permissions are needed.

---

## Azure Entra Setup Instructions

### Step 1: Create an Azure Tenant (if needed)

Skip if you already have an Azure subscription and tenant.

1. Go to [Microsoft Entra Admin Center](https://entra.microsoft.com/)
2. Sign in with your work or personal Microsoft account
3. Navigate to **Tenants** → **Create** → Enter tenant details
4. Wait for tenant creation (may take a few minutes)

### Step 2: Register the Application

1. Go to [Microsoft Entra Admin Center](https://entra.microsoft.com/)
2. Navigate to **Applications** → **App registrations**
3. Click **New registration**

**Fill in:**
- **Name:** `Techletes Full-Stack Template` (or your app name)
- **Supported account types:**
  - *Single-tenant:* `Accounts in this organizational directory only`
  - *Multi-tenant:* `Accounts in any organizational directory (Any Azure AD directory – Multitenant)`
- **Redirect URI:**
  - Type: `Single-page application (SPA)`
  - URI: `http://localhost:5173` (for local development)
  - *For production, add: `https://yourdomain.com` (without trailing slash)*

Click **Register**

### Step 3: Get Credentials

After registration, you'll see the **Overview** page.

**Copy these values to `.env`:**

1. **Application (client) ID** → Set as `AZURE_CLIENT_ID`
2. **Directory (tenant) ID** → Set as `AZURE_TENANT_ID`

Example:
```env
AZURE_CLIENT_ID=00001111-2222-3333-4444-555566667777
AZURE_TENANT_ID=aaaabbbb-cccc-dddd-eeee-ffff00001111
```

### Step 4: Create Client Secret

1. In app registration, go to **Certificates & secrets**
2. Under **Client secrets**, click **New client secret**
3. Add description: `Backend server secret`
4. Set expiry: `24 months` (or your security policy)
5. Click **Add**
6. **Copy the Value** → Set as `AZURE_CLIENT_SECRET` (backend)

⚠️ **Important:** Store this secret securely. Never commit to version control.

### Step 5: Set API Permissions

### Step 5: Configure App Roles

App roles allow tenant admins to assign roles to users. When users log in, their assigned roles are automatically included in the ID token.

**1. Create app roles through the UI:**

1. In app registration, go to **App roles**
2. Click **Create app role**
3. Fill in the form:
   - **Display name:** `Admin`
   - **Allowed member types:** Check `Users/Groups`
   - **Value:** `Admin` (this is what appears in the token's `roles` claim)
   - **Description:** `Admin role with full access`
   - **Do you want to enable this app role?:** Check this box
4. Click **Apply**
5. Repeat to create additional roles:
   - **Display name:** `Editor`, **Value:** `Editor`, **Description:** `Editor role with content management access`
   - **Display name:** `Viewer`, **Value:** `Viewer`, **Description:** `Viewer role with read-only access`

**2. Assign roles to users:**

1. Go to **Enterprise applications**
2. Find and select your app
3. Go to **Users and groups**
4. Click **Add user/group**
5. Select a user
6. Select **Select a role** and choose the role(s) to assign
7. Click **Assign**

**Important:** Once you assign a user to a role, that role appears automatically in the ID token (`roles` claim) when they log in. No additional token configuration is needed.

### Step 6: Set API Permissions

The app needs minimum permissions to read user profile info.

1. In app registration, go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph** → **Delegated permissions**
4. Search for and add:
   - `openid` (OIDC)
   - `profile` (User profile)
   - `email` (Email address)
   - `User.Read` (Read user profile)

5. Click **Add permissions**

**Note:** If you used the old `Directory.Read.All` permission for roles, you can remove it now since roles come from token claims.

---

### Backend Setup (.env)

Set these environment variables in `.env`:

```env
# Microsoft Entra Configuration
AZURE_CLIENT_ID=00001111-2222-3333-4444-555566667777
AZURE_CLIENT_SECRET=your_client_secret_here
AZURE_TENANT_ID=aaaabbbb-cccc-dddd-eeee-ffff00001111
```

The frontend automatically fetches the public configuration from the backend API (`/api/v1/auth/entra/config`) at startup—no additional frontend env vars needed.

---

## Testing the Integration

### 1. Start the Application

```bash
docker compose up --build
# OR for development:
# Backend: cd backend && uv run fastapi dev main.py
# Frontend: cd frontend && bun run dev
```

### 2. Test Login

1. Go to http://localhost:5173 (frontend)
2. Click **Sign in with Microsoft**
3. You should be redirected to Microsoft login
4. Enter your Microsoft account credentials
5. You may see a consent screen (first time only)
6. After consent, you should be logged in
7. User data should appear on the dashboard

### 3. Test Multi-Tenant (if enabled)

**Add a new tenant via admin API:**

```bash
curl -X POST http://localhost:8000/api/v1/tenants/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "new-customer-tenant-id",
    "tenant_name": "Customer Corp",
    "is_enabled": true,
    "auto_create_users": true
  }'
```

Users from that tenant can now log in.

### 4. Debug Issues

**Enable debug logging (in `.env`):**
```env
# Not implemented yet, but you can add browser console
# Check browser DevTools for MSAL debug logs
```

**Common issues:**

| Issue | Solution |
|-------|----------|
| "AADSTS700016: Application not found" | Check `AZURE_CLIENT_ID` matches registration |
| "AADSTS90002: Tenant not found" | Check `AZURE_TENANT_ID` is correct |
| "Redirect URI mismatch" | Ensure registered redirect URI is `http://localhost:5173` for dev |
| "Insufficient privileges" | Add required API permissions in Azure |
| "Sign in with Microsoft" button missing | Check Entra is enabled: `curl http://localhost:8000/api/v1/auth/entra/config` |

---

## Deployment Checklist

### Before going to production:

- [ ] Register app for production domain in Azure
- [ ] Add production redirect URI: `https://yourdomain.com`
- [ ] Rotate client secret (set expiry date)
- [ ] Set `ENVIRONMENT=production` in backend `.env`
- [ ] Use strong `SECRET_KEY` (not "changethis")
- [ ] Test login flow end-to-end
- [ ] Set up admin consent flow for customers
- [ ] Monitor API usage in Azure portal

### Production Environment Variables

Use environment-specific secret management:
- **AWS:** Secrets Manager or Parameter Store
- **Azure:** Azure Key Vault
- **GCP:** Secret Manager
- **Docker:** Docker Secrets

Example with Caddy (included in docker-compose):
```yaml
# docker-compose.prod.yml
environment:
  AZURE_CLIENT_SECRET: ${AZURE_CLIENT_SECRET}  # Load from host
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     BROWSER (SPA)                           │
│  Frontend (React + MSAL)                                    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. Fetch config from /api/v1/auth/entra/config      │   │
│  │ 2. User clicks "Sign in with Microsoft"             │   │
│  │ 3. MSAL redirects to Microsoft login (config-based) │   │
│  │ 4. User authenticates → Gets access token           │   │
│  │ 5. Token sent to backend /auth/entra/login          │   │
│  │ 6. Receives JWT token, stores in localStorage       │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                   MICROSOFT ENTRA                           │
│         https://login.microsoftonline.com                   │
│                                                              │
│  - Authenticates user                                       │
│  - Returns access token                                     │
│  - validates both frontend & backend                        │
└─────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                         │
│  Uses: AZURE_CLIENT_ID, AZURE_CLIENT_SECRET,               │
│        AZURE_TENANT_ID                                      │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. Receive Microsoft access token from frontend     │   │
│  │ 2. Call Microsoft Graph API to verify token        │   │
│  │ 3. Fetch user info & roles                          │   │
│  │ 4. Create/update user in database                   │   │
│  │ 5. Generate JWT token, return to frontend           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Database (PostgreSQL)                                      │
│  - Users with Azure metadata                               │
│  - Multi-tenant assignments                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Supported Scenarios

### ✅ Single-Tenant (One Organization)

One organization's Azure AD. Control access directly in your Azure app registration — only grant access to your tenant:
```env
AZURE_TENANT_ID=your-tenant-id
```
- All users from your tenant can log in
- Simple setup, no tenant management needed

### ✅ Multi-Tenant (SaaS Model)

Multiple customer organizations. In your Azure app registration, allow **any Azure AD tenant**. Then use the tenant management API to track and organize tenants in your app:
```env
AZURE_TENANT_ID=your-primary-tenant-id
```
- Register additional tenants via the `/api/v1/tenants/` admin API
- Each tenant can have different users & roles
- **Access control lives in Azure** — tenant management in the database is for app-level organization

### ✅ Fallback Authentication

Both Entra and email/password:
```env
AZURE_CLIENT_ID=
# Leave empty to disable Entra; email/password still works
```

---

## More Resources

- [Microsoft Entra Overview](https://learn.microsoft.com/entra/identity-platform/)
- [MSAL React Documentation](https://learn.microsoft.com/entra/msal/javascript/react/)
- [Microsoft Graph API](https://graph.microsoft.com/docs)
- [App Registration Best Practices](https://learn.microsoft.com/entra/identity-platform/app-objects-and-service-principals)
- [Multi-Tenant Applications](https://learn.microsoft.com/entra/identity-platform/howto-convert-app-to-be-multi-tenant)

---

## Support & Troubleshooting

If you encounter issues:

1. **Check logs:**
   - Backend: `docker logs full-stack-template-backend-1 | grep -i entra`
   - Frontend: Browser DevTools → Console (Ctrl+Shift+K)

2. **Verify configuration:**
   ```bash
   curl http://localhost:8000/api/v1/auth/entra/config
   ```
   Should return Azure configuration status

3. **Test token validation:**
   Replace `YOUR_MS_TOKEN` with an actual Microsoft access token:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/entra/login \
     -H "Content-Type: application/json" \
     -d '{"access_token": "YOUR_MS_TOKEN"}'
   ```

---

## Feature Roadmap

Potential enhancements:
- [ ] Automatic role sync from Microsoft groups
- [ ] Admin consent workflow UI
- [ ] Tenant onboarding wizard
- [ ] Device Code flow for CLI apps
- [ ] SAML 2.0 support
- [ ] Conditional access integration
