-----

## name: crm-template-population
description: How to format CRM analysis output to match the CRM Program Template (Step 3 — Significant Impact on Risk Profile / Key Risk Factors) and the EXAMPLE Step Details sub-step structure. Use this skill EVERY time analysis output is being written for continuous risk monitoring, quarterly CRM execution, KRI review results, or anything an auditor will transfer into the CRM Program Template — after extraction is complete. Covers field-by-field population rules, sub-step results, Significant Event and WatchList logic, and Impact/IA Response drafting.

# CRM Template Population Skill

This skill defines the exact output structure. The output mirrors two tabs of the CRM Program Template: the **EXAMPLE Step Details** sub-step structure (Part B) and the **CRM Program** execution fields (Part C). Produce ALL sections, in order, every time. Never invent additional sections or omit required ones.

## Output Structure

```
# CRM Step 3 — Key Risk Factors Analysis
AE / Business Line: [from source or "Not stated in source"]
Reporting Period: [from source]
Prepared By: [Agent name] (AI-assisted draft — auditor review required)
Date: [run date]

## A. Document Inventory & KRI Extraction
### A.1 Document Inventory
(per kri-extraction skill Section 1)

### A.2 KRI Extraction Table
| KRI | Risk Category | Current Value | Prior Value(s) | Threshold / Appetite | Status | Trend | Confidence | Reference |

### A.3 Threshold & Risk Appetite Breaches
(breach list, approaching-breach list, RAS breaches — or
"No breaches identified in source documents")

## B. Sub-step Monitoring Results
| Sub-step # | Source Reviewed | Detailed Monitoring Step (summary) | Result | Risk(s) | Reference |

## C. CRM Program Template Fields — Step 3
### C.1 Summary of Outcomes (Agent-suggested — dropdown selection is the auditor's)
### C.2 Comments (only if needed)
### C.3 Management Discussion (Methodology Section 3.3)
### C.4 CTG Work Performed (if applicable)
### C.5 Reference Document(s)
### C.6 Significant Event (if any)
### C.7 WatchList for the Current Quarter
### C.8 Impact / IA Response (Methodology Section 4.0)

## D. Data Gaps & Limitations
## E. Suggested Auditor Follow-ups (max 5)
```

## Part B — Sub-step Monitoring Results

The CRM Program defines sub-steps under Step 3.1 (Key Risk Indicators), each with a source and a detailed monitoring step (e.g., 3.1.22 Liquidity Report → ILM & NSFR limit review; 3.1.24 IR Sub Limit Report → EVE/NII compliance; 3.1.25 Finance Weekly CET1 Analysis → market risk forecast trends). For each sub-step the provided documents can address:

1. Identify the sub-step the document corresponds to. If the sub-step number is not known, describe the source and write `Sub-step # to be confirmed by auditor`.
1. **Result** — answer exactly what the monitoring step asks: Is the entity within limits? Were there changes to limits? What trends are evident? Cite every figure.
1. **Risk(s)** — carry over the risk category mapped in the EXAMPLE Step Details where known (e.g., Liquidity Report → Liquidity Risk / Regulatory Compliance Risk / Reputation Risk; IRR Sub Limit → Market Risk; Exposure Analysis → Credit Risk; RaptOR/quarterly risk reports → Strategic Risk). Otherwise use the kri-extraction mapping rules.
1. If a document maps to no defined sub-step, list it under `Additional sources reviewed (no mapped sub-step)`.
1. For sub-steps whose source documents were NOT provided, list them under `Sub-steps not addressed — source not provided`. Never mark a sub-step complete without its source.

## Part C — Field-by-Field Rules

### C.1 Summary of Outcomes

The template uses a dropdown whose values are controlled in the workbook. Output:

- `Agent-suggested outcome:` one of `No significant change to risk profile` / `Significant event identified — see C.6` / `Emerging risk — WatchList item raised`
- One supporting sentence with citations.
- The line: `Auditor to select the final dropdown value in the template.`

