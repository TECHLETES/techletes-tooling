# Techletes Full Stack Template - Deployment

You can deploy the project with Docker Compose on a remote server.

This repository uses one unified Docker image and one root `docker-compose.yml`. Caddy handles HTTPS, frontend delivery, API reverse proxying, and the adminer subdomain.

You can also deploy with GitHub Actions. The repo already includes workflows for staging and production.

## Preparation

- Have a remote server available.
- Point your DNS records at that server.
- Install Docker Engine on the server.
- Decide the public domain for the app. The frontend is served from the apex domain, the API is available under `/api`, and Adminer is served from `adminer.<domain>`.

## Unified Docker Image

The root `Dockerfile` builds the app in two stages:

- Frontend: Bun installs dependencies and builds the Vite app.
- Backend: uv installs Python dependencies and runs FastAPI.
- Static frontend assets are copied into the backend image.
- The backend entrypoint runs startup checks, database migrations, and seed data before starting the server.

The Docker Compose stack reuses that same image for the backend and worker services.

## Stack Layout

The root `docker-compose.yml` defines:

- `db` for PostgreSQL
- `redis` for background jobs and notifications
- `backend` for the FastAPI app
- `worker` for RQ jobs
- `caddy` for HTTPS and reverse proxying
- `adminer` for database access
- `backup` for scheduled Azure Blob Storage backups

## Deploy the Code

Copy the repository to the server:

```bash
rsync -av --filter=":- .gitignore" ./ root@your-server.example.com:/root/code/app/
```

Note: `--filter=":- .gitignore"` uses the same ignore rules as git.

## Environment Variables

Create or update the `.env` file before starting the stack.

### Required Environment Variables

- `PROJECT_NAME`
- `STACK_NAME`
- `DOMAIN`
- `FRONTEND_HOST`
- `ENVIRONMENT`
- `SECRET_KEY`
- `FIRST_SUPERUSER`
- `FIRST_SUPERUSER_PASSWORD`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`

Set `FRONTEND_HOST` to the public frontend origin, for example:

```bash
export FRONTEND_HOST=https://your-domain.example.com
```

Set `BACKEND_CORS_ORIGINS` to include the frontend origin:

```bash
export BACKEND_CORS_ORIGINS="https://your-domain.example.com"
```

### Generate Secret Keys

Some variables default to `changethis`. Replace them with secure values:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Optional Environment Variables

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `EMAILS_FROM_EMAIL`
- `EMAILS_FROM_NAME`
- `REDIS_URL` is usually set by Compose and does not need manual editing
- `STORAGE_BACKEND`
- `LOCAL_STORAGE_PATH`
- `S3_BUCKET_NAME`
- `S3_ENDPOINT_URL`
- `S3_REGION`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`

## Configure Azure Blob Storage Backups

The Compose stack uses `offen/docker-volume-backup:v2` to archive selected persistent volumes and upload them to Azure Blob Storage. PostgreSQL is backed up with a native custom-format dump immediately before archiving; the live PostgreSQL data directory is not copied.

Techletes backup conventions:

- Storage account: `techletesbackups`
- Blob container: `docker-<app>-<environment>`
- Backup filename prefix: `<app>-<environment>-`
- Default schedule: daily at 03:00 in `Europe/Amsterdam`
- Default retention: 30 days
- SAS permissions: read, add, create, write, delete, and list (`racwdl`)

Examples:

```text
docker-ragflow-staging
docker-ragflow-production
docker-crisisbuddy-production
```

### Prerequisites

The workstation or devcontainer from which you provision the Azure resources must have:

- Azure CLI installed;
- access to the Techletes Azure subscription;
- permission to create Blob containers in `techletesbackups`;
- permission to read the storage-account keys.

Authenticate and verify the selected account:

```bash
az login
az account show
```

### Provision the Container and SAS

The centrally maintained provisioning script is served from:

```text
https://setup.techletes.ai/setup-azure-backup.sh
```

Download it before execution so it can be inspected:

```bash
curl -fsSLo /tmp/setup-azure-backup.sh \
  https://setup.techletes.ai/setup-azure-backup.sh
chmod 700 /tmp/setup-azure-backup.sh
```

Run it first without `--apply`. Dry-run is the default:

```bash
/tmp/setup-azure-backup.sh \
  --app ragflow \
  --environment staging \
  --allowed-ip <VPS_PUBLIC_IP> \
  --expiry-days 365
```

Review the derived container name, expiry, permissions, HTTPS restriction, and optional IP restriction. Then create the private container and generate the container-scoped SAS:

```bash
/tmp/setup-azure-backup.sh \
  --app ragflow \
  --environment staging \
  --allowed-ip <VPS_PUBLIC_IP> \
  --expiry-days 365 \
  --apply
```

The script:

1. verifies Azure CLI authentication;
2. derives `docker-<app>-<environment>`;
3. creates the private container if it does not already exist;
4. retrieves the storage-account key in memory;
5. generates an HTTPS-only container SAS;
6. prints the connection string and a copy-ready backup `.env` block;
7. clears sensitive shell variables before exiting.

The script does not create or modify the storage account, RBAC assignments, lifecycle rules, versioning, soft delete, or firewall settings.

Do not pipe the remote script directly to Bash. Download and inspect it first.

### Configure the Deployment Environment

Copy the values printed by the script into the deployment server's untracked `.env` file. The required shape is:

