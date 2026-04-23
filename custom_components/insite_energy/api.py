"""Insite Energy API client — extracts embedded viewModel JSON from the details page."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

import requests
from bs4 import BeautifulSoup

from .const import BASE_URL, DETAILS_URL, LOGIN_URL

_LOGGER = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}


class InsiteEnergyError(Exception):
    """General Insite Energy error."""


class InsiteEnergyAuthError(InsiteEnergyError):
    """Authentication error."""


class InsiteEnergyAPI:
    """Scrape-based API client for Insite Energy."""

    def __init__(self, email: str, password: str) -> None:
        self._email = email
        self._password = password
        self._session: requests.Session | None = None

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = self._login()
        return self._session

    def _login(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(HEADERS)

        _LOGGER.debug("Fetching login page for CSRF token")
        try:
            resp = session.get(LOGIN_URL, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as err:
            raise InsiteEnergyError(f"Could not reach login page: {err}") from err

        soup = BeautifulSoup(resp.text, "html.parser")
        token_input = soup.find("input", {"name": "__RequestVerificationToken"})
        if not token_input:
            raise InsiteEnergyError("Could not find CSRF token on login page")
        token = token_input.get("value", "")

        # Field names on the form are lowercase: email / password
        payload = {
            "email": self._email,
            "password": self._password,
            "__RequestVerificationToken": token,
        }
        _LOGGER.debug("Posting login credentials for %s", self._email)
        try:
            resp = session.post(LOGIN_URL, data=payload, timeout=20, allow_redirects=True)
            resp.raise_for_status()
        except requests.RequestException as err:
            raise InsiteEnergyError(f"Login request failed: {err}") from err

        if "/Account/Login" in resp.url or "Log in to your account" in resp.text:
            raise InsiteEnergyAuthError("Login failed — check your email and password")

        _LOGGER.debug("Login successful, landed on: %s", resp.url)
        return session

    def fetch_data(self) -> dict[str, Any]:
        session = self._get_session()

        try:
            resp = session.get(DETAILS_URL, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as err:
            self._session = None
            raise InsiteEnergyError(f"Failed to fetch details page: {err}") from err

        if "/Account/Login" in resp.url:
            _LOGGER.debug("Session expired, re-authenticating")
            self._session = None
            session = self._get_session()
            try:
                resp = session.get(DETAILS_URL, timeout=20)
                resp.raise_for_status()
            except requests.RequestException as err:
                raise InsiteEnergyError(f"Failed after re-auth: {err}") from err

        return self._parse(resp.text)

    def _parse(self, html: str) -> dict[str, Any]:
        """Extract the embedded viewModel JSON from the page script tag.
        
        The page inlines: var viewModel = {...}; var isDDAlreadySetup = ...
        This is much more reliable than scraping HTML elements.
        """
        match = re.search(
            r"var\s+viewModel\s*=\s*(\{.*?\});\s*var\s+isDDAlreadySetup",
            html,
            re.DOTALL,
        )
        if not match:
            raise InsiteEnergyError(
                "Could not find viewModel in page — the site may have changed"
            )

        try:
            vm = json.loads(match.group(1))
        except json.JSONDecodeError as err:
            raise InsiteEnergyError(f"Failed to parse viewModel JSON: {err}") from err

        # Use UtilityDetail (single selected utility) or first in UtilityDetails list
        detail = vm.get("UtilityDetail") or {}
        if not detail and vm.get("UtilityDetails"):
            detail = vm["UtilityDetails"][0]

        data: dict[str, Any] = {}

        def _float(val) -> float | None:
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        # Active balance (credit remaining) — e.g. "46.95"
        if (v := _float(detail.get("ActiveBalance"))) is not None:
            data["active_balance"] = v

        # Debt balance — e.g. "0.0000"
        if (v := _float(detail.get("DebtBalance"))) is not None:
            data["debt_balance"] = v

        # Debt recovery rate — e.g. "20.00"
        if (v := _float(detail.get("DebtRatio"))) is not None:
            data["debt_recovery_rate"] = v

        # Unit rate in pence — e.g. "17.76p" -> 17.76
        if m := re.search(r"([\d.]+)", detail.get("Rates", "")):
            if (v := _float(m.group(1))) is not None:
                data["unit_rate_pence"] = v

        # Standing charge in pence — e.g. "94.09p" -> 94.09
        if m := re.search(r"([\d.]+)", detail.get("StandingChargeValue", "")):
            if (v := _float(m.group(1))) is not None:
                data["standing_charge_pence"] = v

        # Last meter reading date string — e.g. "23/04/2026 17:26"
        if reading_date := detail.get("MeterReadingDate"):
            data["last_meter_reading_date"] = reading_date

        # Meter comms status
        data["meter_out_of_comms"] = bool(detail.get("IsMeterOutOfCommas", False))

        # Account metadata
        data["account_number"] = detail.get("AccountNumber")
        data["utility_name"] = detail.get("Name", "Heating & Hot Water")

        _LOGGER.debug("Extracted Insite Energy data: %s", data)
        return data