### C.2 Comments

The template instructs comments be “kept to a minimum.” Maximum 3 sentences. Only include what is necessary to interpret the outcome. If nothing is needed, write `None`.

### C.3 Management Discussion (Methodology Section 3.3)

Evidence for this field is the meeting agenda and key outcomes. The agent cannot attend discussions, so:

- If meeting minutes/agendas are among the provided documents: summarise the discussion focus and key outcomes with citations.
- Otherwise write: `Pending — to be completed by auditor following management discussion. Suggested discussion topics based on KRI analysis:` followed by up to 3 topics drawn from breaches, adverse trends, or source conflicts.

### C.4 CTG Work Performed (if applicable)

If the documents evidence CTG (Centralized Testing Group) work, summarise with citations. Otherwise write `Not applicable / not stated in source`.

### C.5 Reference Document(s)

List every document relied upon: title, period, and where it informed the analysis. This populates the template’s Reference Document column.

### C.6 Significant Event (if any)

Per the template: state **“None”** or **“Yes”** and describe. Documentation must be targeted/focused only on significant items.

- Default to `None` unless the source evidence shows: a threshold/limit/RAS breach; a sustained adverse KRI trend across multiple periods; an explicitly escalated item in the report; or a stated regulatory action/finding.
- If `Yes`: describe in 2–4 sentences maximum, citing the specific KRIs and pages. Label the determination `Agent-suggested — auditor to confirm significance`.
- Never escalate on commentary alone (`Management-asserted trend (unverified)` items cannot by themselves trigger a significant event).

### C.7 WatchList for the Current Quarter

Per the template: state **“None”** or note items to monitor next quarter.

- Candidates: approaching-breach KRIs (within 10% of an explicit threshold), single-period adverse movements not yet a trend, `Source conflict` items, and management-asserted trends awaiting data.
- Each item: one line — KRI, why it warrants monitoring, citation.
- If no candidates: `None`.

### C.8 Impact / IA Response (Methodology Section 4.0)

Mandatory if a significant event is identified; otherwise may be left blank except WatchList. Populate all four columns:

|Column                            |Rule                                                                                                                                                                                  |
|----------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|Change to Audit Universe          |`Agent-suggested: None` or describe, with rationale (refer to Audit Universe methodology)                                                                                             |
|Change in AE level Risk Assessment|`Agent-suggested: None` or state the inherent risk(s) whose direction the evidence supports changing — direction only, never a new rating value (refer to Risk Assessment methodology)|
|Retrospective Review              |`Agent-suggested: Not triggered` or describe the trigger (refer to Appendix 2, Global CRM Methodology)                                                                                |
|Audit Plan Change                 |`Agent-suggested: None` or describe (refer to Audit Plan Change Standard)                                                                                                             |

If C.6 is `None`, write across the block: `No significant event identified — section not required per Methodology 4.0. WatchList completed at C.7.`

## Part D — Data Gaps & Limitations

List: sub-steps without provided sources; principal inherent risks with no supporting KRI; KRIs missing thresholds or prior periods; unreadable pages/charts; source conflicts.

## Part E — Suggested Auditor Follow-ups

Maximum 5 bullets. Each must be a specific question or evidence request tied to a gap, breach, conflict, or unverified trend. No generic advice.

## Self-Check (run before responding)

1. Every number has a `[Document, p. X, section]` citation.
1. No trend claimed from fewer than two data points.
1. C.1, C.6, C.7, and C.8 use the exact controlled phrases (`None`, `Yes`, `Agent-suggested...`).
1. No final rating, dropdown selection, or IA response decision presented as decided.
1. All escape-phrase labels (`Not stated in source`, `Ambiguous — requires manual review`, `Management-asserted trend (unverified)`, `Agent-suggested mapping`, `Source conflict — requires auditor follow-up`) applied wherever required.
1. Comments field ≤ 3 sentences; Significant Event description ≤ 4 sentences.
1. Sections A through E all present, in order.