"""Singapore property listings from PropertyGuru — price, address, district, agent contact, 40+ fields per listing.

Thin wrapper around the Apify REST API (https://docs.apify.com/api/v2) for the
`rl1987/propertyguru-sg-api-scraper` Actor: https://apify.com/rl1987/propertyguru-sg-api-scraper

Requires an Apify API token — get one free at
https://console.apify.com/account/integrations

Typical usage:

    from apify_propertyguru_sg_client import PropertyGuruSGClient

    client = PropertyGuruSGClient(api_token="apify_api_...")
    items = client.run({"location": "Orchard", "listingType": "sale", "maxItems": 20})
    for item in items:
        print(item["url"])

See the package README for the full input schema and output field reference:
https://pypi.org/project/apify-propertyguru-sg-client/
"""
from __future__ import annotations

import time
from typing import Any

import requests

ACTOR_ID = "rl1987/propertyguru-sg-api-scraper"
"""The Apify Actor ID this client targets, as `owner/name`."""

_API_BASE = "https://api.apify.com/v2"


class ApifyActorError(RuntimeError):
	"""Raised when the underlying Apify Actor run fails, times out, or is aborted.

	This is distinct from `requests.HTTPError`, which signals a problem with the
	HTTP request to the Apify API itself (bad token, malformed input, rate
	limiting). `ApifyActorError` means the request succeeded and a run was
	started, but that *run* did not end in `SUCCEEDED` status.
	"""


class PropertyGuruSGClient:
	"""Client for the [PropertyGuru Singapore API Scraper](https://apify.com/rl1987/propertyguru-sg-api-scraper) Apify Actor.

	Singapore property listings from PropertyGuru — price, address, district, agent contact, 40+ fields per listing.

	Each call to `run()` starts a fresh Actor run, polls until it finishes, and
	returns the resulting dataset as a list of plain dicts. There is no
	persistent connection or background process — this is a thin, synchronous
	wrapper over three Apify REST endpoints (start run, poll run, fetch
	dataset items).

	Args:
	    api_token: Your Apify personal API token. Get one free at
	        https://console.apify.com/account/integrations. Required.
	    actor_id: Override the Actor ID to run. Defaults to the Actor this
	        package targets (rl1987/propertyguru-sg-api-scraper); you shouldn't normally need to change
	        this.
	    timeout_secs: How long to wait for a single `run()` call to finish
	        before raising `ApifyActorError`. Increase this for inputs with a
	        large `maxItems`. Defaults to 300 seconds.

	Example:
	    >>> client = PropertyGuruSGClient(api_token="apify_api_...")
	    >>> items = client.run({"location": "Orchard", "listingType": "sale", "maxItems": 20})
	    >>> len(items) > 0
	    True
	"""

	def __init__(self, api_token: str, *, actor_id: str = ACTOR_ID, timeout_secs: int = 300) -> None:
		if not api_token:
			raise ValueError("api_token is required (get one at https://console.apify.com/account/integrations)")
		self.api_token = api_token
		self.actor_id = actor_id
		self.timeout_secs = timeout_secs
		self._session = requests.Session()

	def run(self, actor_input: dict[str, Any] | None = None, *, poll_interval_secs: float = 1.5) -> list[dict[str, Any]]:
		"""Run the Actor with the given input and return the resulting dataset items.

		This starts a new Actor run, blocks while polling its status, and once
		it reaches a terminal state fetches and returns the full dataset.

		Args:
		    actor_input: Dict matching the Actor's input schema. See the
		        package README's "Input reference" section, or the **Input**
		        tab at https://apify.com/rl1987/propertyguru-sg-api-scraper for the authoritative
		        schema. Passing `None` runs the Actor with its default input.
		    poll_interval_secs: Seconds to wait between run-status checks.
		        Lower values notice completion sooner but make more API calls;
		        the default (1.5s) is a reasonable balance for most runs.

		Returns:
		    One dict per result row in the Actor's default dataset, in the
		    order Apify returns them. Field names/availability depend on the
		    input flags you passed (see README).

		Raises:
		    ValueError: `api_token` was empty (raised at construction, not here).
		    ApifyActorError: The run failed, timed out on the Apify side, was
		        aborted, or did not reach a terminal state within
		        `self.timeout_secs`.
		    requests.HTTPError: The HTTP request to the Apify API itself
		        failed — e.g. invalid token (401), bad input (400), or rate
		        limiting (429). Raised by `requests`' `raise_for_status()`.
		"""
		actor_input = actor_input or {}
		run = self._request(
			"POST",
			f"/acts/{self.actor_id.replace('/', '~')}/runs",
			params={"waitForFinish": 0},
			json=actor_input,
		)["data"]

		run_id = run["id"]
		deadline = time.monotonic() + self.timeout_secs
		while True:
			status_data = self._request("GET", f"/actor-runs/{run_id}")["data"]
			status = status_data["status"]
			if status in ("SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"):
				break
			if time.monotonic() > deadline:
				raise ApifyActorError(f"Run {run_id} did not finish within {self.timeout_secs}s (last status: {status})")
			time.sleep(poll_interval_secs)

		if status_data["status"] != "SUCCEEDED":
			raise ApifyActorError(f"Run {run_id} ended with status {status_data['status']}")

		dataset_id = status_data["defaultDatasetId"]
		items = self._request("GET", f"/datasets/{dataset_id}/items")
		return items if isinstance(items, list) else [items]

	def _request(self, method: str, path: str, **kwargs: Any) -> Any:
		"""Make an authenticated request to the Apify API and return the parsed JSON body.

		Internal helper — not part of the public API. Raises `requests.HTTPError`
		via `raise_for_status()` on any non-2xx response.
		"""
		params = kwargs.pop("params", {})
		params["token"] = self.api_token
		resp = self._session.request(method, f"{_API_BASE}{path}", params=params, timeout=60, **kwargs)
		resp.raise_for_status()
		return resp.json()
