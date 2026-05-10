# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
import typing
from genlayer import *


class NewsVerifier(gl.Contract):

    # TreeMap is the correct dict replacement in GenVM (NOT plain dict)
    # Do NOT assign these in __init__ -- GenVM initialises them automatically
    verdicts: TreeMap[str, str]
    sources:  TreeMap[str, str]
    reasons:  TreeMap[str, str]

    def __init__(self):
        pass

    @gl.public.write
    def verify_headline(self, headline: str, source_url: str) -> typing.Any:

        def leader_fn() -> str:
            # Fetch the live source page
            page_text = gl.nondet.web.get(source_url).body.decode("utf-8", errors="replace")
            snippet = page_text[:3000]

            prompt = (
                "You are an expert fact-checker.\n\n"
                "HEADLINE: \"" + headline + "\"\n\n"
                "WEBPAGE (first 3000 chars):\n" + snippet + "\n\n"
                "Classify the headline as exactly ONE of:\n"
                "  REAL        - headline accurately reflects the source\n"
                "  FAKE        - headline contradicts or is not in the source\n"
                "  MISLEADING  - source is related but headline exaggerates it\n"
                "  UNVERIFIABLE- source has no relevant content\n\n"
                "Return ONLY this JSON and nothing else:\n"
                "{\"verdict\": \"REAL\", \"reason\": \"one sentence explanation\"}"
            )

            raw = gl.nondet.exec_prompt(prompt)
            cleaned = raw.strip().strip("```json").strip("```").strip()

            try:
                data = json.loads(cleaned)
                verdict = str(data.get("verdict", "UNVERIFIABLE")).upper().strip()
                reason = str(data.get("reason", "No reason provided."))
                if verdict not in {"REAL", "FAKE", "MISLEADING", "UNVERIFIABLE"}:
                    verdict = "UNVERIFIABLE"
            except Exception:
                verdict = "UNVERIFIABLE"
                reason = "Could not parse LLM response."

            return json.dumps({"verdict": verdict, "reason": reason}, sort_keys=True)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                validator_raw = leader_fn()
                leader_verdict = json.loads(leader_result.calldata).get("verdict", "")
                validator_verdict = json.loads(validator_raw).get("verdict", "")
                # Only the verdict label must match -- reason text may differ across LLMs
                return leader_verdict == validator_verdict
            except Exception:
                return False

        result_json = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        try:
            parsed = json.loads(result_json)
            verdict = parsed.get("verdict", "UNVERIFIABLE")
            reason = parsed.get("reason", "")
        except Exception:
            verdict = "UNVERIFIABLE"
            reason = "Parse error."

        key = headline[:200]
        self.verdicts[key] = verdict
        self.sources[key]  = source_url[:200]
        self.reasons[key]  = reason

    @gl.public.view
    def get_verdict(self, headline: str) -> str:
        return self.verdicts.get(headline[:200], "NOT_FOUND")

    @gl.public.view
    def get_full_result(self, headline: str) -> str:
        key = headline[:200]
        verdict = self.verdicts.get(key, "NOT_FOUND")
        if verdict == "NOT_FOUND":
            return json.dumps({"error": "NOT_FOUND"})
        return json.dumps({
            "headline": headline,
            "verdict":  verdict,
            "reason":   self.reasons.get(key, ""),
            "source":   self.sources.get(key, ""),
        }, sort_keys=True)

    @gl.public.view
    def get_all_headlines(self) -> str:
        return json.dumps(list(self.verdicts.keys()))

    @gl.public.view
    def total_verified(self) -> int:
        count = 0
        for _ in self.verdicts.keys():
            count += 1
        return count
