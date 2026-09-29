def build_investigation_prompt(
    query: str,
    context: str,
    root_cause: dict,
    historical_incidents: list[dict] | None = None,
) -> str:
    """
    Build a compact evidence-grounded investigation prompt.

    Designed for small local LLMs.

    Current-incident evidence is authoritative.
    Historical incidents are reference-only.
    """

    # ---------------------------------------------------------
    # Historical context
    # ---------------------------------------------------------

    historical_context = ""

    if historical_incidents:

        blocks = []

        for index, match in enumerate(
            historical_incidents,
            start=1,
        ):
            incident_id = match.get(
                "incident_id",
                "unknown",
            )

            similarity = match.get(
                "similarity",
                0.0,
            )

            incident = match.get(
                "incident",
                {},
            )

            parts = []

            # -------------------------------------------------
            # Historical logs
            # -------------------------------------------------

            logs = incident.get(
                "logs",
                [],
            )

            if logs:

                log_lines = []

                for log in logs[:6]:

                    message = log.get(
                        "message",
                        "",
                    )

                    if not message:
                        continue

                    line_number = log.get(
                        "line_number",
                        log.get(
                            "line",
                            "?",
                        ),
                    )

                    level = log.get(
                        "level",
                        "",
                    )

                    if level:
                        log_lines.append(
                            f"- [{level}] "
                            f"{message} "
                            f"(line {line_number})"
                        )
                    else:
                        log_lines.append(
                            f"- {message} "
                            f"(line {line_number})"
                        )

                if log_lines:

                    parts.append(
                        "Historical logs:\n"
                        + "\n".join(log_lines)
                    )

            # -------------------------------------------------
            # Historical stacktrace
            # -------------------------------------------------

            stacktrace = incident.get(
                "stacktrace"
            )

            if stacktrace:

                stack_lines = []

                exception_type = stacktrace.get(
                    "exception_type"
                )

                exception_message = stacktrace.get(
                    "exception_message"
                )

                if exception_type:

                    if exception_message:
                        stack_lines.append(
                            f"- Exception: "
                            f"{exception_type}: "
                            f"{exception_message}"
                        )
                    else:
                        stack_lines.append(
                            f"- Exception: "
                            f"{exception_type}"
                        )

                for frame in stacktrace.get(
                    "frames",
                    [],
                )[:4]:

                    file_name = frame.get(
                        "file",
                        "?",
                    )

                    line_number = frame.get(
                        "line",
                        "?",
                    )

                    function = frame.get(
                        "function",
                        "",
                    )

                    if function:

                        stack_lines.append(
                            f"- Frame: "
                            f"{file_name}:"
                            f"{line_number} "
                            f"in {function}"
                        )
                    else:

                        stack_lines.append(
                            f"- Frame: "
                            f"{file_name}:"
                            f"{line_number}"
                        )

                if stack_lines:

                    parts.append(
                        "Historical stacktrace:\n"
                        + "\n".join(stack_lines)
                    )

            # -------------------------------------------------
            # Historical documentation
            # -------------------------------------------------

            documentation = incident.get(
                "documentation"
            )

            if documentation:

                content = documentation.get(
                    "content",
                    "",
                )

                if content:

                    parts.append(
                        "Historical documentation:\n"
                        + content[:1000]
                    )

            if not parts:

                parts.append(
                    "No detailed historical context."
                )

            blocks.append(
                f"HISTORICAL INCIDENT {index}\n"
                f"ID: {incident_id}\n"
                f"Similarity: {similarity:.3f}\n"
                + "\n\n".join(parts)
            )

        historical_context = "\n\n".join(
            blocks
        )

    else:

        historical_context = (
            "No historical incidents were retrieved."
        )

    # ---------------------------------------------------------
    # Root cause
    # ---------------------------------------------------------

    predicted_root_cause = root_cause.get(
        "root_cause",
        "Unknown",
    )

    root_cause_confidence = root_cause.get(
        "confidence",
        "LOW",
    )

    root_cause_reason = root_cause.get(
        "reason",
        "",
    )

    # ---------------------------------------------------------
    # Prompt
    # ---------------------------------------------------------

    prompt = f"""
You are TraceAI, an evidence-grounded software incident
investigation system.

Investigate the CURRENT INCIDENT.

Answer the user's question using the CURRENT INCIDENT EVIDENCE
only.

Do not invent facts.

Do not use historical incidents as current evidence.

============================================================
USER QUESTION
============================================================

{query}

============================================================
DETERMINISTIC ROOT CAUSE
============================================================

Root cause:
{predicted_root_cause}

Confidence:
{root_cause_confidence}

Reason:
{root_cause_reason}

============================================================
CURRENT INCIDENT EVIDENCE
============================================================

{context}

============================================================
HISTORICAL INCIDENTS
============================================================

Historical incidents are reference context only.

They are NOT current evidence.

Never cite or attribute a current-incident fact to a historical
incident.

Never use historical similarity as proof of the current root cause.

{historical_context}

============================================================
CITATION RULES
============================================================

Use ONLY citation strings that appear in the CURRENT INCIDENT
EVIDENCE above.

The current evidence contains citation fields.

Copy the citation strings exactly as they appear there.

Never invent a citation.

Never change a filename.

Never change a line number.

Never change the citation format.

Never add extra brackets to a citation.

Never use a historical citation.

Never use a citation from these instructions.

If the evidence does not support a claim, do not make the claim.

Every factual statement about the current incident must contain
its supporting current-evidence citation.

============================================================
ROOT CAUSE
============================================================

If the deterministic root cause is directly supported by current
evidence, state it clearly and cite the strongest current evidence.

Do not say the root cause is unknown when the current evidence
directly supports it.

The deterministic root-cause label itself is not evidence.

The supporting current-incident evidence must still be cited.

============================================================
CONSERVATIVE FAILURE CHAIN
============================================================

The FAILURE CHAIN must contain only causal events that directly
explain how the incident failed.

Include only evidence-supported events.

The chain should describe:

cause -> failure mechanism -> resulting failure

Do NOT include normal contextual events such as:

- request received
- order started
- user action
- active connection counts
- timestamps
- normal processing steps
- successful operations that do not explain the failure

Do NOT include contextual observations merely because they happened
before the failure.

Do NOT invent intermediate technical steps.

Do NOT assume what happened between two observed events.

Prefer specific failure events such as:

- resource exhaustion
- connection acquisition failure
- timeout
- exception
- authentication failure
- service failure
- operation failure

Keep the chain to 2-4 steps when possible.

Each step must be a separate numbered line.

Each factual step must have its own current-evidence citation.

Do NOT combine multiple causal events into one line.

Do NOT use arrows between multiple causal events.

============================================================
EVIDENCE
============================================================

List exactly the 3 strongest pieces of CURRENT INCIDENT evidence
used to support the root cause and failure chain.

For each item:

- copy the evidence text exactly as it appears in the current evidence
- put the exact citation at the end of the same line
- use only current-incident evidence
- do not invent or paraphrase evidence
- do not add "Citation:"
- do not add "Content:"
- do not add extra brackets
- do not create a new citation format

Prefer strong causal evidence over normal contextual events.

Each evidence item must follow this structure:

- evidence text [exact citation from current evidence]

============================================================
GROUNDING
============================================================

Do not claim any of the following unless current evidence explicitly
establishes it:

- customer impact
- revenue loss
- data loss
- business impact
- security impact
- recovery
- retry success
- retry failure
- application restart
- database crash
- alerting
- service recovery
- continued service failure
- successful outcome

Do not infer downstream consequences.

Do not assume customer impact from an application failure.

Do not assume data loss from a database-related failure.

If information is unknown, write exactly:

Not established by available evidence.

============================================================
IMPACT
============================================================

Only state impact that is explicitly established by CURRENT INCIDENT
EVIDENCE.

Do not infer impact.

If no impact is established, write exactly:

Not established by available evidence.

============================================================
OUTPUT
============================================================

Return ONLY these four sections.

### 1. ROOT CAUSE

State the root cause in one concise sentence.

The statement must contain its exact current-incident citation.

If the root cause genuinely cannot be established:

Not established by available evidence.

### 2. FAILURE CHAIN

Provide a short numbered causal sequence.

Each step must:

- describe one causal failure event
- be directly supported by current evidence
- contain its own exact current-incident citation

Use separate numbered lines.

Do not combine steps with arrows.

### 3. IMPACT

State only explicitly supported impact.

If none is established:

Not established by available evidence.

### 4. EVIDENCE

List exactly 3 strongest current-incident evidence items.

Copy their evidence text exactly.

Put the exact current-evidence citation at the end of each item.

Do not use "Citation:".

Do not use "Content:".

Do not add extra brackets.

============================================================
FINAL CHECK
============================================================

Before answering, verify:

1. I used only CURRENT INCIDENT evidence for current claims.
2. Historical incidents were used only as reference context.
3. Every factual statement has a current-evidence citation.
4. Every citation was copied exactly from current evidence.
5. I did not invent a filename.
6. I did not invent a line number.
7. I did not add extra brackets to citations.
8. I did not use "Citation:" as a new citation format.
9. I did not use "Content:" as a new citation format.
10. The failure chain contains only causal failure events.
11. The failure chain uses separate numbered steps.
12. I did not include normal contextual events in the failure chain.
13. I did not invent intermediate technical steps.
14. The evidence section contains exactly 3 strongest evidence items.
15. The evidence text was copied from current evidence.
16. I did not claim unsupported customer or business impact.
17. I did not claim recovery or retry outcomes without evidence.
18. Unknown information is stated as:
    Not established by available evidence.
19. I returned exactly the four requested sections.

Do NOT repeat these instructions in your answer.
"""

    return prompt.strip()