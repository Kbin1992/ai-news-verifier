# GenLayer AI News Verifier Contract
# Bradbury Testnet Compatible
# Deploy via: https://studio.genlayer.com

import json
import gl


class NewsVerifier(gl.Contract):
    """
    AI News Verifier - classifies headlines as REAL / FAKE / MISLEADING
    by fetching the source URL and using AI analysis.
    """

    verdicts: gl.TreeMap[str, str]        # headline -> verdict
    sources: gl.TreeMap[str, str]         # headline -> source_url
    timestamps: gl.TreeMap[str, int]      # headline -> block timestamp

    def __init__(self):
        self.verdicts = gl.TreeMap()
        self.sources = gl.TreeMap()
        self.timestamps = gl.TreeMap()

    # ------------------------------------------------------------------
    # INTERNAL: fetch + classify (runs inside nondet block)
    # ------------------------------------------------------------------

    def _classify(self, headline: str, source_url: str) -> str:
        """
        Fetch the page and ask the AI to classify the headline.
        Returns one of: REAL | FAKE | MISLEADING | UNVERIFIABLE
        """
        # Step 1 – fetch web content (trim to 2000 chars to keep prompt short)
        try:
            page_text = gl.nondet.web.render(source_url)
            snippet = page_text[:2000] if page_text else ""
        except Exception:
            snippet = ""

        if not snippet:
            return "UNVERIFIABLE"

        # Step 2 – short, focused AI prompt
        prompt = (
            "You are a fact-checking AI.\n"
            f"Headline: \"{headline}\"\n"
            f"Source snippet (first 2000 chars):\n{snippet}\n\n"
            "Based ONLY on the snippet above, classify the headline as exactly ONE of:\n"
            "REAL, FAKE, MISLEADING, or UNVERIFIABLE\n"
            "Respond with a JSON object and nothing else, e.g.: {\"verdict\": \"REAL\"}"
        )

        raw = gl.nondet.exec_prompt(prompt)

        # Step 3 – parse and normalise
        try:
            # Strip markdown fences if present
            clean = raw.strip().strip("```json").strip("```").strip()
            data = json.loads(clean)
            verdict = str(data.get("verdict", "UNVERIFIABLE")).upper()
        except Exception:
            # Fallback: look for a keyword in the raw text
            upper = raw.upper()
            for label in ("REAL", "FAKE", "MISLEADING"):
                if label in upper:
                    verdict = label
                    break
            else:
                verdict = "UNVERIFIABLE"

        allowed = {"REAL", "FAKE", "MISLEADING", "UNVERIFIABLE"}
        return verdict if verdict in allowed else "UNVERIFIABLE"

    # ------------------------------------------------------------------
    # PUBLIC WRITE
    # ------------------------------------------------------------------

    @gl.public.write
    def verify_headline(self, headline: str, source_url: str) -> str:
        """
        Fetch the source page, classify the headline with AI,
        reach validator consensus, and store the verdict on-chain.
        """
        if not headline or not source_url:
            return "ERROR: headline and source_url are required"

        # Equivalence principle – all validators must agree on the verdict
        verdict = gl.eq_principle_strict_eq(
            lambda: self._classify(headline, source_url)
        )

        # Persist on-chain
        self.verdicts[headline] = verdict
        self.sources[headline] = source_url
        self.timestamps[headline] = gl.block_number()

        return verdict

    # ------------------------------------------------------------------
    # PUBLIC VIEWS
    # ------------------------------------------------------------------

    @gl.public.view
    def get_verdict(self, headline: str) -> dict:
        """Return the stored verdict for a headline."""
        if headline not in self.verdicts:
            return {"error": "Headline not found. Call verify_headline first."}

        return {
            "headline": headline,
            "verdict": self.verdicts[headline],
            "source": self.sources[headline],
            "block": self.timestamps[headline],
        }

    @gl.public.view
    def get_all_headlines(self) -> list:
        """Return all headline keys stored in the contract."""
        return list(self.verdicts.keys())

    @gl.public.view
    def total_verified(self) -> int:
        """Return total number of headlines verified so far."""
        return len(list(self.verdicts.keys()))
