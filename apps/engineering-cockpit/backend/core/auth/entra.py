"""Microsoft Entra (Azure AD) authentication client utilities."""

import logging
from typing import Any, cast
from urllib.parse import urlencode
from uuid import uuid4

import httpx
import jwt
from jwt import PyJWKClient

from backend.core.config import settings
from backend.core.constants import constants

logger = logging.getLogger(__name__)


class EntraAuthClient:
    """Handle Microsoft Entra (Azure AD) authentication."""

    def __init__(self) -> None:
        """Initialize the Entra auth client with configuration values."""
        self.authority = settings.AZURE_AUTHORITY
        self.client_id = settings.AZURE_CLIENT_ID
        self.client_secret = settings.AZURE_CLIENT_SECRET
        self.graph_api = constants.entra.GRAPH_API_BASE_URL

    def _get_tenant_id(self, tenant_id: str | None = None) -> str:
        if tenant_id:
            return tenant_id
        if settings.AZURE_TENANT_ID:
            return str(settings.AZURE_TENANT_ID)
        return constants.entra.DEFAULT_TENANT

    def get_authority(self, tenant_id: str | None = None) -> str:
        """Return the public authority URL for the selected tenant."""
        return f"{self.authority}/{self._get_tenant_id(tenant_id)}"

    def _get_openid_configuration(self, tenant_id: str | None = None) -> dict[str, Any]:
        metadata_url = (
            f"{self.get_authority(tenant_id)}/v2.0/.well-known/openid-configuration"
        )
        with httpx.Client() as client:
            response = client.get(metadata_url, timeout=10.0)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

    def verify_id_token(self, id_token: str) -> dict[str, Any]:
        """Verify an Entra ID token for this application and return its claims."""
        unverified_claims = cast(
            dict[str, Any],
            jwt.decode(
                id_token,
                options={
                    "verify_signature": False,
                    "verify_aud": False,
                    "verify_exp": False,
                },
                algorithms=["RS256"],
            ),
        )

        token_tenant_id = cast(str | None, unverified_claims.get("tid"))
        if settings.AZURE_TENANT_ID and token_tenant_id != settings.AZURE_TENANT_ID:
            raise Exception("Unexpected Entra tenant")

        oidc_config = self._get_openid_configuration(token_tenant_id)
        signing_key = PyJWKClient(oidc_config["jwks_uri"]).get_signing_key_from_jwt(
            id_token
        )
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self.client_id,
            issuer=oidc_config["issuer"],
        )
        return cast(dict[str, Any], claims)

    def _get_application(
        self,
        client: httpx.Client,
        headers: dict[str, str],
        select_fields: str,
    ) -> dict[str, Any] | None:
        app_resp = client.get(
            f"{self.graph_api}/applications"
            f"?$filter=appId eq '{self.client_id}'&$select={select_fields}",
            headers=headers,
        )
        if app_resp.status_code != 200:
            raise Exception(f"Failed to load Entra application: {app_resp.text}")

        apps = app_resp.json().get("value", [])
        if not apps:
            return None

        return cast(dict[str, Any], apps[0])

    def get_token_by_auth_code(
        self,
        auth_code: str,
        redirect_uri: str,
        tenant_id: str | None = None,
    ) -> dict[str, str]:
        """Exchange authorization code for access token."""
        tid = self._get_tenant_id(tenant_id)
        token_url = f"{self.authority}/{tid}/oauth2/v2.0/token"

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": auth_code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "scope": "openid profile email " + settings.AZURE_GRAPH_SCOPE,
        }

        with httpx.Client() as client:
            resp = client.post(token_url, data=payload)
            if resp.status_code == 200:
                return resp.json()  # type: ignore[no-any-return]
            raise Exception(f"Token exchange failed: {resp.text}")

    def get_user_info(self, access_token: str) -> dict[str, str]:
        """Get user info from Microsoft Graph."""
        headers = {"Authorization": f"Bearer {access_token}"}

        with httpx.Client() as client:
            resp = client.get(f"{self.graph_api}/me", headers=headers)
            if resp.status_code == 200:
                return resp.json()  # type: ignore[no-any-return]
            raise Exception(f"Failed to get user info: {resp.status_code}")

    def get_login_url(
        self,
        redirect_uri: str,
        tenant_id: str | None = None,
        state: str | None = None,
    ) -> str:
        """Generate Microsoft login URL."""
        tid = self._get_tenant_id(tenant_id)

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "response_mode": "query",
            "scope": "openid profile email " + settings.AZURE_GRAPH_SCOPE,
            "state": state or uuid4().hex,
        }

        query_string = urlencode(params)
        return f"{self.authority}/{tid}/oauth2/v2.0/authorize?{query_string}"

    def _get_service_principal_token(self) -> str:
        """Get service principal token for Graph API calls."""
        token_url = f"{self.authority}/{settings.AZURE_TENANT_ID}/oauth2/v2.0/token"

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "https://graph.microsoft.com/.default",
        }

        with httpx.Client() as client:
            resp = client.post(token_url, data=payload)
            if resp.status_code == 200:
                token_response = resp.json()
                return str(token_response["access_token"])
            raise Exception(f"Failed to get service principal token: {resp.text}")

    def get_application_roles(self) -> list[dict[str, Any]]:
        """Return enabled user-assignable app roles from the Entra application."""
        if not self.client_id or not self.client_secret:
            return []

        try:
            token = self._get_service_principal_token()
            headers = {"Authorization": f"Bearer {token}"}

            with httpx.Client() as client:
                application = self._get_application(client, headers, "id,appRoles")
                if not application:
                    return []

                app_roles = cast(list[dict[str, Any]], application.get("appRoles", []))
                return [
                    role
                    for role in app_roles
                    if role.get("isEnabled", True)
                    and constants.entra.APP_ROLE_MEMBER_TYPE_USER
                    in role.get("allowedMemberTypes", [])
                ]
        except Exception as e:
            logger.error(f"Failed to fetch app roles from Entra: {e}")
            return []

    def sync_app_roles_to_manifest(self, roles: list[dict[str, str]]) -> bool:
        """
        Sync application roles to Entra app manifest.

        Args:
            roles: List of role dicts with format:
                {"id": "uuid", "displayName": "admin", "value": "admin"}

        Returns:
            True if successful, False otherwise
        """
        if not self.client_id or not self.client_secret:
            return False

        try:
            token = self._get_service_principal_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            # Get current app
            with httpx.Client() as client:
                application = self._get_application(client, headers, "id")
                if not application:
                    return False

                app_id = application["id"]

                # Prepare app roles payload
                payload = {
                    "appRoles": [
                        {
                            "id": role["id"],
                            "allowedMemberTypes": [
                                constants.entra.APP_ROLE_MEMBER_TYPE_USER
                            ],
                            "description": role.get("description", role["displayName"]),
                            "displayName": role["displayName"],
                            "isEnabled": True,
                            "value": role["value"],
                        }
                        for role in roles
                    ]
                }

                # Update app manifest
                update_resp = client.patch(
                    f"{self.graph_api}/applications/{app_id}",
                    json=payload,
                    headers=headers,
                )

                return cast(bool, update_resp.status_code == 200)

        except Exception as e:
            logger.error(f"Failed to sync roles to Entra: {e}")
            return False