```dotenv
BACKUP_CRON_EXPRESSION=0 3 * * *
BACKUP_RETENTION_DAYS=30
BACKUP_FILENAME=ragflow-staging-%Y-%m-%dT%H-%M-%S.{{ .Extension }}
BACKUP_PRUNING_PREFIX=ragflow-staging-
AZURE_STORAGE_ACCOUNT_NAME=techletesbackups
AZURE_STORAGE_CONTAINER_NAME=docker-ragflow-staging
AZURE_STORAGE_CONNECTION_STRING='BlobEndpoint=https://techletesbackups.blob.core.windows.net/;SharedAccessSignature=<sas-token>'
```

The SAS connection string is a secret. Do not commit it, add it to example environment files, paste it into documentation, or expose it in logs.

Keep the filename reference in Compose as:

```yaml
BACKUP_FILENAME: ${BACKUP_FILENAME}
```

Do not use a Compose default expression containing `{{ .Extension }}`. Compose can interpret the closing braces incorrectly and produce filenames ending in `}`.

### PostgreSQL Native Dump

Before each archive, the `db` container writes a custom-format dump to the dedicated `database_backups` volume. The backup service archives that volume and the lifecycle cleanup removes the temporary dump afterwards.

The live PostgreSQL volume must not be mounted under `/backup`.

Test dump creation manually when troubleshooting:

```bash
docker compose exec db pg_dump \
  --username="$POSTGRES_USER" \
  --dbname="$POSTGRES_DB" \
  --format=custom \
  --file=/database-backups/database.dump
```

Adapt password handling to the deployed database configuration. Never print the database password.

### Start and Test Backups

Render and validate the Compose configuration:

```bash
docker compose config
./scripts/test-backup-config.sh
```

Start or recreate the backup service:

```bash
docker compose up -d --force-recreate backup
docker compose logs --tail=100 backup
```

Run one backup immediately rather than waiting for the schedule:

```bash
docker compose exec backup backup
```

Fallback when the service is not running:

```bash
docker compose run --rm --entrypoint backup backup
```

Verify the resulting Blob through Azure CLI:

```bash
az storage blob list \
  --account-name techletesbackups \
  --container-name docker-ragflow-staging \
  --auth-mode login \
  --query '[].{name:name,size:properties.contentLength,lastModified:properties.lastModified}' \
  --output table
```

If the Azure identity lacks Blob data-plane access, verify the private container through the Azure Portal.

### Rotate the SAS

SAS tokens cannot be retrieved later. To rotate one:

1. download the current central script again;
2. rerun it with the same app and environment plus `--apply`;
3. replace `AZURE_STORAGE_CONNECTION_STRING` in the server `.env`;
4. recreate the backup service;
5. run an immediate backup test.

```bash
docker compose up -d --force-recreate backup
./scripts/test-backup-config.sh --run
```

An old SAS remains valid until its expiry unless the underlying account key is rotated.

### Restore PostgreSQL

Download and extract the selected backup, locate `database/database.dump`, stop application writers, restore the dump, restart the application, and validate health.

```bash
docker compose stop backend worker

docker compose exec -T db pg_restore \
  --clean \
  --if-exists \
  --no-owner \
  --username="$POSTGRES_USER" \
  --dbname="$POSTGRES_DB" \
  < database.dump

docker compose up -d backend worker
```

`--clean` is destructive. Test restores against a disposable database before restoring production.

### Backup Troubleshooting

- SAS expired: generate a new SAS and recreate the backup service.
- VPS IP changed: regenerate the SAS with the current `--allowed-ip` or omit the restriction.
- Upload works but pruning fails: verify `delete` and `list` permissions and the pruning prefix.
- Filename ends with `}`: remove Compose defaults around `{{ .Extension }}`.
- Archive is empty: verify selected volumes are mounted read-only below `/backup`.
- PostgreSQL dump fails: inspect `db` health, credentials, lifecycle labels, and backup logs.
- Wrong schedule time: verify the backup service uses `TZ=Europe/Amsterdam`.
- Azure CLI is unauthenticated: run `az login` and `az account show`.
- Azure identity lacks permissions: request container-creation and storage-key access.

## Deploy with Docker Compose

From the repository root:

```bash
docker compose -f docker-compose.yml up -d --build
```

For later updates, rerun the same command after pulling or copying the new code.

## Continuous Deployment

The repository already includes GitHub Actions deployment workflows for `staging` and `production`.

Typical secrets used by those workflows include:

- `DOMAIN_PRODUCTION`
- `DOMAIN_STAGING`
- `STACK_NAME_PRODUCTION`
- `STACK_NAME_STAGING`
- `EMAILS_FROM_EMAIL`
- `FIRST_SUPERUSER`
- `FIRST_SUPERUSER_PASSWORD`
- `POSTGRES_PASSWORD`
- `SECRET_KEY`
- `LATEST_CHANGES`
- `SMOKESHOW_AUTH_KEY`

## URLs

Replace `your-domain.example.com` with your real domain.

### Production

- Frontend: `https://your-domain.example.com`
- Backend API docs: `https://your-domain.example.com/api/v1/docs`
- Backend API base URL: `https://your-domain.example.com/api`
- Adminer: `https://adminer.your-domain.example.com`

### Staging

- Frontend: `https://staging.your-domain.example.com`
- Backend API docs: `https://staging.your-domain.example.com/api/v1/docs`
- Backend API base URL: `https://staging.your-domain.example.com/api`
- Adminer: `https://adminer.staging.your-domain.example.com`
