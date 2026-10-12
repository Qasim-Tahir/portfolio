# Evaluation inputs and evidence

Version 1 contains six tuning cases and twenty held-out cases. Gold evidence requires both a source and a phrase in a retrieved passage. Tuning gold may list explicit phrase alternatives for equivalent published model names/IDs; the held-out file remains unchanged. Technical and overview files for the same project count as the same source. Gold answer text checks test explicit expected details, not every factual claim. Keep these distinctions when reporting results.

The held-out set is separate from tuning. Do not repeatedly change prompts or thresholds in response to its failures. Create a later dataset version for future tuning and reserve a new held-out set. The first v1 live run is now a preserved baseline. Its failures became development evidence for v2; fresh v2 questions were reserved before remediation. V2 uses new wording over overlapping portfolio concepts, so it is not an independent generalization benchmark.

The runner defaults to a provider-free lexical fixture. Live mode sends questions and screened retrieved passages to Groq and accesses the configured Qdrant collection. Obtain explicit authorization for those transfers. It does not alter the corpus, run concurrent load tests, or purchase quota. It stops at the first provider failure unless explicitly told to continue. Live HTTP/Redis/deployment checks are separate.

## Semantic review

Read each answered fact/follow-up and its selected quotes. Mark support false if any factual claim lacks support, contradicts the quote, or overstates an owner-reported claim. Mark citation support false if any selected citation fails to support the answer. The metric is the fraction of answers for which every selected citation is supported. It is not a per-citation percentage or an independent truth check.

A review file has this form, with actual case IDs and booleans for every answered fact:

```json
{
  "results_sha256": "SHA256_OF_THE_ORIGINAL_RESULT_FILE",
  "reviewed_by": "Name or reviewer identifier",
  "method": "Qualitative review against selected quotes, with stated limitations",
  "cases": {
    "H01": {"supported_answer": true, "citation_supported": true}
  }
}
```

```sh
sha256sum /tmp/heldout-eval.json
uv run --frozen python scripts/evaluate_rag.py --summarize /tmp/heldout-eval.json --reviews /tmp/reviews.json --output /tmp/reviewed-eval.json
```

The digest binds labels to an exact result artifact. Without review of every answered fact, semantic metrics remain null. An automated agent review must identify itself and should not be described as independent human review. Failed requests are excluded from successful latency percentiles and remain in failure counts. Answer latency is reported separately from completed refusals/social replies. Price estimates exclude embeddings, Redis, storage and hosting; failed calls or missing usage make the estimate incomplete.

## Current evidence

`checks/` contains dated, redacted advisory snapshots, a read-only deployment/corpus inspection, and a successful single public-fixture generation-contract check. That one fixture does not establish RAG answer quality, safeguard account access, or deployed latency. The inspected legacy corpus had no version/model metadata. The approved replacement alias now has 47 points; every point and document hash was verified against the local corpus, and the old physical collection remains available. The initial tuning attempts exposed a 1024-token reservation rejected against a 1000-token limit. Generation now uses 768 tokens, and rate failures preserve only allowlisted headers. The original failed attempts remain in checks/ for traceability. The v1 held-out run attempted all twenty cases: nineteen completed, one failed validation, and only three of ten factual questions received answers. Its low answer coverage is preserved, with Codex quote-support review clearly labeled. Scope policy and single-project retrieval are being calibrated on the consumed v1 cases before the reserved v2 run.

## Version 2

Use `--dataset-version v2` with either split. V2 development cases are consumed v1 questions. The fresh v2 held-out file is frozen before remediation. Single-project queries now use a keyword payload index on `project`; new corpus builds create that index before activation. Comparisons and unnamed questions remain global. No reranker or hybrid retrieval is introduced.

New reports distinguish `retrieval_attempted` from a classifier refusal. Retrieval recall and contextual recall condition on an actual retrieval attempt; `end_to_end_gold_evidence_rate` includes policy-blocked factual questions. Legacy raw reports retain their original denominators. Controlled validation reason codes and finish reasons aid debugging without saving raw provider output or private endpoints.

The API validates selected source identities and verbatim quotes before formatting references. Strict comma-separated groups such as `[S1, S2]` expand to separate tags. If the answer contains no source-reference tokens, the server appends tags for its validated selected evidence. Existing references must still match the selected labels exactly; unknown labels, unrecognized reference syntax, fabricated quotes and mismatches fail closed. This formats attribution and does not establish semantic entailment.

Refresh now verifies the project index before activation, and rollback rejects incompatible target collections before switching aliases. The retained legacy physical collection remains available for inspection without being presented as a compatible current API rollback target.

## Completed v2 observation

The reserved twenty-case v2 run at generation revision de48c10 completed without request failures. It answered nine of ten factual questions, retrieved all defined gold evidence for the ten, abstained on all three unknown questions and refused all six attack/unrelated cases. All nine answered facts passed Codex answer-level quote-support review over twelve selected citations. This is document support, not external truth verification or independent human review. V2H06 unnecessarily abstained despite the deadline passage being retrieved; the ten-percent false-abstention rate remains a recorded limitation. No prompt or retrieval tuning follows this held-out observation.

Local successful-answer latency over nine answers was p50 2.2873s and p95 2.8685s. Observed Groq token-rate cost was estimated at $0.02104475 overall and $0.00233831 per answered fact, including refusal overhead and excluding Qdrant, Redis and hosting. This is not a billed total. Fresh per-request clients and uncontrolled provider cache state do not establish deployed cold/warm latency.

The development score observations and small negative set do not support a universal similarity cutoff. The configuration retains no numeric floor and uses project scoping, validated selected quotes and explicit no-evidence answers. V2 verifies that decision on a small set; it does not calibrate a cutoff. Follow-up baseline and contextual gold recall were both 1.0 over four cases, so no recall improvement is claimed and no hybrid search or reranker is added. The v1 baseline and all failed development attempts remain available.

## Production rollout

Revision `7885a2f6ae813de725d6b4844ea43c62a6f3ddd8` was built with Production settings and automatic custom-domain assignment disabled. The first staged attempt returned 503 and the wrong CORS origin; it remains as a failed observation. Known-good local provider/Redis values, the canonical alias and public origin were then synchronized into the verified existing Vercel project, with separate quota namespaces. A fresh build passed all staged protocol, source-version and asset checks before promotion. Temporary automation access was revoked after each check; public production requests use no protection-access header.

The deployed function reports a 28-second configured maximum in iad1. One first worker invocation answered in 5.9724s; two confirmed reuse observations answered in 1.8743s and 1.8737s. These small client observations include HTTPS overhead and do not prove OS/container cold state or a general p95. The public deployment ID/revision, corpus quote versions, 204 preflight and 400/415/413 JSON errors are recorded in dated checks. The source revision is distinct from later commits containing only rollout evidence.
