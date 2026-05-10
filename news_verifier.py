# { "Depends": "py-genlayer:test" }
from genlayer import *
import json
import typing


class NewsVerifier(gl.Contract):
    """
    AI News Verifier - GenLayer Intelligent Contract
    Verifies news headlines against their source URLs using AI + live web fetching.
    Verdicts are stored permanently on-chain.
    """

    verifications: TreeMap[str, str]  # stores headline -> result JSON

    def __init__(self):
        self.verifications = {}

    @gl.public.write
    def verify_headline(self, headline: str, source_url: str) -> None:
        """
        Submit a news headline and source URL for verification.
        The AI fetches the actual page and determines if the headline is
        REAL, FAKE, or MISLEADING, then stores the verdict on-chain.
        """

        def check_headline() -> str:
            # Fetch the live web page content
            web_data = gl.get_webpage(source_url, mode="text")

            prompt = f"""You are an expert news fact-checker and investigative journalist.

HEADLINE TO VERIFY: "{headline}"

SOURCE PAGE CONTENT (first 4000 chars):
{web_data[:4000]}

SOURCE URL: {source_url}

Carefully analyze whether the headline is:
- REAL: The headline accurately reflects what the source article actually says
- FAKE: The headline is not supported by the source, contradicts it, or the source doesn't mention this at all
- MISLEADING: The headline is technically connected to the source but exaggerates, distorts, cherry-picks, or takes content out of context

Return ONLY valid JSON in this exact format, nothing else:
{{"verdict": "REAL", "confidence": "HIGH", "reason": "Brief one-sentence explanation of your finding"}}

Possible verdict values: REAL, FAKE, MISLEADING
Possible confidence values: HIGH, MEDIUM, LOW"""

            result = gl.exec_prompt(prompt)

            # Normalize and re-serialize so validators can compare consistently
            try:
                parsed = json.loads(result.strip())
                return json.dumps({
                    "verdict": parsed.get("verdict", "FAKE").upper(),
                    "confidence": parsed.get("confidence", "LOW").upper(),
                    "reason": parsed.get("reason", "Could not determine"),
                }, sort_keys=True)
            except Exception:
                return json.dumps({
                    "verdict": "FAKE",
                    "confidence": "LOW",
                    "reason": "Could not parse source content"
                }, sort_keys=True)

        # Use comparative equivalence — validators must agree on the verdict
        result_json = gl.eq_principle_prompt_comparative(
            check_headline,
            principle="The verdict field (REAL, FAKE, or MISLEADING) must match exactly. Minor differences in the reason wording are acceptable."
        )

        # Store on-chain: key is headline truncated to 120 chars
        key = headline[:120]
        self.verifications[key] = json.dumps({
            "headline": headline,
            "source_url": source_url,
            "result": json.loads(result_json),
        }, sort_keys=True)

    @gl.public.view
    def get_verdict(self, headline: str) -> str:
        """Returns the stored verdict JSON for a given headline, or 'NOT_VERIFIED'."""
        key = headline[:120]
        return self.verifications.get(key, "NOT_VERIFIED")

    @gl.public.view
    def get_all_verifications(self) -> dict:
        """Returns all stored verifications as a dict."""
        return dict(self.verifications)

    @gl.public.view
    def get_verification_count(self) -> int:
        """Returns the total number of verifications stored on-chain."""
        return len(self.verifications)
