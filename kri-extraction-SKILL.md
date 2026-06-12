-----

## name: kri-extraction
description: How to extract Key Risk Indicators (KRIs) from enterprise risk report PDFs for Continuous Risk Monitoring (CRM). Use this skill EVERY time a risk report, management report, quarterly risk report, dashboard, RaptOR extract, or committee pack is provided for analysis — before reading any source document. Covers citation rules, trend classification, threshold and risk appetite breach identification, principal inherent risk mapping, and anti-hallucination safeguards.

# KRI Extraction Skill

This skill governs how to read enterprise risk reports and extract KRIs reliably. Follow every rule. When uncertain, choose the more conservative option (omit, flag, or label as unverified).

## 1. Document Inventory (always first)

Before extracting anything, record for each document:

- Document title (as printed on the document)
- Reporting period / as-at date
- Auditable Entity (AE) / business line covered
- Report owner or issuing function, if stated

If any of these is not stated, record `Not stated in source`.

## 2. What Counts as a KRI

Extract every instance of:

- Named Key Risk Indicators and key risk metrics
- Risk appetite statement (RAS) measures, limits, and limit utilisation
- RAG statuses attached to a metric
- Regulatory ratios and thresholds (e.g., LCR, NSFR, ILM, CET1, EVE/NII limits)
- Metrics in tables, charts, and dashboards — not just narrative text

Do NOT extract: general commentary without a measurable indicator, forward-looking statements without figures, or boilerplate.

## 3. Fields to Capture per KRI

|Field                       |Rule                                                                                                                         |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------|
|KRI name                    |Verbatim from source                                                                                                         |
|Current value               |Verbatim, with units                                                                                                         |
|Prior period value(s)       |All shown; if none, `Not stated in source`                                                                                   |
|Threshold / limit / appetite|Verbatim; if none, `Not stated in source`                                                                                    |
|Status                      |RAG or breach status as stated; if implied only by colour in a chart, write `Colour-coded only — verify`                     |
|Risk category               |Principal inherent risk mapping (Section 5)                                                                                  |
|Trend                       |Per Section 4                                                                                                                |
|Confidence                  |High = clearly stated in text/table; Medium = required interpreting layout; Low = partially legible, chart-read, or ambiguous|
|Reference                   |`[Document name, p. X, section/table name]`                                                                                  |

## 4. Trend Classification

Classify each KRI’s trend as one of exactly these labels:

- **Increasing** — risk direction is rising
- **Decreasing** — risk direction is falling
- **Stable** — no material movement
- **Insufficient data for trend** — fewer than two data points in the source
- **Management-asserted trend (unverified)** — commentary claims a trend but no supporting figures are shown

Rules:

1. Trend means **risk direction, not metric direction**. A falling capital ratio, falling liquidity buffer, or falling coverage ratio is **Increasing** risk. A rising loss rate, rising limit utilisation, or rising overdue count is **Increasing** risk. State the metric movement and the risk direction separately if there is any chance of confusion.
1. Never classify a trend from a single data point.
1. Never classify a trend from commentary alone — use the `Management-asserted trend (unverified)` label.
1. If consecutive periods use different definitions or restated figures, note `Basis change — trend not comparable`.

## 5. Principal Inherent Risk Mapping

Map each KRI to one principal inherent risk category. Use the source document’s own mapping when stated. When the document does not map the KRI, suggest a mapping and label it `Agent-suggested mapping`. Categories in use (per the CRM EXAMPLE Step Details):

- Credit Risk
- Market Risk
- Liquidity Risk
- Regulatory Compliance Risk
- Processing and Execution (Operational) Risk
- Reputation Risk
- Strategic Risk

If a KRI plausibly maps to more than one category, list the primary first and note the secondary.

## 6. Threshold and Risk Appetite Breach Identification

Flag and list separately:

1. **Breaches** — KRI at or beyond its stated threshold, limit, or appetite level.
1. **Approaching breach** — within 10% of the threshold, ONLY where both the value and the threshold are explicitly stated in the source. Never compute proximity against an assumed threshold.
1. **RAS breaches** — any explicit statement of a risk appetite breach, listed verbatim with citation.

If no breaches are identified, state: `No breaches identified in source documents`.

## 7. Anti-Hallucination Safeguards

1. Every number in your output must exist verbatim in the source. No interpolation, no derived figures unless you show the arithmetic and cite both inputs.
1. Use the literal escape phrases — `Not stated in source`, `Ambiguous — requires manual review`, `Management-asserted trend (unverified)`, `Agent-suggested mapping` — rather than guessing.
1. If a page, table, or chart is unreadable, say which one and what is missing. Never reconstruct it.
1. If two documents contradict each other, report both values with both citations and flag `Source conflict — requires auditor follow-up`. Do not pick one.
1. Quote sparingly: capture values and statuses, paraphrase commentary.

## 8. Output of This Skill

The product of this skill is the **KRI Extraction Table** (fields per Section 3) plus the **breach list** and **document inventory**. Pass these into the crm-template-population skill — do not present raw extraction as the final answer.