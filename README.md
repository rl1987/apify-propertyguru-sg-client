# apify-propertyguru-sg-client

**Singapore property listings from PropertyGuru — price, address, district, agent contact, 40+ fields per listing.**

Python client for the [`rl1987/propertyguru-sg-api-scraper`](https://apify.com/rl1987/propertyguru-sg-api-scraper) [Apify](https://apify.com) Actor. No local scraping, no proxy management, no anti-bot maintenance — the Actor runs on Apify's infrastructure and this package just starts it, waits, and hands you back the dataset as plain Python dicts.

[Install](#install) · [Quickstart](#quickstart) · [Getting an API token](#getting-an-api-token) · [Input reference](#input-reference) · [Output fields](#output-fields) · [Error handling](#error-handling) · [Pricing](#pricing) · [Async / long-running runs](#advanced-longer-timeouts--polling) · [Links](#links)

## Install

```bash
pip install apify-propertyguru-sg-client
```

Requires Python 3.9+. Only dependency is [`requests`](https://pypi.org/project/requests/).

## Quickstart

```python
from apify_propertyguru_sg_client import PropertyGuruSGClient

client = PropertyGuruSGClient(api_token="apify_api_...")  # see "Getting an API token" below
items = client.run({"location": "Orchard", "listingType": "sale", "maxItems": 20})

for item in items:
    print(item)
```

Real output from the example above (trimmed to a few fields):

```python
{"title": "Well maintained unit", "price": 7999000, "district": "Orchard / River Valley", "listingUrl": "https://www.propertyguru.com.sg/listing/for-sale-orchard-view-60186981"}
```

`run()` blocks until the Actor finishes (usually a few seconds to ~30s depending on `maxItems`) and returns a plain `list[dict]` — the Actor's dataset, one dict per result row.

## Getting an API token

1. Sign up for a free account at [console.apify.com](https://console.apify.com).
2. Go to **Settings → Integrations** and copy your **Personal API token**.
3. Pass it to the client: `PropertyGuruSGClient(api_token="...")`, or read it from an environment variable:

   ```python
   import os
   client = PropertyGuruSGClient(api_token=os.environ["APIFY_TOKEN"])
   ```

Never hardcode the token in source control — use an environment variable or secrets manager.

## Input reference

`run()` takes a single `dict` matching the Actor's input schema. Full/authoritative schema: the **Input** tab on [the Actor's Apify page](https://apify.com/rl1987/propertyguru-sg-api-scraper).

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `location` | str | — | Area/neighbourhood name, e.g. `"Orchard"`. Ignored when `districtCode` is set. |
| `districtCode` | str | — | Precise district, e.g. `"D09"`. Overrides `location`. |
| `listingType` | str | `"sale"` | `"sale"` or `"rent"`. |
| `propertyType` | str | — | e.g. `"hdb"`, `"condo"`, `"apartment"`, `"terrace"`, `"semi-detached"`, `"landed"`. |
| `minPrice` / `maxPrice` | int | — | Price range in SGD. |
| `bedrooms` | int | — | Exact bedroom count. |
| `maxItems` | int | `100` | `0` = unlimited. |
| `includeDetails` | bool | `False` | Fetch all photos, videos, floor plans, full agent contact per listing. |

## Output fields

Each dict in the returned list is one row from the Actor's dataset. Common fields:

`title`, `price`, `pricePretty`, `address`, `district`, `beds`, `baths`, `floorArea`, `propertyType`, `tenure`, `agentName`, `agentMobile`, `agencyName`, `listingUrl`, `images`, `postedDate`.

Exact field availability can vary by input flags (see table above) — treat unfamiliar/missing keys as optional and use `.get()` rather than `[...]` indexing.

## Error handling

```python
from apify_propertyguru_sg_client import PropertyGuruSGClient, ApifyActorError
import requests

client = PropertyGuruSGClient(api_token="...")

try:
    items = client.run({"location": "Orchard", "listingType": "sale", "maxItems": 20})
except ApifyActorError as e:
    # The Actor run itself failed, timed out, or was aborted on the Apify side.
    print(f"Actor run did not succeed: {e}")
except requests.HTTPError as e:
    # Bad token, malformed input, rate limiting, etc. — an HTTP-level error
    # calling the Apify API (not the Actor run).
    print(f"Apify API request failed: {e}")
```

`ApifyActorError` is raised when the run reaches a terminal non-success status (`FAILED`, `TIMED-OUT`, `ABORTED`) or doesn't finish within `timeout_secs` (default 300s — raise it for `run()` calls with a large `maxItems`, e.g. `PropertyGuruSGClient(api_token="...", timeout_secs=900)`).

## Pricing

The current price of every event is on the **Pricing** tab of this Actor's page in Apify Store. That tab is generated from the Actor's own pricing record, so it is always current, and your plan's rung is applied automatically. A figure repeated here would be a second copy that drifts out of date.

You can cap what any single run may spend with **Max total charge**.

## Advanced: longer timeouts & polling

```python
client = PropertyGuruSGClient(api_token="...", timeout_secs=900)  # allow up to 15 min
items = client.run(actor_input, poll_interval_secs=3.0)   # poll less aggressively
```

## Links

- [PropertyGuru Singapore API Scraper on Apify](https://apify.com/rl1987/propertyguru-sg-api-scraper) — Actor page, input schema, pricing
- [PyPI package](https://pypi.org/project/apify-propertyguru-sg-client/)
- [Apify API reference](https://docs.apify.com/api/v2) — what this client wraps under the hood

## License

MIT
