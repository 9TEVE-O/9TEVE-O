# EXA_SMARTERWAY_INGEST_001_RESULT

## Experiment

- **Experiment ID:** `EXA_SMARTERWAY_INGEST_001`
- **Objective:** Determine whether Exa can reliably discover and retrieve the publicly accessible SmarterWay prompt catalogue sufficiently well to serve as the discovery/retrieval layer of a governed prompt-ingestion workflow.
- **Primary source:** <https://smarterway.ai/prompts/all>
- **Scope:** Publicly accessible content originating from `smarterway.ai` only.
- **Execution date:** 2026-08-21 (UTC)
- **Exa configuration attempted:** Hosted MCP endpoint `https://mcp.exa.ai/mcp`, with no agent tooling or credentials enabled.
- **Comparison gate:** Compare Exa's prompt URL and retrieval-status output with the independently verified baseline.

## Inventory

No prompt records were discovered. Exa's hosted MCP transport could not be reached from the execution environment, so neither the catalogue nor any prompt page was retrieved. No search-result snippets, inferred URL slugs, invented URLs, or unverified metadata have been converted into records.

The inventory is therefore the empty JSON array:

```json
[]
```

## SUMMARY

| Measure | Count |
|---|---:|
| Total unique prompt records | 0 |
| Accessible verified | 0 |
| Discovered but not retrieved | 0 |
| Access denied | 0 |
| Not found | 0 |
| Ambiguous | 0 |
| Errors | 0 |
| Duplicates detected | 0 |

The error count is a count of **prompt records** carrying `retrieval_status: ERROR`. Because no prompt entry was discovered, it is zero. The experiment-level transport failure is reported separately below and must not be interpreted as a successful empty catalogue.

## BASELINE COMPARISON

The comparison gate was **not executed**. There is no Exa URL/status output to compare because the Exa MCP transport failed before its tools could be listed or called. In addition, no independently verified SmarterWay baseline dataset is present in this repository; the only SmarterWay artefact in the current tree is this experiment result.

| Comparison measure | Result |
|---|---|
| Exa records available for comparison | 0 |
| Verified baseline records available in repository | 0 |
| URL matches | `NOT_MEASURED` |
| URL mismatches | `NOT_MEASURED` |
| Retrieval-status matches | `NOT_MEASURED` |
| Retrieval-status mismatches | `NOT_MEASURED` |

These values are not zero-error results. `NOT_MEASURED` means no comparison was possible. A valid rerun must retain Exa's raw URL/status output, identify the immutable verified-baseline artefact and version used, and report URL and status mismatches without silently normalizing them away.

## DISCOVERY COVERAGE

- **Catalogue traversal:** Not performed. Codex registered the Exa hosted MCP URL, but the MCP client could not establish its HTTP transport. Consequently, Exa could not retrieve `https://smarterway.ai/prompts/all`.
- **Pagination:** Not inspected. The presence, structure, and extent of pagination are unknown.
- **Categories and filters:** Not inspected. No category or filter page was discovered or traversed.
- **Direct prompt links:** Not inspected because the source catalogue was not retrieved.
- **Web-search discovery:** Not performed. Exa search tools were unavailable after the MCP transport failed. No substitute search provider was used because this experiment specifically evaluates Exa.
- **Exhaustiveness:** Enumeration did not begin. The zero-record inventory reflects an unavailable retrieval layer, not evidence that the catalogue contains no public prompts.

## FAILURE LOG

| URL | Failure type | What was attempted | Could retrying reasonably change the result? |
|---|---|---|---|
| `https://mcp.exa.ai/mcp` | `ERROR` — MCP transport unavailable | Added the hosted endpoint with `/opt/codex/bin/codex mcp add exa --url https://mcp.exa.ai/mcp`. The configuration was written successfully. MCP initialization then failed repeatedly with `http/request failed: error sending request for url (https://mcp.exa.ai/mcp)`. A direct HTTP connectivity check also received `HTTP CONNECT failed with status 403` from the environment's outbound proxy. | Yes. Retry from an environment whose outbound policy permits HTTPS connections to `mcp.exa.ai`; then rerun the entire experiment. Retrying unchanged in this environment is unlikely to help. |
| `https://smarterway.ai/prompts/all` | `ERROR` — retrieval not attempted because Exa was unavailable | Intended to begin discovery from this URL through Exa. No Exa tool call could be issued after MCP initialization failed. The page was not fetched through another provider, and its accessibility was not inferred. | Yes, after Exa MCP connectivity is restored. |

No individual prompt retrieval failures can be listed because no prompt URL was discovered.

## UNCERTAINTIES

The following prevent the claim, “We identified every publicly accessible prompt in the SmarterWay catalogue”:

1. The primary catalogue page was not retrieved.
2. Catalogue pagination could not be detected or traversed.
3. Category and filter surfaces could not be detected or traversed.
4. Directly linked prompt pages could not be enumerated.
5. Exa web search could not run, so it could not discover SmarterWay prompt pages outside the main catalogue.
6. No actual prompt page was retrieved, so no title, category, canonical URL, page identity, or access status could be verified.
7. Completeness, deduplication quality, and retrieval reliability could not be measured from an empty inventory caused by an experiment-level transport failure.
8. It remains unknown whether authentication would be required for any later Exa operation; MCP initialization failed before tool capabilities could be inspected.
9. URL and retrieval-status accuracy against the independently verified baseline could not be measured because neither Exa output nor the referenced baseline dataset was available in this checkout.

This artefact deliberately makes no `PASS`, `CONDITIONAL PASS`, or `FAIL` decision.

EXPERIMENT RESULT: COMPLETE
