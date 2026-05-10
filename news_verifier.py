# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
# ─────────────────────────────────────────────────────────────
#  AI NEWS VERIFIER — GenLayer Intelligent Contract
#  Tested against: studio.genlayer.com (Bradbury Testnet)
#
#  API used (from official docs):
#    gl.nondet.web.get(url).body.decode("utf-8")  ← web fetch
#    gl.nondet.exec_prompt(prompt)                ← LLM call
#    gl.vm.run_nondet_unsafe(leader, validator)   ← consensus
#    gl.vm.Return                                 ← result type check
#
#  Verdict labels: REAL | FAKE | MISLEADING | UNVERIFIABLE
# ─────────────────────────────────────────────────────────────

import json
from genlayer import *


class NewsVerifier(gl.Contract):

    # ── on-chain storage ──────────────────────────────────────
    # Plain dict is supported for string→string maps in GenVM
    verdicts:  dict   # headline → verdict string
    sources:   dict   # headline → source url
    reasons:   dict   # headline → one-sentence reason

    def __init__(self):
        self.verdicts = {}
        self.sources  = {}
        self.reasons  = {}

    # ─────────────────────────────────────────────────────────
    #  WRITE — submit a headline + source URL for verification
    # ─────────────────────────────────────────────────────────
    @gl.public.write
    def verify_headline(self, headline: str, source_url: str) -> None:
        """
        Fetches the source page, calls an LLM to classify the headline,
        and stores the consensus verdict on-chain.

        Validators independently repeat the work and compare only the
        'verdict' field (LLM reasoning text will differ — that's fine).
        """

        # ── LEADER: runs on the proposing validator ───────────
        def leader_fn() -> str:
            # 1. Fetch live page as plain text
            try:
                page_bytes = gl.nondet.web.get(source_url).body
                page_text  = page_bytes.decode("utf-8", errors="replace")
            except Exception:
                # If page is unreachable, return UNVERIFIABLE
                return json.dumps({
                    "verdict": "UNVERIFIABLE",
                    "reason":  "Could not fetch source URL."
                }, sort_keys=True)

            snippet = page_text[:3000]   # keep prompt concise

            if not snippet.strip():
                return json.dumps({
                    "verdict": "UNVERIFIABLE",
                    "reason":  "Source page returned empty content."
                }, sort_keys=True)

            # 2. Ask LLM to classify the headline
            prompt = (
                "You are an expert fact-checker.\n\n"
                "HEADLINE: \"" + headline + "\"\n\n"
                "SOURCE PAGE (first 3000 chars):\n"
                + snippet + "\n\n"
                "Based ONLY on the source page above, classify the headline as:\n"
                "  REAL        — headline accurately reflects the source\n"
                "  FAKE        — headline contradicts or is absent from the source\n"
                "  MISLEADING  — source is related but headline exaggerates or distorts it\n"
                "  UNVERIFIABLE— source has no relevant content to judge the headline\n\n"
                "Return ONLY valid JSON, nothing else:\n"
                "{\"verdict\": \"REAL\", \"reason\": \"one short sentence\"}"
            )

            raw = gl.nondet.exec_prompt(prompt)

            # 3. Parse and normalise
            try:
                # exec_prompt returns a string; strip markdown fences if any
                clean = raw.strip().strip("```json").strip("```").strip()
                data  = json.loads(clean)

                verdict = str(data.get("verdict", "UNVERIFIABLE")).upper().strip()
                reason  = str(data.get("reason",  "No reason provided."))

                allowed = {"REAL", "FAKE", "MISLEADING", "UNVERIFIABLE"}
                if verdict not in allowed:
                    verdict = "UNVERIFIABLE"

                return json.dumps({
                    "verdict": verdict,
                    "reason":  reason
                }, sort_keys=True)

            except Exception:
                # Fallback: scan raw string for a verdict keyword
                upper = raw.upper()
                verdict = "UNVERIFIABLE"
                for label in ("REAL", "FAKE", "MISLEADING"):
                    if label in upper:
                        verdict = label
                        break
                return json.dumps({
                    "verdict": verdict,
                    "reason":  "Parsed from raw LLM output."
                }, sort_keys=True)

        # ── VALIDATOR: re-runs leader independently ───────────
        # Only the 'verdict' field must agree — reasoning text will differ
        # across different LLMs, so we never compare it.
        def validator_fn(leader_result) -> bool:
            # Reject if leader itself errored
            if not isinstance(leader_result, gl.vm.Return):
                return False

            # Re-run leader logic on this validator's node
            try:
                validator_raw = leader_fn()
                leader_raw    = leader_result.calldata

                leader_verdict    = json.loads(leader_raw).get("verdict", "")
                validator_verdict = json.loads(validator_raw).get("verdict", "")

                # Verdicts must match exactly; reasoning may differ
                return leader_verdict == validator_verdict

            except Exception:
                return False

        # ── CONSENSUS: run across all validator nodes ─────────
        result_json = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        # ── STORE on-chain ─────────────────────────────────────
        try:
            parsed  = json.loads(result_json)
            verdict = parsed.get("verdict", "UNVERIFIABLE")
            reason  = parsed.get("reason",  "")
        except Exception:
            verdict = "UNVERIFIABLE"
            reason  = "Could not parse result."

        key = headline[:200]        # cap key length
        self.verdicts[key] = verdict
        self.sources[key]  = source_url
        self.reasons[key]  = reason

    # ─────────────────────────────────────────────────────────
    #  VIEWS — read stored data (no gas cost)
    # ─────────────────────────────────────────────────────────

    @gl.public.view
    def get_verdict(self, headline: str) -> str:
        """Returns verdict for a headline, or NOT_FOUND."""
        return self.verdicts.get(headline[:200], "NOT_FOUND")

    @gl.public.view
    def get_reason(self, headline: str) -> str:
        """Returns the stored reason for a verdict."""
        return self.reasons.get(headline[:200], "NOT_FOUND")

    @gl.public.view
    def get_full_result(self, headline: str) -> str:
        """Returns verdict + reason + source as JSON string."""
        key = headline[:200]
        if key not in self.verdicts:
            return "{\"error\": \"NOT_FOUND\"}"
        return json.dumps({
            "verdict":    self.verdicts[key],
            "reason":     self.reasons.get(key, ""),
            "source_url": self.sources.get(key, ""),
            "headline":   headline
        }, sort_keys=True)

    @gl.public.view
    def get_all_headlines(self) -> list:
        """Returns list of all verified headlines."""
        return list(self.verdicts.keys())

    @gl.public.view
    def total_verified(self) -> int:
        """Returns count of all verified headlines."""
        return len(self.verdicts)
