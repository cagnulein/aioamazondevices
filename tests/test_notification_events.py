# Copyright 2024 Simone Chemelli and contributors
# SPDX-License-Identifier: Apache-2.0

"""Tests for Alexa notification push-event handling."""

from collections.abc import Callable
from unittest.mock import AsyncMock

import pytest

from aioamazondevices.api import AmazonEchoApi
from aioamazondevices.structures import AmazonDevice, AmazonSchedule

SERIAL_1 = "SERIAL_1"
SERIAL_2 = "SERIAL_2"


@pytest.mark.anyio
async def test_notification_change_updates_only_target_device(
    api: AmazonEchoApi,
    make_device: Callable[..., AmazonDevice],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A notification push refreshes the device named by the event payload."""
    device_1 = make_device(SERIAL_1, capabilities=["TIMERS_AND_ALARMS"])
    device_2 = make_device(SERIAL_2, capabilities=["TIMERS_AND_ALARMS"])
    device_2.notifications = {
        "Timer": AmazonSchedule("Timer", "ON", "", None)
    }
    api._device_handler._final_devices = {SERIAL_1: device_1, SERIAL_2: device_2}

    notifications: dict[str, dict[str, AmazonSchedule]] = {
        SERIAL_1: {"Timer": AmazonSchedule("Timer", "ON", "", None)},
        SERIAL_2: {"Timer": AmazonSchedule("Timer", "ON", "", None)},
    }
    get_notifications = AsyncMock(return_value=notifications)
    monkeypatch.setattr(api._notification_handler, "get_notifications", get_notifications)

    received: list[dict[str, AmazonDevice]] = []

    async def on_notification(devices: dict[str, AmazonDevice]) -> None:
        received.append(devices)

    api.on_notification_event.append(on_notification)
    api.on_notification_event.freeze()

    await api._handle_notification_change_event(SERIAL_1)

    get_notifications.assert_awaited_once()
    assert device_1.notifications == notifications[SERIAL_1]
    assert device_2.notifications == {"Timer": AmazonSchedule("Timer", "ON", "", None)}
    assert received == [{SERIAL_1: device_1, SERIAL_2: device_2}]
