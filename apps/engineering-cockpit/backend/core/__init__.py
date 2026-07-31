"""Core backend utilities and shared configuration.

Organized into logical submodules:
  - auth/: Authentication (OAuth providers, JWT, password hashing)
  - queue/: Background jobs (RQ, Redis, callbacks)
  - storage/: File storage backends (local, S3)
  - config.py: Environment configuration
  - db.py: Database connection
  - rbac.py: Role-based access control
"""
