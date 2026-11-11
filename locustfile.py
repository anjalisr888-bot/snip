import uuid

from locust import HttpUser, task, between


class RedirectUser(HttpUser):
    wait_time = between(0, 0.1)

    def on_start(self):
        alias = "b" + uuid.uuid4().hex[:10]
        r = self.client.post(
            "/shorten",
            json={"url": "https://www.wikipedia.org", "alias": alias},
      )
        self.code = alias if r.status_code == 200 else None

    @task
    def hit_redirect(self):
        if self.code:
            self.client.get(f"/{self.code}", allow_redirects=False, name="/[code]")