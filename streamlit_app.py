import streamlit as st
import pandas as pd
import json
import re
from snowflake.snowpark.context import get_active_session

st.set_page_config(
    page_title="Event Harmonization Engine",
    page_icon=":material/sensors:",
    layout="wide",
)

session = get_active_session()
DB = "PATIENTPOINT_DEMO"
SCHEMA = "EVENT_HARMONIZATION"

def fq(table):
    return f"{DB}.{SCHEMA}.{table}"

def run_query(sql, **kwargs):
    return session.sql(sql).to_pandas()

def run_sql(sql):
    session.sql(sql).collect()

def unwrap_ai_response(raw):
    try:
        decoded = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        decoded = raw
    if isinstance(decoded, list):
        return decoded
    if isinstance(decoded, str):
        raw = decoded
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip()
    start = raw.index("[")
    end = raw.rindex("]") + 1
    return json.loads(raw[start:end])

def get_config(key, default=""):
    try:
        r = run_query(f"SELECT CONFIG_VALUE FROM {fq('PIPELINE_CONFIG')} WHERE CONFIG_KEY = '{key}'")
        if not r.empty:
            return r["CONFIG_VALUE"].iloc[0]
    except:
        pass
    return default

def set_config(key, value):
    run_sql(
        f"UPDATE {fq('PIPELINE_CONFIG')} SET CONFIG_VALUE = $${value}$$, "
        f"UPDATED_AT = CURRENT_TIMESTAMP() WHERE CONFIG_KEY = '{key}'"
    )


# ─── Load config ───
AUTO_APPROVE_THRESHOLD = float(get_config("AUTO_APPROVE_THRESHOLD", "0.85"))
HUMAN_REVIEW_THRESHOLD = float(get_config("HUMAN_REVIEW_THRESHOLD", "0.70"))
QUALITY_THRESHOLD = float(get_config("QUALITY_THRESHOLD", "0.7"))
CLASSIFICATION_MODEL = get_config("CLASSIFICATION_MODEL", "claude-sonnet-4-6")
RATIONALE_MODEL = get_config("RATIONALE_MODEL", "claude-sonnet-4-6")
PROFILING_MODEL = get_config("PROFILING_MODEL", "llama3.1-8b")

# ─── Source definitions ───
SOURCES = {
    "Waiting Room Displays": {
        "table": "RAW_WAITING_ROOM_EVENTS",
        "system": "waiting_room_displays",
        "description": "Proof of play, ad impressions on lobby/waiting room screens",
    },
    "iXR Interactive Devices": {
        "table": "RAW_IXR_EVENTS",
        "system": "ixr_interactive",
        "description": "Touch interactions, link sends on exam room kiosks",
    },
    "Programmatic Ad Platform": {
        "table": "RAW_PROGRAMMATIC_EVENTS",
        "system": "programmatic_platform",
        "description": "Bid requests, impressions, clicks, conversions in the ad exchange",
    },
    "Mobile Check-in App": {
        "table": "RAW_MOBILE_CHECKIN_EVENTS",
        "system": "mobile_checkin",
        "description": "Patient check-in, form submissions, notifications",
    },
    "Provider Portal": {
        "table": "RAW_PROVIDER_PORTAL_EVENTS",
        "system": "provider_portal",
        "description": "Provider login, page views, search, content activation",
    },
}

system_to_name = {v["system"]: k for k, v in SOURCES.items()}

st.title("AI-Driven Event Schema Harmonization")
st.caption("Forensic Analysis | Data Profiling | Field Mapping | Pipeline Generation")

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Architecture",
    "Source Discovery",
    "Data Profiling",
    "AI Mapping & Review",
    "Compounding Value",
    "Pipeline Builder",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 0: ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════════════
