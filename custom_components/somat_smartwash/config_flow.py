"""Config flow for Somat Smartwash integration."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SomatAuthError, SomatConnectionError, SomatSmartwashApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class SomatSmartwashConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Somat Smartwash."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._reauth_entry: Optional[config_entries.ConfigEntry] = None

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial user step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip().lower()
            password = user_input[CONF_PASSWORD]

            session = async_get_clientsession(self.hass)
            client = SomatSmartwashApiClient(email, password, session)

            try:
                await client.async_login()
                user_info = await client.async_get_user()
                user_id = user_info.get("id") or email

                await self.async_set_unique_id(user_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Somat Smartwash ({email})",
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                    },
                )

            except SomatAuthError:
                errors["base"] = "invalid_auth"
            except SomatConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during config flow: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Dict[str, Any]
    ) -> FlowResult:
        """Handle reauth when credentials expire."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Dialog that informs the user that reauth is required."""
        errors: Dict[str, str] = {}
        assert self._reauth_entry is not None

        if user_input is not None:
            email = self._reauth_entry.data[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            session = async_get_clientsession(self.hass)
            client = SomatSmartwashApiClient(email, password, session)

            try:
                await client.async_login()
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                    },
                )
                await self.hass.config_entries.async_reload(
                    self._reauth_entry.entry_id
                )
                return self.async_abort(reason="reauth_successful")

            except SomatAuthError:
                errors["base"] = "invalid_auth"
            except SomatConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
            description_placeholders={
                CONF_EMAIL: self._reauth_entry.data[CONF_EMAIL]
            },
        )
