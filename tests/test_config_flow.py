"""Tests for the config flow."""
from unittest import mock
from unittest.mock import AsyncMock, patch

#from gidgethub import BadRequest
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_NAME, CONF_PATH
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.valetudo_vacuum_camera import config_flow
from custom_components.valetudo_vacuum_camera.const import DOMAIN, CONF_VACUUM_ENTITY_ID, \
    CONF_MQTT_USER, \
    CONF_MQTT_PASS, CONF_VACUUM_CONNECTION_STRING


@pytest.mark.asyncio
async def test_flow_user_init(hass):
    """Test the initialization of the form in the first step of the config flow."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": "user"}
    )
    expected ={
        "data_schema": config_flow.AUTH_SCHEMA,
        "description_placeholders": None,
        "errors": {},
        "flow_id": mock.ANY,
        "handler": "valedudo_vacuum_camera",
        "last_step": None,
        "step_id": "user",
        "type": "form",
    }
    assert expected == result


@pytest.mark.asyncio
async def test_flow_user_init_form(hass):
    """Test the initialization of the form in the second step of the config flow."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": "user"}
    )
    expected = {
        "data_schema": config_flow.AUTH_SCHEMA,
        "description_placeholders": None,
        "errors": {},
        "flow_id": mock.ANY,
        "handler": "github_custom",
        "step_id": "repo",
        "last_step": None,
        "type": "form",
    }
    assert expected == result


@pytest.mark.asyncio
@patch("custom_components.valetudo_vacuum_camera.config_flow.GitHubAPI")
async def test_flow_user_creates_config_entry(m_github, hass):
    """Test the config entry is successfully created."""
    m_instance = AsyncMock()
    m_instance.getitem = AsyncMock()
    m_github.return_value = m_instance
    config_flow.ValetudoCameraFlowHandler.data = {
        "name": user_input.get(CONF_NAME),
        "vacuum_entity": user_input.get(CONF_VACUUM_ENTITY_ID),
        "broker_user": user_input.get(CONF_MQTT_USER),
        "broker_password": user_input.get(CONF_MQTT_PASS),
        "vacuum_map": user_input.get(CONF_VACUUM_CONNECTION_STRING)
    }
    with patch("custom_components.github_custom.async_setup_entry", return_value=True):
        _result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN, context={"source": "repo"}
        )
        await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(
        _result["flow_id"],
        user_input={CONF_PATH: "home-assistant/core"},
    )
    expected = {
        "context": {"source": "repo"},
        "version": 1,
        "type": "create_entry",
        "flow_id": mock.ANY,
        "handler": "github_custom",
        "title": "GitHub Custom",
        "data": {
            "access_token": "token",
            "repositories": [
                {"path": "home-assistant/core", "name": "home-assistant/core"}
            ],
        },
        "description": None,
        "description_placeholders": None,
        "options": {},
        "result": mock.ANY,
    }
    assert expected == result
