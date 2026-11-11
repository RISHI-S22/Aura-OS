from urllib.parse import urlparse

class SourceVerifier:
    TRUSTED_DOMAINS = {"github.com", "arxiv.org", "python.org", "wikipedia.org"}

    def verify_url(self, url: str) -> bool:
        try:
            domain = urlparse(url).netloc.lower()
            return any(trusted in domain for trusted in self.TRUSTED_DOMAINS)
        except Exception:
            return False