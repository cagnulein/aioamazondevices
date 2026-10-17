# Copyright 2024 Simone Chemelli and contributors
# SPDX-License-Identifier: Apache-2.0

"""Tests for Amazon MFA device selection."""

import pytest
from bs4 import BeautifulSoup

from aioamazondevices.exceptions import CannotAuthenticate
from aioamazondevices.login import AmazonLogin


def _login() -> AmazonLogin:
    """Build a login instance without creating an HTTP session."""
    return object.__new__(AmazonLogin)


def test_select_totp_mfa_device() -> None:
    """Select the authenticator-app option and preserve hidden fields."""
    soup = BeautifulSoup(
        """
        <form id="auth-select-device-form" method="post" action="/mfa">
          <input type="hidden" name="workflowState" value="state">
          <div data-a-input-name="otpDeviceContext" class="auth-SMS">
            <input type="radio" name="otpDeviceContext" value="sms, SMS">
          </div>
          <div data-a-input-name="otpDeviceContext" class="auth-TOTP">
            <input type="radio" name="otpDeviceContext" value="totp, TOTP">
          </div>
        </form>
        """,
        "html.parser",
    )

    assert _login()._select_totp_mfa_device(soup) == {
        "workflowState": "state",
        "otpDeviceContext": "totp, TOTP",
    }


def test_select_totp_mfa_device_fallback_value() -> None:
    """Select TOTP when Amazon omits the auth-TOTP CSS class."""
    soup = BeautifulSoup(
        """
        <form id="auth-select-device-form">
          <input type="hidden" name="workflowState" value="state">
          <input name="otpDeviceContext" value="totp, TOTP">
        </form>
        """,
        "html.parser",
    )

    assert _login()._select_totp_mfa_device(soup)["otpDeviceContext"] == (
        "totp, TOTP"
    )


def test_select_totp_mfa_device_requires_authenticator_option() -> None:
    """Fail clearly when the account has no authenticator-app option."""
    soup = BeautifulSoup(
        """
        <form id="auth-select-device-form">
          <input name="otpDeviceContext" value="sms, SMS">
        </form>
        """,
        "html.parser",
    )

    with pytest.raises(CannotAuthenticate, match="Authenticator app MFA method"):
        _login()._select_totp_mfa_device(soup)
