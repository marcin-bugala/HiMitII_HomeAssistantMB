"""PR #1 regression coverage. All API operations are mocked."""
import asyncio
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.himit import _async_update_listener, async_setup_entry, async_unload_entry
from custom_components.himit.api import HimitAPIError, HimitAuthError
from custom_components.himit.coordinator import HimitCoordinator


TOKENS = {"access_token": "new-access", "refresh_token": "new-refresh",
          "token_created_ms": 123456, "token_expire_secs": 7200}


def make_coordinator():
    entry = SimpleNamespace(entry_id="test-entry", options={"scan_interval": 60}, data={
        "username": "test@example.invalid", "password": "test-password",
        "home_id": "test-home", "access_token": "old-access", "refresh_token": "old-refresh",
        "token_created_ms": int(time.time() * 1000), "token_expire_secs": 7200,
        "refresh_expire_secs": 2592000,
    })
    hass = SimpleNamespace(config_entries=SimpleNamespace(
        async_update_entry=Mock(), async_reload=AsyncMock()))
    api = SimpleNamespace(refresh_token=AsyncMock(return_value=TOKENS),
                          login=AsyncMock(return_value=TOKENS),
                          get_device_property=AsyncMock(return_value=[]))
    coord = HimitCoordinator(hass, api, entry)
    coord.atw_devices = [{"wifiId": "wifi-test", "deviceId": "device-test"}]
    hass.data = {"himit": {entry.entry_id: coord}}
    return coord, hass, entry


def test_token_refresh_persists_without_reload_and_options_reload():
    async def run():
        coord, hass, entry = make_coordinator()
        coord._token_data["token_created_ms"] = int((time.time() - 7100) * 1000)
        await coord._ensure_token()
        coord.api.refresh_token.assert_awaited_once_with("old-refresh")
        coord.api.login.assert_not_awaited()
        assert coord.access_token == "new-access"
        assert coord.loaded_options == {"scan_interval": 60}
        saved = hass.config_entries.async_update_entry.call_args.kwargs["data"]
        assert saved["access_token"] == "new-access"
        entry.data = saved
        await _async_update_listener(hass, entry)
        hass.config_entries.async_reload.assert_not_awaited()
        entry.options["scan_interval"] = 90
        assert coord.loaded_options == {"scan_interval": 60}
        await _async_update_listener(hass, entry)
        hass.config_entries.async_reload.assert_awaited_once_with(entry.entry_id)
    asyncio.run(run())


@pytest.mark.parametrize("error", [HimitAuthError("invalid refresh"), HimitAPIError("Server error 1: invalid token")])
def test_refresh_failure_falls_back_to_login(error):
    async def run():
        coord, _, _ = make_coordinator()
        coord._token_is_expiring = lambda: True
        coord.api.refresh_token.side_effect = error
        await coord._ensure_token()
        coord.api.login.assert_awaited_once_with("test@example.invalid", "test-password")
        assert coord.access_token == "new-access"
    asyncio.run(run())


@pytest.mark.parametrize("error", [aiohttp.ClientConnectionError("offline"), asyncio.TimeoutError()])
def test_refresh_network_failure_does_not_reauthenticate(error):
    async def run():
        coord, _, _ = make_coordinator()
        coord._token_is_expiring = lambda: True
        coord.api.refresh_token.side_effect = error
        with pytest.raises(UpdateFailed):
            await coord._ensure_token()
        coord.api.login.assert_not_awaited()
    asyncio.run(run())


@pytest.mark.parametrize("error,expected", [
    (HimitAuthError("bad credentials"), ConfigEntryAuthFailed),
    (HimitAPIError("cloud unavailable"), UpdateFailed),
    (aiohttp.ClientConnectionError("offline"), UpdateFailed),
    (asyncio.TimeoutError(), UpdateFailed),
])
def test_login_error_classification(error, expected):
    async def run():
        coord, _, _ = make_coordinator()
        coord.api.login.side_effect = error
        with pytest.raises(expected):
            await coord._try_relogin()
    asyncio.run(run())


def test_missing_credentials_requires_reauth():
    async def run():
        coord, _, entry = make_coordinator()
        entry.data.pop("password")
        with pytest.raises(ConfigEntryAuthFailed):
            await coord._try_relogin()
        coord.api.login.assert_not_awaited()
    asyncio.run(run())


def test_normal_poll_reads_once():
    async def run():
        coord, _, _ = make_coordinator()
        assert await coord._async_update_data() == {}
        coord.api.get_device_property.assert_awaited_once()
        coord.api.login.assert_not_awaited()
    asyncio.run(run())


def http_error(status):
    return aiohttp.ClientResponseError(SimpleNamespace(real_url="https://example.invalid"), (), status=status)


@pytest.mark.parametrize("error", [HimitAuthError("rejected"), http_error(401), http_error(403)])
def test_rejected_token_relogs_and_retries_once(error):
    async def run():
        coord, _, _ = make_coordinator()
        coord.api.get_device_property.side_effect = [error, [{"deviceId": "device-test", "status": {"fixedDid18": "38"}}]]
        result = await coord._async_update_data()
        assert result["device-test"]["fixedDid18"] == 38.0
        assert coord.api.get_device_property.await_count == 2
        coord.api.login.assert_awaited_once()
        assert coord.api.get_device_property.call_args.args[0] == "new-access"
    asyncio.run(run())


@pytest.mark.parametrize("error,expected", [
    (HimitAuthError("still rejected"), ConfigEntryAuthFailed),
    (http_error(401), ConfigEntryAuthFailed), (http_error(403), ConfigEntryAuthFailed),
    (http_error(503), UpdateFailed), (HimitAPIError("cloud error"), UpdateFailed),
    (asyncio.TimeoutError(), UpdateFailed),
])
def test_retry_failure_is_bounded(error, expected):
    async def run():
        coord, _, _ = make_coordinator()
        coord.api.get_device_property.side_effect = [HimitAuthError("revoked"), error]
        with pytest.raises(expected):
            await coord._async_update_data()
        assert coord.api.get_device_property.await_count == 2
        coord.api.login.assert_awaited_once()
    asyncio.run(run())


@pytest.mark.parametrize("error", [http_error(503), aiohttp.ClientConnectionError("offline"), asyncio.TimeoutError(), HimitAPIError("server error")])
def test_poll_network_or_server_error_never_logs_in(error):
    async def run():
        coord, _, _ = make_coordinator()
        coord.api.get_device_property.side_effect = error
        with pytest.raises(UpdateFailed):
            await coord._async_update_data()
        coord.api.login.assert_not_awaited()
        coord.api.get_device_property.assert_awaited_once()
    asyncio.run(run())


def test_setup_unload_and_listener_registration():
    async def run():
        coord, hass, entry = make_coordinator()
        coord.async_config_entry_first_refresh = AsyncMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock()
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        entry.add_update_listener = Mock(return_value="listener-unsubscribe")
        entry.async_on_unload = Mock()
        with patch("custom_components.himit.async_get_clientsession", return_value=object()), patch("custom_components.himit.HimitAPI"), patch("custom_components.himit.HimitCoordinator", return_value=coord):
            assert await async_setup_entry(hass, entry)
        coord.async_config_entry_first_refresh.assert_awaited_once()
        entry.add_update_listener.assert_called_once_with(_async_update_listener)
        entry.async_on_unload.assert_called_once_with("listener-unsubscribe")
        assert await async_unload_entry(hass, entry)
        assert entry.entry_id not in hass.data["himit"]
    asyncio.run(run())
