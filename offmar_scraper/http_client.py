import random
import time
from typing import Dict, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class HttpClient:
	def __init__(
		self,
		user_agent: str,
		request_delay_seconds_min: float = 0.8,
		request_delay_seconds_max: float = 1.6,
		request_timeout_seconds: float = 20.0,
		extra_headers: Optional[Dict[str, str]] = None,
	) -> None:
		self.session = requests.Session()
		self.user_agent = user_agent
		self.request_delay_seconds_min = request_delay_seconds_min
		self.request_delay_seconds_max = request_delay_seconds_max
		self.request_timeout_seconds = request_timeout_seconds
		self.extra_headers = extra_headers or {}

	def _headers(self) -> Dict[str, str]:
		headers = {
			"User-Agent": self.user_agent,
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
			"Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
		}
		headers.update(self.extra_headers)
		return headers

	@retry(
		retry=retry_if_exception_type((requests.RequestException,)),
		wait=wait_exponential(multiplier=1.0, min=1, max=10),
		stop=stop_after_attempt(5),
		reraise=True,
	)
	def get(self, url: str) -> requests.Response:
		# polite delay
		delay = random.uniform(self.request_delay_seconds_min, self.request_delay_seconds_max)
		time.sleep(delay)
		response = self.session.get(url, headers=self._headers(), timeout=self.request_timeout_seconds)
		response.raise_for_status()
		return response