with tab0:
    st.header("Pipeline architecture")
    st.markdown("""
End-to-end flow: from raw event ingestion through quality profiling to a unified gold layer.

**RAW** (landing) → **SILVER** (profiled + quality-scored) → **GOLD** (unified canonical schema)
""")

    st.markdown("""
<style>
.arch-box {
    border: 2px solid #444;
    border-radius: 12px;
    padding: 18px 14px 12px;
    text-align: center;
    min-height: 130px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.arch-box h4 { margin: 0 0 6px; }
.arch-box p  { margin: 0; font-size: 0.85em; opacity: 0.85; }
.arch-bronze  { border-color: #cd7f32; background: rgba(205,127,50,0.08); }
.arch-silver  { border-color: #c0c0c0; background: rgba(192,192,192,0.08); }
.arch-ai      { border-color: #29b5e8; background: rgba(41,181,232,0.08); }
.arch-router  { border-color: #ff9f43; background: rgba(255,159,67,0.08); }
.arch-mdr     { border-color: #2ecc71; background: rgba(46,204,113,0.08); }
.arch-gold    { border-color: #f1c40f; background: rgba(241,196,15,0.08); }
.arch-arrow { text-align: center; font-size: 2em; line-height: 130px; color: #888; }
</style>
""", unsafe_allow_html=True)

    st.subheader("RAW > Profile > Classify > Map > MDR > Pipeline")

    cols = st.columns([2, 0.3, 2, 0.3, 2, 0.3, 2, 0.3, 2, 0.3, 2])

    with cols[0]:
        st.markdown("""<div class="arch-box arch-bronze">
<h4>RAW (VARIANT)</h4>
<p>5 products, 5 schemas<br/>JSON ingested as-is</p>
</div>""", unsafe_allow_html=True)
    with cols[1]:
        st.markdown('<div class="arch-arrow">&rarr;</div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown("""<div class="arch-box arch-silver">
<h4>Data Profiling</h4>
<p>SQL stats + AI quality assessment<br/>Null rates, type checks, anomalies</p>
</div>""", unsafe_allow_html=True)
    with cols[3]:
        st.markdown('<div class="arch-arrow">&rarr;</div>', unsafe_allow_html=True)
    with cols[4]:
        st.markdown("""<div class="arch-box arch-ai">
<h4>AI Classification</h4>
<p><code>AI_COMPLETE</code> classifies fields<br/>+ Embedding match to canonical</p>
</div>""", unsafe_allow_html=True)
    with cols[5]:
        st.markdown('<div class="arch-arrow">&rarr;</div>', unsafe_allow_html=True)
    with cols[6]:
        st.markdown("""<div class="arch-box arch-router">
<h4>Confidence Router</h4>
<p>&gt;0.85: Auto-approve<br/>0.70-0.85: Human review<br/>&lt;0.70: Novel field</p>
</div>""", unsafe_allow_html=True)
    with cols[7]:
        st.markdown('<div class="arch-arrow">&rarr;</div>', unsafe_allow_html=True)
    with cols[8]:
        st.markdown("""<div class="arch-box arch-mdr">
<h4>MDR</h4>
<p>Mapping Data Repository<br/>Compounding institutional memory</p>
</div>""", unsafe_allow_html=True)
    with cols[9]:
        st.markdown('<div class="arch-arrow">&rarr;</div>', unsafe_allow_html=True)
    with cols[10]:
        st.markdown("""<div class="arch-box arch-gold">
<h4>GOLD (Dynamic Table)</h4>
<p>Unified event schema<br/>Auto-refreshing pipeline</p>
</div>""", unsafe_allow_html=True)

    st.divider()

    st.subheader("Technology stack")
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.markdown("**Data platform**")
        st.code("Snowflake", language=None)
        st.caption("Single platform for raw data, embeddings, MDR, and app runtime")
    with t2:
        st.markdown("**AI / LLM**")
        st.code(f"AI_COMPLETE\n{CLASSIFICATION_MODEL}", language=None)
        st.caption("Field classification + mapping rationale")
    with t3:
        st.markdown("**Embeddings**")
        st.code("AI_EMBED\ne5-base-v2", language=None)
        st.caption("Semantic similarity matching")
    with t4:
        st.markdown("**Pipeline**")
        st.code("Dynamic Tables\nTARGET_LAG", language=None)
        st.caption("Auto-refreshing Silver and Gold layers")

    # ─── Settings summary ───
    st.divider()
    st.subheader("Active settings")
    st.markdown(
        f"**Classification model:** `{CLASSIFICATION_MODEL}` | "
        f"**Profiling model:** `{PROFILING_MODEL}` | "
        f"**Auto-approve:** >{AUTO_APPROVE_THRESHOLD} | "
        f"**Human review:** {HUMAN_REVIEW_THRESHOLD}–{AUTO_APPROVE_THRESHOLD} | "
        f"**Quality threshold:** {QUALITY_THRESHOLD}"
    )
    st.caption("Prompts are editable inline on each tab, directly above the action button. Settings stored in PIPELINE_CONFIG table.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: SOURCE DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("Source forensic analysis")
    st.markdown("AI scans raw event JSON and classifies each field into a canonical event concept.")

    selected_source = st.selectbox("Select an event source to analyze", list(SOURCES.keys()), key="disc_source")
    source = SOURCES[selected_source]

    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(f"**{selected_source}**")
        st.caption(source["description"])
        st.markdown(f"Table: `{source['table']}`")
    with col2:
        preview = run_query(f"SELECT RAW FROM {fq(source['table'])} LIMIT 3")
        st.markdown("**Raw JSON preview:**")
        for _, row in preview.iterrows():
            st.json(json.loads(row["RAW"]) if isinstance(row["RAW"], str) else row["RAW"])

    # ─── Editable prompt (above the button) ───
    with st.expander("Classification prompt (edit before running)"):
        st.caption("Variables `{source_name}` and `{field_list_json}` are auto-filled at runtime.")
        class_prompt_val = get_config("PROMPT_CLASSIFICATION", "")
        edited_class_prompt = st.text_area(
            "Prompt template", value=class_prompt_val, height=200, key="edit_class_prompt"
        )
        if edited_class_prompt != class_prompt_val:
            if st.button("Save changes", key="save_class_prompt"):
                set_config("PROMPT_CLASSIFICATION", edited_class_prompt)
                st.success("Classification prompt updated.")
                st.rerun()

    if st.button("Run AI field classification", type="primary", key="classify_btn"):
        with st.spinner("Classifying fields with Cortex AI..."):
            keys_df = run_query(
                f"SELECT DISTINCT f.key AS FIELD_NAME "
                f"FROM {fq(source['table'])}, LATERAL FLATTEN(input => RAW) f "
                f"ORDER BY f.key"
            )

            sample_vals = {}
            for field in keys_df["FIELD_NAME"]:
                sv = run_query(
                    f"SELECT DISTINCT RAW:{field}::VARCHAR AS V "
                    f"FROM {fq(source['table'])} "
                    f"WHERE RAW:{field} IS NOT NULL LIMIT 5"
                )
                sample_vals[field] = ", ".join(sv["V"].dropna().astype(str).tolist()[:5])

            field_list = [{"field": f, "samples": sample_vals.get(f, "")} for f in keys_df["FIELD_NAME"]]

            prompt_template = get_config("PROMPT_CLASSIFICATION", "")
            prompt = prompt_template.replace("{source_name}", selected_source).replace(
                "{field_list_json}", json.dumps(field_list, indent=2)
            )

            result = run_query(
                f"SELECT AI_COMPLETE('{CLASSIFICATION_MODEL}', $${prompt}$$) AS RESPONSE"
            )
            response_text = result["RESPONSE"].iloc[0]

            try:
                classifications = unwrap_ai_response(response_text)
            except (ValueError, json.JSONDecodeError):
                st.error("Failed to parse AI response:")
                st.code(response_text)
                classifications = []

            if classifications:
                run_sql(f"DELETE FROM {fq('SOURCE_TYPE_CATALOG')} WHERE SOURCE_SYSTEM = '{source['system']}'")

                for c in classifications:
                    sv = sample_vals.get(c["field"], "").replace("'", "''")
                    concept = c.get("event_concept", "").replace("'", "''")
                    run_sql(
                        f"INSERT INTO {fq('SOURCE_TYPE_CATALOG')} "
                        f"(SOURCE_SYSTEM, FIELD_NAME, INFERRED_DATA_TYPE, SAMPLE_VALUES, "
                        f"AI_FIELD_CLASSIFICATION, AI_EVENT_CONCEPT, CONFIDENCE_SCORE) "
                        f"VALUES ('{source['system']}', '{c['field']}', 'VARIANT', "
                        f"$${sv}$$, '{c['classification']}', $${concept}$$, {c['confidence']})"
                    )

                st.success(f"Cataloged {len(classifications)} fields from {selected_source}")

    catalog = run_query(
        f"SELECT * FROM {fq('SOURCE_TYPE_CATALOG')} WHERE SOURCE_SYSTEM = '{source['system']}' ORDER BY CONFIDENCE_SCORE DESC"
    )
    if not catalog.empty:
        st.subheader("Field classification results")
        st.dataframe(
            catalog[["FIELD_NAME", "AI_FIELD_CLASSIFICATION", "AI_EVENT_CONCEPT", "CONFIDENCE_SCORE"]],
            use_container_width=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: DATA PROFILING
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("Data profiling & quality assessment")
    st.markdown("Structural analysis + AI-driven quality checks. Identifies issues *before* mapping.")

    prof_source = st.selectbox("Select source to profile", list(SOURCES.keys()), key="prof_source")
    psrc = SOURCES[prof_source]

    # ─── Structural profiling (pure SQL) ───
    st.subheader("Structural profile (SQL-based, zero AI cost)")

    struct_query = f"""
    SELECT
        f.key AS FIELD_NAME,
        COUNT(*) AS TOTAL_EVENTS,
        COUNT(CASE WHEN f.value IS NULL OR f.value::VARCHAR = 'null' THEN 1 END) AS NULL_COUNT,
        ROUND(COUNT(CASE WHEN f.value IS NULL OR f.value::VARCHAR = 'null' THEN 1 END) * 100.0 / COUNT(*), 1) AS NULL_PCT,
        COUNT(DISTINCT f.value::VARCHAR) AS DISTINCT_VALUES,
        MIN(f.value::VARCHAR) AS MIN_VALUE,
        MAX(f.value::VARCHAR) AS MAX_VALUE
    FROM {fq(psrc['table'])}, LATERAL FLATTEN(input => RAW) f
    GROUP BY f.key
    ORDER BY NULL_PCT DESC, f.key
    """

    struct_df = run_query(struct_query)
    if not struct_df.empty:
        st.dataframe(struct_df, use_container_width=True)

        # Summary metrics
        total_fields = len(struct_df)
        fields_with_nulls = len(struct_df[struct_df["NULL_PCT"] > 0])
        avg_null_rate = struct_df["NULL_PCT"].mean()
        st.markdown(
            f"**Summary:** {total_fields} fields | "
            f"{fields_with_nulls} with nulls | "
            f"Avg null rate: {avg_null_rate:.1f}%"
        )

    # ─── AI-driven quality assessment ───
    st.subheader(f"AI quality assessment (model: `{PROFILING_MODEL}`)")

    with st.expander("Profiling prompt (edit before running)"):
        st.caption("Variables `{source_name}`, `{total_count}`, `{events_json}` are auto-filled at runtime.")
        prof_prompt_val = get_config("PROMPT_PROFILING", "")
        edited_prof_prompt = st.text_area(
            "Prompt template", value=prof_prompt_val, height=200, key="edit_prof_prompt"
        )
        if edited_prof_prompt != prof_prompt_val:
            if st.button("Save changes", key="save_prof_prompt"):
                set_config("PROMPT_PROFILING", edited_prof_prompt)
                st.success("Profiling prompt updated.")
                st.rerun()

    if st.button("Run AI quality profiling", type="primary", key="profile_btn"):
        with st.spinner(f"Analyzing data quality with {PROFILING_MODEL}..."):
            events_df = run_query(f"SELECT RAW::VARCHAR AS EVENT FROM {fq(psrc['table'])} LIMIT 10")
            events_list = events_df["EVENT"].tolist()
            total_count = run_query(f"SELECT COUNT(*) AS CNT FROM {fq(psrc['table'])}")["CNT"].iloc[0]

            prompt_template = get_config("PROMPT_PROFILING", "")
            prompt = prompt_template.replace("{source_name}", prof_source).replace(
                "{total_count}", str(total_count)
            ).replace("{events_json}", json.dumps(events_list[:10], indent=2))

            result = run_query(
                f"SELECT AI_COMPLETE('{PROFILING_MODEL}', $${prompt}$$) AS RESPONSE"
            )
            response_text = result["RESPONSE"].iloc[0]

            try:
                issues = unwrap_ai_response(response_text)
            except (ValueError, json.JSONDecodeError):
                st.warning("No structured issues found or parse error.")
                st.code(str(response_text)[:2000])
                issues = []

            if issues:
                st.markdown(f"**Found {len(issues)} quality issue(s):**")
                for issue in issues:
                    severity = issue.get("severity", "medium")
                    if severity == "high":
                        sev_color = "red"
                    elif severity == "medium":
                        sev_color = "orange"
                    else:
                        sev_color = "gray"
                    st.markdown(
                        f"- **[{severity.upper()}]** `{issue.get('field', '?')}` — "
                        f"{issue.get('description', 'No description')} "
                        f"(type: {issue.get('issue_type', '?')})"
                    )
            else:
                st.success("No quality issues detected by AI.")

    # ─── Cross-source comparison ───
    st.divider()
    st.subheader("Cross-source field comparison")
    st.markdown("After classifying multiple sources, this matrix shows how the same concepts get different names.")

    all_catalog = run_query(f"SELECT * FROM {fq('SOURCE_TYPE_CATALOG')}")
    if all_catalog.empty:
        st.info("Run Source Discovery on at least 2 sources to see the comparison matrix.")
    else:
        # Pivot: rows = classification, columns = source system
        pivot_data = all_catalog.pivot_table(
            index="AI_FIELD_CLASSIFICATION",
            columns="SOURCE_SYSTEM",
            values="FIELD_NAME",
            aggfunc=lambda x: ", ".join(x),
        ).fillna("—")

        # Rename columns to friendly names
        pivot_data.columns = [system_to_name.get(c, c) for c in pivot_data.columns]
        st.dataframe(pivot_data, use_container_width=True)
        st.caption("Same row = same concept. Different column values = the schema divergence problem.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: AI MAPPING & REVIEW
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("AI mapping suggestions")
    st.markdown(
        f"**Auto-approve** at >{AUTO_APPROVE_THRESHOLD:.0%} | "
        f"**Human review** at {HUMAN_REVIEW_THRESHOLD:.0%}–{AUTO_APPROVE_THRESHOLD:.0%} | "
        f"**Novel** below {HUMAN_REVIEW_THRESHOLD:.0%}"
    )

    catalog_data = run_query(f"SELECT DISTINCT SOURCE_SYSTEM FROM {fq('SOURCE_TYPE_CATALOG')}")
    if catalog_data.empty:
        st.info("Run Source Discovery first to populate the catalog.")
    else:
        system_opts = catalog_data["SOURCE_SYSTEM"].tolist()
        display_opts = [system_to_name.get(s, s) for s in system_opts]
        map_source_display = st.selectbox("Source to map", display_opts, key="map_source")
        map_source_system = system_opts[display_opts.index(map_source_display)]

        with st.expander("Rationale prompt (edit before running)"):
            st.caption("Variables `{field_name}`, `{source_name}`, `{event_concept}`, `{candidates_json}` are auto-filled per field.")
            rat_prompt_val = get_config("PROMPT_RATIONALE", "")
            edited_rat_prompt = st.text_area(
                "Prompt template", value=rat_prompt_val, height=120, key="edit_rat_prompt"
            )
            if edited_rat_prompt != rat_prompt_val:
                if st.button("Save changes", key="save_rat_prompt"):
                    set_config("PROMPT_RATIONALE", edited_rat_prompt)
                    st.success("Rationale prompt updated.")
                    st.rerun()

        if st.button("Generate mapping suggestions", type="primary", key="map_btn"):
            with st.spinner("Computing semantic similarity with Cortex embeddings..."):
                catalog_fields = run_query(
                    f"SELECT FIELD_NAME, AI_FIELD_CLASSIFICATION, AI_EVENT_CONCEPT "
                    f"FROM {fq('SOURCE_TYPE_CATALOG')} "
                    f"WHERE SOURCE_SYSTEM = '{map_source_system}'"
                )

                mdr_data = run_query(f"SELECT * FROM {fq('MDR')}")
                run_sql(f"DELETE FROM {fq('MAPPING_SUGGESTIONS')} WHERE SOURCE_SYSTEM = '{map_source_system}'")

                mdr_lookup = {}
                if not mdr_data.empty:
                    for _, m in mdr_data.iterrows():
                        key = m["TARGET_VARIABLE"]
                        if key not in mdr_lookup:
                            mdr_lookup[key] = m

                auto_count = 0
                pending_count = 0
                novel_count = 0
                mdr_hit_count = 0

                for _, field in catalog_fields.iterrows():
                    field_name = field["FIELD_NAME"]
                    event_concept = field["AI_EVENT_CONCEPT"]

                    embed_text = f"{field_name} | {event_concept}"
                    top_matches = run_query(
                        f"SELECT VARIABLE_NAME, VARIABLE_LABEL, VARIABLE_DESCRIPTION, "
                        f"VECTOR_COSINE_SIMILARITY(EMBEDDING, "
                        f"AI_EMBED('e5-base-v2', $${embed_text}$$)) AS SCORE "
                        f"FROM {fq('EVENT_VARIABLE_EMBEDDINGS')} "
                        f"ORDER BY SCORE DESC LIMIT 3"
                    )

                    if top_matches.empty:
                        continue

                    best = top_matches.iloc[0]
                    score = float(best["SCORE"])

                    # MDR reuse check
                    if best["VARIABLE_NAME"] in mdr_lookup and score >= HUMAN_REVIEW_THRESHOLD:
                        mdr_entry = mdr_lookup[best["VARIABLE_NAME"]]
                        if mdr_entry["SOURCE_ORIGIN"] != map_source_system:
                            run_sql(
                                f"INSERT INTO {fq('MAPPING_SUGGESTIONS')} "
                                f"(SOURCE_SYSTEM, SOURCE_FIELD, TARGET_VARIABLE, TARGET_LABEL, "
                                f"SIMILARITY_SCORE, AI_RATIONALE, STATUS) VALUES "
                                f"('{map_source_system}', '{field_name}', "
                                f"'{best['VARIABLE_NAME']}', $${best['VARIABLE_LABEL']}$$, "
                                f"0.99, 'MDR reuse from {mdr_entry['SOURCE_ORIGIN']}', 'MDR_MATCH')"
                            )
                            run_sql(
                                f"UPDATE {fq('MDR')} SET TIMES_REUSED = TIMES_REUSED + 1 "
                                f"WHERE TARGET_VARIABLE = '{best['VARIABLE_NAME']}'"
                            )
                            mdr_hit_count += 1
                            continue

                    # Confidence routing
                    if score >= AUTO_APPROVE_THRESHOLD:
                        status = "AUTO_APPROVED"
                        auto_count += 1
                    elif score >= HUMAN_REVIEW_THRESHOLD:
                        status = "PENDING"
                        pending_count += 1
                    else:
                        status = "NOVEL"
                        novel_count += 1

                    # Rationale
                    candidates_json = json.dumps(top_matches.head(3).to_dict(orient="records"), default=str)
                    rationale_template = get_config("PROMPT_RATIONALE", "")
                    rationale_prompt = rationale_template.replace("{field_name}", field_name).replace(
                        "{source_name}", map_source_display
                    ).replace("{event_concept}", event_concept).replace("{candidates_json}", candidates_json)

                    rationale_result = run_query(
                        f"SELECT AI_COMPLETE('{RATIONALE_MODEL}', $${rationale_prompt}$$) AS R"
                    )
                    raw_rationale = rationale_result["R"].iloc[0]
                    try:
                        rationale = json.loads(raw_rationale)
                    except (json.JSONDecodeError, TypeError):
                        rationale = raw_rationale
                    if not isinstance(rationale, str):
                        rationale = str(rationale)
                    rationale_clean = rationale.replace("'", "''")

                    run_sql(
                        f"INSERT INTO {fq('MAPPING_SUGGESTIONS')} "
                        f"(SOURCE_SYSTEM, SOURCE_FIELD, TARGET_VARIABLE, TARGET_LABEL, "
                        f"SIMILARITY_SCORE, AI_RATIONALE, STATUS) VALUES "
                        f"('{map_source_system}', '{field_name}', "
                        f"'{best['VARIABLE_NAME']}', $${best['VARIABLE_LABEL']}$$, "
                        f"{score}, $${rationale_clean}$$, '{status}')"
                    )

                    # Auto-approve persists to MDR
                    if status == "AUTO_APPROVED":
                        concept_clean = event_concept.replace("'", "''")
                        run_sql(
                            f"MERGE INTO {fq('MDR')} t USING ("
                            f"SELECT '{field_name}' AS P, $${concept_clean}$$ AS C, "
                            f"'{best['VARIABLE_NAME']}' AS V, $${best['VARIABLE_LABEL']}$$ AS L, "
                            f"'{map_source_system}' AS S) s "
                            f"ON t.SOURCE_EVENT_CONCEPT = s.C AND t.TARGET_VARIABLE = s.V "
                            f"WHEN MATCHED THEN UPDATE SET TIMES_REUSED = t.TIMES_REUSED + 1 "
                            f"WHEN NOT MATCHED THEN INSERT "
                            f"(SOURCE_FIELD_PATTERN, SOURCE_EVENT_CONCEPT, TARGET_VARIABLE, "
                            f"TARGET_LABEL, APPROVED_BY, SOURCE_ORIGIN) "
                            f"VALUES (s.P, s.C, s.V, s.L, 'auto_approve', s.S)"
                        )

                st.success(
                    f"Done: {auto_count} auto-approved, {pending_count} pending, "
                    f"{novel_count} novel, {mdr_hit_count} MDR reuses"
                )

        # Display suggestions
        suggestions = run_query(
            f"SELECT * FROM {fq('MAPPING_SUGGESTIONS')} "
            f"WHERE SOURCE_SYSTEM = '{map_source_system}' "
            f"ORDER BY SIMILARITY_SCORE DESC"
        )

        if not suggestions.empty:
            st.subheader("Review queue")

            for idx, row in suggestions.iterrows():
                status = row["STATUS"]
                with st.container():
                    c1, c2, c3, c4 = st.columns([2, 2, 1, 2])
                    with c1:
                        st.markdown(f"**{row['SOURCE_FIELD']}**")
                        st.caption(f"Source: {map_source_display}")
                    with c2:
                        st.markdown(f"**{row['TARGET_VARIABLE']}**")
                        st.caption(row["TARGET_LABEL"])
                    with c3:
                        st.metric("Score", f"{row['SIMILARITY_SCORE']:.0%}")
                    with c4:
                        st.markdown(f"**`{status}`**")
                        if row["AI_RATIONALE"]:
                            st.caption(str(row["AI_RATIONALE"])[:200])

                    if status == "PENDING":
                        bc1, bc2, _ = st.columns([1, 1, 4])
                        with bc1:
                            if st.button("Approve", key=f"approve_{map_source_system}_{idx}", type="primary"):
                                run_sql(
                                    f"UPDATE {fq('MAPPING_SUGGESTIONS')} SET STATUS = 'APPROVED', "
                                    f"REVIEWED_BY = 'demo_reviewer', REVIEWED_AT = CURRENT_TIMESTAMP() "
                                    f"WHERE SOURCE_SYSTEM = '{map_source_system}' "
                                    f"AND SOURCE_FIELD = '{row['SOURCE_FIELD']}'"
                                )
                                concept_row = run_query(
                                    f"SELECT AI_EVENT_CONCEPT FROM {fq('SOURCE_TYPE_CATALOG')} "
                                    f"WHERE SOURCE_SYSTEM = '{map_source_system}' "
                                    f"AND FIELD_NAME = '{row['SOURCE_FIELD']}' LIMIT 1"
                                )
                                if not concept_row.empty:
                                    concept = concept_row["AI_EVENT_CONCEPT"].iloc[0].replace("'", "''")
                                    run_sql(
                                        f"MERGE INTO {fq('MDR')} t USING ("
                                        f"SELECT '{row['SOURCE_FIELD']}' AS P, $${concept}$$ AS C, "
                                        f"'{row['TARGET_VARIABLE']}' AS V, $${row['TARGET_LABEL']}$$ AS L, "
                                        f"'{map_source_system}' AS S) s "
                                        f"ON t.SOURCE_EVENT_CONCEPT = s.C AND t.TARGET_VARIABLE = s.V "
                                        f"WHEN MATCHED THEN UPDATE SET TIMES_REUSED = t.TIMES_REUSED + 1 "
                                        f"WHEN NOT MATCHED THEN INSERT "
                                        f"(SOURCE_FIELD_PATTERN, SOURCE_EVENT_CONCEPT, TARGET_VARIABLE, "
                                        f"TARGET_LABEL, APPROVED_BY, SOURCE_ORIGIN) "
                                        f"VALUES (s.P, s.C, s.V, s.L, 'demo_reviewer', s.S)"
                                    )
                                st.rerun()
                        with bc2:
                            if st.button("Reject", key=f"reject_{map_source_system}_{idx}"):
                                run_sql(
                                    f"UPDATE {fq('MAPPING_SUGGESTIONS')} SET STATUS = 'REJECTED', "
                                    f"REVIEWED_BY = 'demo_reviewer', REVIEWED_AT = CURRENT_TIMESTAMP() "
                                    f"WHERE SOURCE_SYSTEM = '{map_source_system}' "
                                    f"AND SOURCE_FIELD = '{row['SOURCE_FIELD']}'"
                                )
                                st.rerun()

                    st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: COMPOUNDING VALUE
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.header("Compounding value")
    st.markdown("Approved mappings persist in the MDR. Each new source benefits from every previous one.")

    mdr = run_query(f"SELECT * FROM {fq('MDR')} ORDER BY APPROVAL_DATE DESC")
    suggestions_all = run_query(f"SELECT * FROM {fq('MAPPING_SUGGESTIONS')}")

    if mdr.empty:
        st.info("Run AI Mapping on at least one source to build the MDR.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("MDR entries", len(mdr))
        with m2:
            st.metric("Total reuses", int(mdr["TIMES_REUSED"].sum()))
        with m3:
            if not suggestions_all.empty:
                mdr_matches = len(suggestions_all[suggestions_all["STATUS"] == "MDR_MATCH"])
                total = len(suggestions_all)
                st.metric("MDR hit rate", f"{mdr_matches/total:.0%}" if total > 0 else "—")
            else:
                st.metric("MDR hit rate", "—")
        with m4:
            if not suggestions_all.empty:
                pending = len(suggestions_all[suggestions_all["STATUS"] == "PENDING"])
                st.metric("Pending review", pending)
            else:
                st.metric("Pending review", 0)

        st.subheader("Mapping Data Repository (MDR)")
        st.markdown("Review and manage approved mappings by source. Re-target or delete incorrect entries.")

        # Get canonical variable list for re-targeting
        canonical_vars = run_query(f"SELECT VARIABLE_NAME, VARIABLE_LABEL FROM {fq('EVENT_VARIABLE_EMBEDDINGS')} ORDER BY VARIABLE_NAME")
        canonical_options = canonical_vars["VARIABLE_NAME"].tolist()
        canonical_label_map = dict(zip(canonical_vars["VARIABLE_NAME"], canonical_vars["VARIABLE_LABEL"]))

        # Source filter
        mdr_sources = mdr["SOURCE_ORIGIN"].unique().tolist()
        mdr_source_names = [system_to_name.get(s, s) for s in mdr_sources]
        mdr_all_option = ["All Sources"] + mdr_source_names
        selected_mdr_view = st.selectbox("Filter by source", mdr_all_option, key="mdr_filter")

        if selected_mdr_view == "All Sources":
            filtered_mdr = mdr
        else:
            filter_system = mdr_sources[mdr_source_names.index(selected_mdr_view)]
            filtered_mdr = mdr[mdr["SOURCE_ORIGIN"] == filter_system]

        st.caption(f"Showing {len(filtered_mdr)} mapping(s)")

        # Compact CSS for MDR rows
        st.markdown("""<style>
        .mdr-row { padding: 4px 0; border-bottom: 1px solid #eee; }
        .mdr-field { font-weight: bold; }
        .mdr-src { font-size: 0.8em; color: #888; }
        .mdr-reuse { font-size: 0.85em; color: #666; }
        </style>""", unsafe_allow_html=True)

        for midx, mrow in filtered_mdr.iterrows():
            mc1, mc2, mc3, mc4 = st.columns([2, 4, 1, 1])
            with mc1:
                st.markdown(f"**{mrow['SOURCE_FIELD_PATTERN']}**<br/><span style='font-size:0.8em;color:#888'>{system_to_name.get(mrow['SOURCE_ORIGIN'], mrow['SOURCE_ORIGIN'])}</span>", unsafe_allow_html=True)
            with mc2:
                current_target = mrow['TARGET_VARIABLE']
                current_idx = canonical_options.index(current_target) if current_target in canonical_options else 0
                new_target = st.selectbox(
                    "Target",
                    canonical_options,
                    index=current_idx,
                    key=f"mdr_target_{midx}",
                    label_visibility="collapsed",
                )
                if new_target != current_target:
                    new_label = canonical_label_map.get(new_target, new_target)
                    if st.button("Save", key=f"mdr_save_{midx}"):
                        run_sql(
                            f"UPDATE {fq('MDR')} SET TARGET_VARIABLE = '{new_target}', "
                            f"TARGET_LABEL = $${new_label}$$ "
                            f"WHERE SOURCE_FIELD_PATTERN = '{mrow['SOURCE_FIELD_PATTERN']}' "
                            f"AND SOURCE_ORIGIN = '{mrow['SOURCE_ORIGIN']}'"
                        )
                        st.rerun()
            with mc3:
                st.markdown(f"**{int(mrow['TIMES_REUSED'])}** reuses")
            with mc4:
                if st.button("Delete", key=f"mdr_del_{midx}"):
                    run_sql(
                        f"DELETE FROM {fq('MDR')} WHERE SOURCE_FIELD_PATTERN = '{mrow['SOURCE_FIELD_PATTERN']}' "
                        f"AND SOURCE_ORIGIN = '{mrow['SOURCE_ORIGIN']}'"
                    )
                    st.rerun()

        if not suggestions_all.empty:
            st.subheader("Source-over-source improvement")
            study_stats = suggestions_all.groupby("SOURCE_SYSTEM").agg(
                total=("STATUS", "count"),
                mdr_matches=("STATUS", lambda x: (x == "MDR_MATCH").sum()),
                auto_approved=("STATUS", lambda x: (x == "AUTO_APPROVED").sum()),
                avg_score=("SIMILARITY_SCORE", "mean"),
            ).reset_index()
            study_stats["mdr_rate"] = study_stats["mdr_matches"] / study_stats["total"]
            study_stats["SOURCE_SYSTEM"] = study_stats["SOURCE_SYSTEM"].map(lambda s: system_to_name.get(s, s))

            st.dataframe(
                study_stats.rename(columns={
                    "SOURCE_SYSTEM": "Source",
                    "total": "Fields",
                    "mdr_matches": "MDR Hits",
                    "auto_approved": "Auto-Approved",
                    "avg_score": "Avg Score",
                    "mdr_rate": "MDR Rate",
                }),
                use_container_width=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: PIPELINE BUILDER
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.header("Pipeline builder")
    st.markdown("Generate Dynamic Table DDL from approved MDR mappings. Customize before deploying.")

    mdr_pb = run_query(f"SELECT * FROM {fq('MDR')}")

    if mdr_pb.empty:
        st.info("Approve mappings in the AI Mapping tab to generate pipeline SQL.")
    else:
        # ─── Configuration controls ───
        st.subheader("Pipeline configuration")
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            silver_lag = st.text_input("Silver TARGET_LAG", value=get_config("SILVER_TARGET_LAG", "10 minutes"), key="pb_slag")
            gold_lag = st.text_input("Gold TARGET_LAG", value=get_config("GOLD_TARGET_LAG", "10 minutes"), key="pb_glag")
        with pc2:
            silver_wh = st.text_input("Silver warehouse", value=get_config("SILVER_WAREHOUSE", "APP_WH"), key="pb_swh")
            gold_wh = st.text_input("Gold warehouse", value=get_config("GOLD_WAREHOUSE", "APP_WH"), key="pb_gwh")
        with pc3:
            qual_thresh = st.text_input("Quality threshold", value=str(QUALITY_THRESHOLD), key="pb_qt")
            st.caption("Events below this score stay in Silver (dead letter)")

        st.divider()

        # ─── Generate Silver DT ───
        st.subheader("Silver Dynamic Table (profiling + quality score)")

        source_table_map = {v["system"]: v["table"] for v in SOURCES.values()}
        sources_mapped = mdr_pb["SOURCE_ORIGIN"].unique().tolist()

        silver_union_parts = []
        for src in sources_mapped:
            if src not in source_table_map:
                continue
            table = source_table_map[src]
            src_name = system_to_name.get(src, src)

            # Get the fields for this source from MDR
            src_fields = mdr_pb[mdr_pb["SOURCE_ORIGIN"] == src]
            ts_field = None
            for _, m in src_fields.iterrows():
                if m["TARGET_VARIABLE"] == "EVENT_TIMESTAMP":
                    ts_field = m["SOURCE_FIELD_PATTERN"]
                    break

            timestamp_check = f"TRY_TO_TIMESTAMP(RAW:{ts_field}::VARCHAR) IS NOT NULL" if ts_field else "TRUE"

            silver_union_parts.append(f"""    -- {src_name}
    SELECT
        RAW,
        '{src}' AS SOURCE_SYSTEM,
        INGESTED_AT,
        -- Structural quality checks
        (CASE WHEN {timestamp_check} THEN 1 ELSE 0 END
         + CASE WHEN OBJECT_KEYS(RAW) IS NOT NULL THEN 1 ELSE 0 END
        ) / 2.0 AS QUALITY_SCORE
    FROM {fq(table)}""")

        silver_sql = f"""CREATE OR REPLACE DYNAMIC TABLE {fq('SILVER_EVENTS')}
  TARGET_LAG = '{silver_lag}'
  WAREHOUSE = {silver_wh}
AS
{chr(10).join(["UNION ALL" + chr(10) if i > 0 else "" for i in range(len(silver_union_parts))]).join(silver_union_parts)};"""

        # Simpler approach - just join with UNION ALL
        silver_sql = f"""CREATE OR REPLACE DYNAMIC TABLE {fq('SILVER_EVENTS')}
  TARGET_LAG = '{silver_lag}'
  WAREHOUSE = {silver_wh}
AS
""" + "\nUNION ALL\n".join(silver_union_parts) + ";"

        st.code(silver_sql, language="sql")

        st.divider()

        # ─── Generate Gold DT ───
        st.subheader("Gold Dynamic Table (unified canonical schema)")

        gold_union_parts = []
        for src in sources_mapped:
            if src not in source_table_map:
                continue
            table = source_table_map[src]
            src_mappings = mdr_pb[mdr_pb["SOURCE_ORIGIN"] == src]
            src_name = system_to_name.get(src, src)

            select_exprs = []
            mapped_vars = set()
            for _, m in src_mappings.iterrows():
                field = m["SOURCE_FIELD_PATTERN"]
                target = m["TARGET_VARIABLE"]
                if target in mapped_vars:
                    continue
                mapped_vars.add(target)
                select_exprs.append(f"        RAW:{field}::VARCHAR AS {target}")

            all_canonical = ["EVENT_TIMESTAMP", "EVENT_TYPE", "DEVICE_ID", "DEVICE_TYPE",
                           "SESSION_ID", "USER_ACTION", "CONTENT_ID", "CONTENT_TYPE",
                           "LOCATION_ID", "DURATION_MS", "USER_ID", "SOURCE_PRODUCT"]
            for canon in all_canonical:
                if canon not in mapped_vars:
                    select_exprs.append(f"        NULL AS {canon}")

            select_exprs.append(f"        '{src}' AS _SOURCE_SYSTEM")
            select_exprs.append(f"        RAW AS _PAYLOAD")

            gold_union_parts.append(f"    -- {src_name}\n    SELECT\n" + ",\n".join(select_exprs) + f"\n    FROM {fq(table)}\n    WHERE TRUE  -- quality filter applied upstream in Silver")

        gold_sql = f"""CREATE OR REPLACE DYNAMIC TABLE {fq('GOLD_UNIFIED_EVENTS')}
  TARGET_LAG = '{gold_lag}'
  WAREHOUSE = {gold_wh}
AS
""" + "\n    UNION ALL\n".join(gold_union_parts) + ";"

        st.code(gold_sql, language="sql")

        st.divider()

        # ─── Deploy controls ───
        st.subheader("Deploy pipeline")
        st.markdown("Review the SQL above, then deploy both Dynamic Tables to start the automated pipeline.")

        dc1, dc2, dc3 = st.columns([1, 1, 3])
        with dc1:
            if st.button("Deploy Silver DT", type="primary", key="deploy_silver"):
                try:
                    run_sql(silver_sql.rstrip(";"))
                    st.success("Silver Dynamic Table created successfully")
                except Exception as e:
                    st.error(f"Error: {e}")
        with dc2:
            if st.button("Deploy Gold DT", type="primary", key="deploy_gold"):
                try:
                    run_sql(gold_sql.rstrip(";"))
                    st.success("Gold Dynamic Table created successfully")
                except Exception as e:
                    st.error(f"Error: {e}")

        # ─── Pipeline status ───
        st.divider()
        st.subheader("Pipeline status")
        try:
            dt_status = run_query(
                f"SELECT NAME, TARGET_LAG, REFRESH_MODE, SCHEDULING_STATE, LAST_COMPLETED_REFRESH_TIME "
                f"FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLES()) "
                f"WHERE SCHEMA_NAME = '{SCHEMA}' AND CATALOG_NAME = '{DB}'"
            )
            if not dt_status.empty:
                st.dataframe(dt_status, use_container_width=True)
            else:
                st.caption("No dynamic tables deployed yet.")
        except:
            st.caption("No dynamic tables deployed yet.")
