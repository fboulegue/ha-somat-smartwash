"""Async API client for Somat Smartwash."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import aiohttp
from yarl import URL

from .const import (
    GIGYA_API_KEY,
    GIGYA_LOGIN_URL,
    GRAPHQL_URL,
    PRODUCT_HEADER,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)


class SomatApiError(Exception):
    """Base exception for Somat Smartwash API errors."""


class SomatAuthError(SomatApiError):
    """Exception raised for authentication failure."""


class SomatConnectionError(SomatApiError):
    """Exception raised for network or connection failure."""


class SomatSmartwashApiClient:
    """API client for communication with Gigya and Somat Smartwash GraphQL."""

    def __init__(
        self,
        email: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client."""
        self.email = email
        self.password = password
        self.session = session
        self.id_token: Optional[str] = None
        self.user_id: Optional[str] = None

    async def async_login(self) -> str:
        """Authenticate with Gigya and obtain an ID Token (JWT)."""
        params = {
            "apiKey": GIGYA_API_KEY,
            "loginID": self.email,
            "password": self.password,
            "targetEnv": "mobile",
            "format": "json",
            "httpStatusCodes": "false",
            "include": "id_token",
        }
        headers = {
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            async with self.session.post(
                GIGYA_LOGIN_URL,
                data=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise SomatConnectionError(
                        f"Gigya HTTP error {response.status}: {text}"
                    )

                data = await response.json(content_type=None)
                if data.get("errorCode") != 0 or "id_token" not in data:
                    error_msg = data.get("errorMessage", "Unknown error")
                    error_details = data.get("errorDetails", "")
                    _LOGGER.error(
                        "Gigya login failed: %s (%s)", error_msg, error_details
                    )
                    raise SomatAuthError(f"{error_msg}: {error_details}")

                self.id_token = data["id_token"]
                return self.id_token

        except aiohttp.ClientError as err:
            raise SomatConnectionError(f"Error connecting to Gigya: {err}") from err

    async def async_graphql_request(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        retry_on_auth: bool = True,
    ) -> Dict[str, Any]:
        """Execute a GraphQL query or mutation with automatic token refresh."""
        if not self.id_token:
            await self.async_login()

        headers = {
            "Content-Type": "application/json",
            "product": PRODUCT_HEADER,
            "Authorization": f"Bearer {self.id_token}",
        }
        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            async with self.session.post(
                GRAPHQL_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                if response.status == 401 or response.status == 403:
                    if retry_on_auth:
                        _LOGGER.debug("Token expired, refreshing Gigya token...")
                        await self.async_login()
                        return await self.async_graphql_request(
                            query, variables, retry_on_auth=False
                        )
                    raise SomatAuthError("Authentication token rejected by Somat API")

                if response.status != 200:
                    text = await response.text()
                    raise SomatConnectionError(
                        f"Somat API HTTP error {response.status}: {text}"
                    )

                result = await response.json(content_type=None)
                if "errors" in result and result["errors"]:
                    err = result["errors"][0]
                    msg = err.get("message", "Unknown GraphQL error")
                    if "Unauthenticated" in msg and retry_on_auth:
                        _LOGGER.debug(
                            "Unauthenticated GraphQL error, refreshing token..."
                        )
                        await self.async_login()
                        return await self.async_graphql_request(
                            query, variables, retry_on_auth=False
                        )
                    raise SomatApiError(f"GraphQL Error: {msg}")

                return result.get("data", {})

        except aiohttp.ClientError as err:
            raise SomatConnectionError(
                f"Error connecting to Somat API: {err}"
            ) from err

    async def async_get_user(self) -> Dict[str, Any]:
        """Fetch current user info."""
        query = "{ user { id product country } }"
        data = await self.async_graphql_request(query)
        user = data.get("user", {})
        self.user_id = user.get("id")
        return user

    async def async_get_devices(self) -> List[Dict[str, Any]]:
        """Fetch all registered devices."""
        query = "{ devices { id } }"
        data = await self.async_graphql_request(query)
        return data.get("devices", [])

    async def async_get_device(self, device_id: str) -> Dict[str, Any]:
        """Fetch full device details and flatten properties."""
        query = """
        query GetDevice($id: UUID!) {
          device(id: $id) {
            id
            createTime
            updateTime
            properties {
              name
              value
            }
          }
        }
        """
        data = await self.async_graphql_request(query, {"id": device_id})
        device = data.get("device", {})
        if not device:
            raise SomatApiError(f"Device {device_id} not found")

        props: Dict[str, Any] = {}
        for p in device.get("properties", []):
            props[p["name"]] = p["value"]
        device["state"] = props
        return device

    async def async_get_activity(self) -> Dict[str, Any]:
        """Fetch activity and statistics."""
        query = """
        {
          activity {
            ... on SomatActivity {
              washCycleCount
              refillCount
              avgRatingPerWashCycle
              washCycles {
                id
                time
                duration
                status
                program
                initialDetergentFillLevelFloat
                finalDetergentFillLevelFloat
              }
            }
          }
        }
        """
        data = await self.async_graphql_request(query)
        return data.get("activity", {})

    async def async_update_device_property(
        self, device_id: str, name: str, value: Any
    ) -> Any:
        """Update a writable property on the device (e.g. program)."""
        mut = """
        mutation UpdateProp($deviceId: UUID!, $name: String!, $value: Any!) {
          updateDeviceProperty(deviceId: $deviceId, name: $name, value: $value) {
            property {
              name
              value
            }
          }
        }
        """
        data = await self.async_graphql_request(
            mut, {"deviceId": device_id, "name": name, "value": value}
        )
        return data.get("updateDeviceProperty", {})
