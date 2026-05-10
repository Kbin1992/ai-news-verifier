# { "Depends": "py-genlayer:test" }
# ============================================================
#  AI NEWS VERIFIER — GenLayer Intelligent Contract
#  Bradbury Testnet  |  studio.genlayer.com
#
#  Classifies a news headline as:
#    REAL / FAKE / MISLEADING / UNVERIFIABLE
#
#  HOW IT WORKS:
#    1. Fetch source URL via gl.nondet.web.render()
#    2. Call AI via gl.nondet.exec_prompt()
#    3. Reach validator consensus via gl.vm.run_nondet_unsafe()
#    4. Store result on-chain in TreeMap
# ============================================================

import json
from genlayer import *


class NewsVerifier(gl.Contract):

    # ── Fully-typed storage (plain dict / int NOT allowed in GenVM) ──
    verdicts: TreeMap[str, str]   # headline → verdict
    sources:  TreeMap[str, str]   # headline → source_url

    def __init__(self):
        self.verdicts = TreeMap()
        self.sources  = TreeMap()

    # ────────────────────────────────────────────────────────
    #  WRITE  — verify a headline and store the result
    # ────────────────────────────────────────────────────────

    @gl.public.write
    def verify_headline(self, headline: str, source_url: str) -> str:
        """
        Fetch the source page, classify the headline with AI,
        reach on-chain validator consensus, and store the verdict.

        Returns one of: REAL | FAKE | MISLEADING | UNVERIFIABLE
        """

        # ── LEADER: runs on the proposing validator ──────────
        def leader_fn() -> str:

            # Step 1: fetch the webpage as plain text
            page = gl.nondet.web.render(source_url, mode="text")
            snippet = (page or "")[:2000]   # cap at 2000 chars

            if not snippet.strip():
                return "UNVERIFIABLE"

            # Step 2: call the AI with a short, focused prompt
            prompt = (
                "You are a fact-checking AI.\n"
                "Headline: \"" + headline + "\"\n\n"
                "Webpage evidence (first 2000 chars):\n"
                + snippet + "\n\n"
                "Based only on the evidence above, classify the headline "
                "as exactly ONE of: REAL, FAKE, MISLEADING, UNVERIFIABLE.\n"
                "Return ONLY valid JSON like: {\"verdict\": \"REAL\"}"
            )

            # response_format='json' makes exec_prompt return a dict directly
            result = gl.nondet.exec_prompt(prompt, response_format="json")

            if isinstance(result, dict):
                v = str(result.get("verdict", "UNVERIFIABLE")).upper().strip()
            else:
                # Safety fallback: scan raw string for a keyword
                raw = str(result).upper()
                v = "UNVERIFIABLE"
                for label in ("REAL", "FAKE", "MISLEADING"):
                    if label in raw:
                        v = label
                        break

            allowed = {"REAL", "FAKE", "MISLEADING", "UNVERIFIABLE"}
            return v if v in allowed else "UNVERIFIABLE"

        # ── VALIDATOR: checks structure, NOT exact text ──────
        #   (LLM output is non-deterministic — never use strict_eq with AI)
        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            allowed = {"REAL", "FAKE", "MISLEADING", "UNVERIFIABLE"}
            return leader_result.calldata in allowed

        # ── CONSENSUS: run leader + validator across all nodes ─
        verdict = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        # ── STORE on-chain ────────────────────────────────────
        self.verdicts[headline] = verdict
        self.sources[headline]  = source_url

        return verdict

    # ────────────────────────────────────────────────────────
    #  VIEWS  — read stored data (no gas cost)
    # ────────────────────────────────────────────────────────

    @gl.public.view
    def get_verdict(self, headline: str) -> str:
        """Return the stored verdict for a headline. Returns NOT_FOUND if unknown."""
        return self.verdicts.get(headline, "NOT_FOUND")

    @gl.public.view
    def get_source(self, headline: str) -> str:
        """Return the source URL that was used to verify a headline."""
        return self.sources.get(headline, "NOT_FOUND")

    @gl.public.view
    def get_all_headlines(self) -> list:
        """Return a list of all headlines that have been verified."""
        return list(self.verdicts.keys())

    @gl.public.view
    def total_verified(self) -> int:
        """Return the total number of verified headlines."""
        count = 0
        for _ in self.verdicts.keys():
            count += 1
        return count
