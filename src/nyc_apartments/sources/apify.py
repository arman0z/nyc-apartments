from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nyc_apartments.config import SourceConfig


@dataclass(slots=True)
class ApifySource:
    config: SourceConfig
    token: str

    def fetch(self) -> list[dict[str, Any]]:
        if not self.config.actor_id:
            raise ValueError(f"Source {self.config.name} is missing actor_id")
        if not self.token:
            raise RuntimeError("APIFY_API_TOKEN is required for live Apify runs")

        try:
            from apify_client import ApifyClient
        except ImportError as exc:
            raise RuntimeError(
                "Install live dependencies first: python3 -m pip install -e '.[live]'"
            ) from exc

        client = ApifyClient(self.token)
        run = client.actor(self.config.actor_id).call(
            run_input=self.config.input,
            timeout_secs=self.config.timeout_seconds,
        )
        status = run.get("status")
        if status != "SUCCEEDED":
            raise RuntimeError(f"Apify actor ended with status {status}")
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            return []

        items = list(client.dataset(dataset_id).iterate_items())
        if self.config.max_items is not None:
            return items[: self.config.max_items]
        return items
