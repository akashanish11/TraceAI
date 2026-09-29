import hashlib
import re
import shutil
from pathlib import Path

import streamlit as st

from app.services.investigation_service import InvestigationService


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TraceAI — Incident Investigator",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    .trace-title {
        font-size: 2.35rem;
        font-weight: 750;
        margin-bottom: 0.15rem;
    }

    .trace-subtitle {
        color: #8b949e;
        font-size: 1rem;
        margin-bottom: 1.8rem;
    }

    .muted {
        color: #8b949e;
    }

    .citation {
        font-family: monospace;
        font-size: 0.88rem;
    }

    .status-pass {
        color: #2ea043;
        font-weight: 700;
    }

    .status-review {
        color: #d29922;
        font-weight: 700;
    }

    .status-fail {
        color: #f85149;
        font-weight: 700;
    }

    .rca-card {
        padding: 1.35rem 1.5rem;
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 14px;
        background: rgba(128,128,128,0.055);
    }

    .rca-label {
        color: #8b949e;
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
    }

    .rca-value {
        font-size: 1.55rem;
        font-weight: 750;
        line-height: 1.3;
        margin-top: 0.3rem;
        margin-bottom: 0.55rem;
    }

    .workflow-card {
        padding: 1rem;
        border: 1px solid rgba(128,128,128,0.20);
        border-radius: 12px;
        min-height: 125px;
    }

    .workflow-number {
        color: #8b949e;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.08em;
    }

    .workflow-name {
        font-weight: 700;
        margin: 0.25rem 0 0.45rem 0;
    }

    .section-caption {
        color: #8b949e;
        margin-top: -0.5rem;
        margin-bottom: 0.8rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PATHS
# ============================================================

BASE_INCIDENT_DIRECTORY = Path("data/incidents")
RUNTIME_DIRECTORY = Path("data/.traceai_runtime")
HISTORY_DATABASE = Path("data/traceai.db")

ALLOWED_EXTENSIONS = {
    ".log",
    ".stacktrace",
    ".md",
}


# ============================================================
# INVESTIGATORS
# ============================================================

@st.cache_resource
def load_investigation_service(incident_directory: str):
    return InvestigationService(
        incident_directory=incident_directory,
        history_database=str(HISTORY_DATABASE),
    )


# ============================================================
# UI HELPERS
# ============================================================

def status_badge(status):
    status = str(status).upper()

    if status == "PASS":
        return '<span class="status-pass">● PASS</span>'

    if status == "REVIEW":
        return '<span class="status-review">● REVIEW</span>'

    return '<span class="status-fail">● FAIL</span>'


def confidence_badge(level):
    level = str(level).upper()

    if level == "HIGH":
        return "🟢 HIGH"

    if level == "MEDIUM":
        return "🟡 MEDIUM"

    return "🔴 LOW"


def get_incident_ids(service):
    return service.list_incidents()


def format_evidence(item):
    return {
        "source_file": item.get(
            "source_file",
            "unknown",
        ),
        "location": item.get(
            "location",
            "unknown",
        ),
        "text": item.get(
            "text",
            "",
        ),
        "source_type": item.get(
            "source_type",
            "unknown",
        ),
        "provenance": item.get(
            "provenance",
            "unknown",
        ),
        "score": item.get(
            "final_score",
            item.get(
                "score",
                0.0,
            ),
        ),
    }


# ============================================================
# UPLOAD HANDLING
# ============================================================

def create_runtime_corpus(uploaded_files):
    """
    Creates an isolated runtime corpus.

    Original data/incidents is never modified.
    """

    if not uploaded_files:
        return None, None

    file_contents = []

    for uploaded_file in uploaded_files:

        filename = Path(
            uploaded_file.name
        ).name

        extension = Path(
            filename
        ).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            continue

        file_contents.append(
            (
                filename,
                uploaded_file.getvalue(),
            )
        )

    if not file_contents:
        return None, None

    hasher = hashlib.sha256()

    for filename, content in sorted(
        file_contents,
        key=lambda item: item[0],
    ):
        hasher.update(
            filename.encode("utf-8")
        )
        hasher.update(content)

    upload_hash = hasher.hexdigest()[:12]

    incident_id = f"uploaded_{upload_hash}"

    runtime_directory = (
        RUNTIME_DIRECTORY / incident_id
    )

    runtime_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Copy original corpus into isolated runtime.
    for source in BASE_INCIDENT_DIRECTORY.iterdir():

        destination = (
            runtime_directory / source.name
        )

        if destination.exists():
            continue

        if source.is_dir():

            shutil.copytree(
                source,
                destination,
            )

        elif source.is_file():

            shutil.copy2(
                source,
                destination,
            )

    uploaded_incident_directory = (
        runtime_directory / incident_id
    )

    uploaded_incident_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    for filename, content in file_contents:

        target = (
            uploaded_incident_directory / filename
        )

        target.write_bytes(content)

    return (
        str(runtime_directory),
        incident_id,
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="trace-title">🔎 TraceAI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="trace-subtitle">
        Evidence-Grounded GenAI System for Software Incident
        Investigation and Root Cause Analysis
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR — INFORMATION ONLY
# ============================================================

with st.sidebar:

    st.markdown("## TraceAI")

    st.caption(
        "Local, evidence-grounded incident investigation."
    )

    st.divider()

    st.markdown("### Architecture")

    st.markdown(
        """
        **Retrieval**
        - Sentence Transformers
        - FAISS
        - Multi-source evidence

        **Analysis**
        - Deterministic RCA
        - Historical matching
        - Local LLM

        **Grounding**
        - Citation repair
        - Citation verification
        - Claim verification
        - Groundedness
        """
    )

    st.divider()

    st.markdown("### Supported Files")

    st.caption(
        "`.log` · `.stacktrace` · `.md`"
    )

    st.markdown("### Runtime")

    st.caption(
        "Local CPU inference · Open-source stack"
    )


# ============================================================
# LOAD DEFAULT INVESTIGATION SERVICE
# ============================================================

try:

    with st.spinner(
        "Loading TraceAI investigation engine..."
    ):
        default_service = load_investigation_service(
            str(BASE_INCIDENT_DIRECTORY)
        )

except Exception as error:

    st.error(
        "Failed to initialize TraceAI."
    )

    st.exception(error)

    st.stop()


# ============================================================
# INVESTIGATION WORKSPACE
# ============================================================

st.markdown("## Investigation Workspace")

workspace_left, workspace_right = st.columns(
    [1.15, 1],
    gap="large",
)


# ============================================================
# UPLOAD INCIDENT
# ============================================================

with workspace_left:

    with st.container(border=True):

        st.markdown("### 📤 Upload Incident")

        st.caption(
            "Upload one or more files belonging to the same incident."
        )

        uploaded_files = st.file_uploader(
            "Incident files",
            type=[
                "log",
                "stacktrace",
                "md",
            ],
            accept_multiple_files=True,
            help=(
                "Supported formats: .log, .stacktrace and .md"
            ),
        )

        runtime_directory = None
        uploaded_incident_id = None

        if uploaded_files:

            (
                runtime_directory,
                uploaded_incident_id,
            ) = create_runtime_corpus(
                uploaded_files
            )

            if runtime_directory:

                st.success(
                    f"Uploaded incident ready: "
                    f"`{uploaded_incident_id}`"
                )

                st.caption(
                    "The original incident corpus is unchanged. "
                    "The upload is indexed in an isolated runtime corpus."
                )


# ============================================================
# SELECT INVESTIGATION SERVICE
# ============================================================

if runtime_directory:

    try:

        with st.spinner(
            "Indexing uploaded incident..."
        ):

            investigation_service = (
                load_investigation_service(
                    runtime_directory
                )
            )

    except Exception as error:

        st.error(
            "Failed to index uploaded incident."
        )

        st.exception(error)

        investigation_service = default_service

else:

    investigation_service = default_service


# ============================================================
# INVESTIGATION SETUP
# ============================================================

with workspace_right:

    with st.container(border=True):

        st.markdown("### 🎯 Investigation Setup")

        incident_ids = get_incident_ids(
            investigation_service
        )

        if not incident_ids:

            st.error(
                "No incidents were found."
            )

            st.stop()

        preferred_index = 0

        if uploaded_incident_id in incident_ids:

            preferred_index = (
                incident_ids.index(
                    uploaded_incident_id
                )
            )

        selected_incident = st.selectbox(
            "Incident",
            incident_ids,
            index=preferred_index,
        )

        incident_id = selected_incident

        # Better default question for uploaded incidents.
        if uploaded_incident_id:

            default_query = (
                "Why did this incident fail?"
            )

        else:

            default_query = (
                "Why did the payment service fail "
                "to acquire a database connection?"
            )

        query = st.text_area(
            "Investigation question",
            value=default_query,
            height=105,
        )

        top_k = st.slider(
            "Evidence items to retrieve",
            min_value=3,
            max_value=12,
            value=8,
        )

        investigate_button = st.button(
            "🔍 Investigate Incident",
            type="primary",
            use_container_width=True,
        )


# ============================================================
# WORKFLOW
# ============================================================

st.markdown("### How TraceAI Investigates")

flow1, flow2, flow3, flow4 = st.columns(
    4
)

workflow = [
    (
        flow1,
        "01",
        "Retrieve Evidence",
        "Search logs, stack traces, code and documentation.",
    ),
    (
        flow2,
        "02",
        "Determine Root Cause",
        "Combine diagnostic signals with ranked evidence.",
    ),
    (
        flow3,
        "03",
        "Generate Investigation",
        "Use a local LLM to produce an evidence-grounded explanation.",
    ),
    (
        flow4,
        "04",
        "Verify Grounding",
        "Check citations, risky claims and factual grounding.",
    ),
]

for (
    column,
    number,
    title,
    description,
) in workflow:

    with column:

        st.markdown(
            f"""
            <div class="workflow-card">
                <div class="workflow-number">{number}</div>
                <div class="workflow-name">{title}</div>
                <div class="muted">{description}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# SESSION STATE
# ============================================================

if (
    "investigation_result"
    not in st.session_state
):

    st.session_state.investigation_result = None

if (
    "investigation_id"
    not in st.session_state
):

    st.session_state.investigation_id = None


# ============================================================
# RUN INVESTIGATION
# ============================================================

if investigate_button:

    if not query.strip():

        st.warning(
            "Please enter an investigation question."
        )

        st.stop()

    with st.spinner(
        "Investigating incident using retrieved evidence..."
    ):

        try:

            result = investigation_service.investigate(
                query=query.strip(),
                top_k=top_k,
                incident_id=incident_id,
            )

            # InvestigationService owns persistence and returns the
            # generated investigation ID with the completed result.
            st.session_state.investigation_result = result

            st.session_state.investigation_id = (
                result.get("investigation_id")
            )

            st.success(
                "Investigation completed and saved to history."
            )

        except Exception as error:

            st.error(
                "Investigation failed."
            )

            st.exception(error)

            st.stop()


# ============================================================
# GET RESULT
# ============================================================

result = (
    st.session_state.investigation_result
)

if result is None:

    st.divider()

    st.info(
        "Upload or select an incident, enter an "
        "investigation question, and click "
        "**Investigate Incident**."
    )

    st.stop()


# ============================================================
# EXTRACT RESULT DATA
# ============================================================

root_cause_details = result.get(
    "root_cause_details",
    result.get(
        "root_cause",
        {},
    ),
)

root_cause = root_cause_details.get(
    "root_cause",
    "Unknown",
)

root_confidence = root_cause_details.get(
    "confidence",
    result.get(
        "root_cause_confidence",
        "LOW",
    ),
)

evidence_confidence = result.get(
    "evidence_confidence",
    {},
)

evidence_confidence_level = (
    evidence_confidence.get(
        "confidence",
        evidence_confidence.get(
            "level",
            "LOW",
        ),
    )
)

evidence_confidence_score = (
    evidence_confidence.get(
        "score",
        0.0,
    )
)

groundedness = result.get(
    "groundedness",
    {},
)

groundedness_level = groundedness.get(
    "level",
    "LOW",
)

groundedness_score = groundedness.get(
    "score",
    0.0,
)

evidence = result.get(
    "evidence",
    [],
)

historical_incidents = result.get(
    "historical_incidents",
    [],
)

citation_repair = result.get(
    "citation_repair",
    {},
)

citation_verification = result.get(
    "citation_verification",
    {},
)

claim_verification = result.get(
    "claim_verification",
    {},
)


# ============================================================
# RESULT HEADER
# ============================================================

st.divider()

st.markdown("## Investigation Result")

result_incident = result.get(
    "incident_id",
    incident_id,
)

result_query = result.get(
    "query",
    query,
)

st.caption(
    f"Incident: `{result_incident}`  ·  "
    f"Evidence retrieved: {len(evidence)}"
)

with st.container(border=True):

    st.markdown(
        f"**Investigation question:** {result_query}"
    )


# ============================================================
# INCIDENT OVERVIEW
# ============================================================

st.markdown("### 1 · Incident Overview")

overview_col1, overview_col2, overview_col3, overview_col4 = (
    st.columns(4)
)

with overview_col1:

    st.metric(
        "Incident",
        result_incident,
    )

with overview_col2:

    st.metric(
        "Evidence Items",
        len(evidence),
    )

with overview_col3:

    st.metric(
        "RCA Confidence",
        confidence_badge(
            root_confidence
        ),
    )

with overview_col4:

    st.metric(
        "Groundedness",
        f"{groundedness_level} "
        f"({groundedness_score:.2f})",
    )


# ============================================================
# ROOT CAUSE ANALYSIS
# ============================================================

st.markdown("### 2 · Root Cause Analysis")

with st.container(border=True):

    st.markdown(
        '<div class="rca-label">'
        'Probable Root Cause'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="rca-value">'
        f'{root_cause}'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"**RCA Confidence:** "
        f"{confidence_badge(root_confidence)}"
    )

    if root_confidence == "LOW":

        st.caption(
            "LOW confidence does not mean the root cause "
            "is incorrect. It indicates that the available "
            "diagnostic evidence is limited in strength or "
            "source diversity."
        )

    elif root_confidence == "MEDIUM":

        st.caption(
            "The diagnosis is supported, but additional "
            "independent evidence would strengthen confidence."
        )

    else:

        st.caption(
            "The diagnosis has strong support from the "
            "available evidence."
        )

    st.caption(
        f"Evidence confidence: "
        f"{evidence_confidence_level} "
        f"({evidence_confidence_score:.2f})"
    )


# ============================================================
# AI INVESTIGATION
# ============================================================

st.markdown("### 3 · AI Investigation")

analysis = result.get(
    "analysis",
    "",
)

with st.container(border=True):

    if analysis.strip():

        st.markdown(
            analysis
        )

    else:

        st.info(
            "No AI investigation narrative was returned."
        )


# ============================================================
# EVIDENCE
# ============================================================

st.markdown("### 4 · Evidence")

st.markdown(
    '<div class="section-caption">'
    'Ranked evidence retrieved from the selected incident.'
    '</div>',
    unsafe_allow_html=True,
)

if not evidence:

    st.info(
        "No evidence items were retrieved."
    )

else:

    for index, raw_item in enumerate(
        evidence,
        start=1,
    ):

        item = format_evidence(
            raw_item
        )

        citation = (
            f"[{item['source_file']}:"
            f"{item['location']}]"
        )

        with st.container(
            border=True
        ):

            evidence_col1, evidence_col2 = (
                st.columns(
                    [5.5, 1],
                    gap="large",
                )
            )

            with evidence_col1:

                st.markdown(
                    f"**{index}. {item['text']}**"
                )

                st.markdown(
                    f'<span class="citation">'
                    f'{citation}'
                    f'</span>',
                    unsafe_allow_html=True,
                )

                st.caption(
                    f"Source: {item['source_type']} "
                    f"· Provenance: {item['provenance']}"
                )

            with evidence_col2:

                st.metric(
                    "Score",
                    f"{item['score']:.3f}",
                )


# ============================================================
# VERIFICATION
# ============================================================

st.markdown("### 5 · Verification")

verification_col1, verification_col2 = (
    st.columns(
        2,
        gap="large",
    )
)


# ------------------------------------------------------------
# GROUNDEDNESS
# ------------------------------------------------------------

with verification_col1:

    with st.container(
        border=True
    ):

        st.markdown(
            "#### 🛡️ Groundedness"
        )

        grounded_status = groundedness.get(
            "status",
            "FAIL",
        )

        st.markdown(
            status_badge(
                grounded_status
            ),
            unsafe_allow_html=True,
        )

        metric_col1, metric_col2 = (
            st.columns(2)
        )

        with metric_col1:

            st.metric(
                "Score",
                f"{groundedness_score:.2f}",
            )

        with metric_col2:

            st.metric(
                "Claims",
                groundedness.get(
                    "total_claims",
                    0,
                ),
            )

        grounded_count = groundedness.get(
            "grounded_claims",
            0,
        )

        ungrounded_count = groundedness.get(
            "ungrounded_claims",
            0,
        )

        st.write(
            f"Grounded claims: **{grounded_count}**"
        )

        st.write(
            f"Ungrounded claims: **{ungrounded_count}**"
        )

        if groundedness.get(
            "ungrounded_lines"
        ):

            with st.expander(
                "View ungrounded statements"
            ):

                for claim in groundedness[
                    "ungrounded_lines"
                ]:

                    st.warning(
                        f"Line {claim.get('line_number')}: "
                        f"{claim.get('text')}"
                    )


# ------------------------------------------------------------
# CITATION + CLAIM VERIFICATION
# ------------------------------------------------------------

with verification_col2:

    with st.container(
        border=True
    ):

        st.markdown(
            "#### 🔐 Citation & Claim Verification"
        )

        # ----------------------------------------------------
        # Citation verification
        # ----------------------------------------------------

        citation_status = (
            citation_verification.get(
                "status",
                "FAIL",
            )
        )

        st.write(
            "**Citation Verification**"
        )

        st.markdown(
            status_badge(
                citation_status
            ),
            unsafe_allow_html=True,
        )

        citation_col1, citation_col2 = (
            st.columns(2)
        )

        with citation_col1:

            st.metric(
                "Verified",
                citation_verification.get(
                    "verified_citations",
                    0,
                ),
            )

        with citation_col2:

            st.metric(
                "Total",
                citation_verification.get(
                    "total_citations",
                    0,
                ),
            )

        citation_coverage = (
            citation_verification.get(
                "citation_coverage",
                0.0,
            )
        )

        st.caption(
            f"Citation coverage: "
            f"{citation_coverage:.2f}"
        )

        st.divider()

        # ----------------------------------------------------
        # Claim verification
        # ----------------------------------------------------

        claim_status = (
            claim_verification.get(
                "status",
                (
                    "REVIEW"
                    if claim_verification.get(
                        "has_unsupported_claims",
                        False,
                    )
                    else "PASS"
                ),
            )
        )

        st.write(
            "**Claim Verification**"
        )

        st.markdown(
            status_badge(
                claim_status
            ),
            unsafe_allow_html=True,
        )

        checked_claims = (
            claim_verification.get(
                "checked_claims",
                claim_verification.get(
                    "total_claims",
                    0,
                ),
            )
        )

        supported_claims = (
            claim_verification.get(
                "supported_count",
                0,
            )
        )

        unsupported_claims = (
            claim_verification.get(
                "unsupported_count",
                0,
            )
        )

        if checked_claims == 0:

            st.metric(
                "Risky Claims Checked",
                "0",
            )

            st.success(
                "No risky claims detected."
            )

        else:

            claim_coverage = (
                claim_verification.get(
                    "claim_coverage"
                )
            )

            if claim_coverage is not None:

                st.metric(
                    "Claim Coverage",
                    f"{claim_coverage:.2f}",
                )

            st.write(
                f"Supported claims: "
                f"**{supported_claims}**"
            )

            st.write(
                f"Unsupported claims: "
                f"**{unsupported_claims}**"
            )

            if claim_verification.get(
                "unsupported_claims"
            ):

                with st.expander(
                    "View unsupported claims"
                ):

                    for claim in (
                        claim_verification[
                            "unsupported_claims"
                        ]
                    ):

                        st.warning(
                            claim.get(
                                "claim",
                                str(claim),
                            )
                        )


# ============================================================
# CITATION REPAIR
# ============================================================

st.markdown(
    "### 6 · Citation Grounding"
)

repair_count = citation_repair.get(
    "repair_count",
    0,
)

repairs = citation_repair.get(
    "repairs",
    [],
)

if repair_count == 0:

    st.success(
        "No citation repairs were required."
    )

else:

    st.info(
        f"TraceAI automatically applied "
        f"**{repair_count} citation repair(s)** "
        f"against the current incident evidence."
    )

    with st.expander(
        f"View {repair_count} citation repair(s)"
    ):

        for repair in repairs:

            repair_type = repair.get(
                "type",
                "unknown",
            )

            original = repair.get(
                "original"
            )

            replacement = repair.get(
                "replacement",
                "",
            )

            similarity = repair.get(
                "similarity",
                0.0,
            )

            evidence_text = repair.get(
                "evidence",
                "",
            )

            if (
                repair_type
                == "invalid_citation_repair"
            ):

                st.markdown(
                    f"""
                    **Invalid citation repaired**

                    `{original}` → `{replacement}`

                    Similarity: **{similarity:.3f}**

                    Evidence: {evidence_text}
                    """
                )

            elif (
                repair_type
                == "missing_citation_added"
            ):

                st.markdown(
                    f"""
                    **Missing citation added**

                    Added: `{replacement}`

                    Similarity: **{similarity:.3f}**

                    Evidence: {evidence_text}
                    """
                )


# ============================================================
# HISTORICAL CONTEXT
# ============================================================

st.markdown(
    "### 7 · Historical Context"
)

with st.expander(
    "🕘 Similar Historical Incidents — Reference Only"
):

    st.caption(
        "Historical matches provide context only. "
        "They are not treated as primary evidence "
        "for the current incident."
    )

    if not historical_incidents:

        st.info(
            "No similar historical incidents were found."
        )

    else:

        for match in historical_incidents:

            historical_id = match.get(
                "incident_id",
                "unknown",
            )

            similarity = match.get(
                "similarity",
                0.0,
            )

            st.markdown(
                f"**{historical_id}**  \n"
                f"Similarity: `{similarity:.3f}`"
            )

            st.divider()


# ============================================================
# INVESTIGATION HISTORY
# ============================================================

st.markdown("### 8 · Investigation History")

history_records = investigation_service.list_investigations(
    limit=25
)

with st.container(border=True):

    st.caption(
        "Previously completed TraceAI investigations "
        "stored locally in SQLite."
    )

    if not history_records:

        st.info(
            "No saved investigations yet."
        )

    else:

        for record in history_records:

            record_id = record.get(
                "investigation_id",
                "unknown",
            )

            record_incident = record.get(
                "incident_id",
                "unknown",
            )

            record_root_cause = record.get(
                "root_cause",
                "Unknown",
            )

            record_confidence = record.get(
                "confidence",
                "UNKNOWN",
            )

            record_score = record.get(
                "confidence_score"
            )

            record_created = record.get(
                "created_at",
                "unknown",
            )

            with st.expander(
                f"{record_root_cause} · "
                f"{record_incident} · "
                f"{record_confidence}"
            ):

                history_col1, history_col2, history_col3 = (
                    st.columns(3)
                )

                with history_col1:

                    st.write(
                        f"**Incident:** "
                        f"`{record_incident}`"
                    )

                    st.write(
                        f"**Confidence:** "
                        f"{confidence_badge(record_confidence)}"
                    )

                with history_col2:

                    if record_score is not None:

                        st.write(
                            f"**Support Score:** "
                            f"`{float(record_score):.2f}`"
                        )

                    st.write(
                        f"**Groundedness:** "
                        f"`{float(record.get('groundedness_score', 0.0)):.2f}`"
                    )

                with history_col3:

                    st.write(
                        f"**Citation Coverage:** "
                        f"`{float(record.get('citation_coverage', 0.0)):.2f}`"
                    )

                    st.write(
                        f"**Created:** "
                        f"`{record_created}`"
                    )

                st.markdown(
                    "**Investigation Question**"
                )

                st.write(
                    record.get(
                        "query",
                        "",
                    )
                )

                if record.get("analysis"):

                    with st.expander(
                        "View saved AI investigation"
                    ):

                        st.markdown(
                            record["analysis"]
                        )

                if st.button(
                    "Delete this investigation",
                    key=f"delete_{record_id}",
                ):

                    deleted = (
                        investigation_service.delete_investigation(
                            record_id
                        )
                    )

                    if deleted:

                        if (
                            st.session_state.get(
                                "investigation_id"
                            )
                            == record_id
                        ):
                            st.session_state.investigation_result = None
                            st.session_state.investigation_id = None

                        st.rerun()


# ============================================================
# TECHNICAL DETAILS
# ============================================================

with st.expander(
    "🔧 Technical Investigation Details"
):

    st.caption(
        "Developer-level diagnostic output. "
        "This section exposes the internal investigation "
        "objects, scores and verification results."
    )

    st.json(
        {
            "investigation_id": result.get(
                "investigation_id"
            ),
            "query": result.get(
                "query"
            ),
            "incident_id": result.get(
                "incident_id"
            ),
            "root_cause": root_cause_details,
            "evidence_confidence": evidence_confidence,
            "groundedness": groundedness,
            "citation_repair": citation_repair,
            "citation_verification": citation_verification,
            "claim_verification": claim_verification,
        }
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "TraceAI • Evidence-Grounded GenAI Incident Investigation "
    "• Local inference • Open-source stack"
)