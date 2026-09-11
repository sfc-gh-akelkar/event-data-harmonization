# Event Schema Harmonization

AI-driven field classification, mapping, and pipeline generation for unifying event telemetry across multiple product lines with no standard schema.

## The Problem

Organizations with multiple products collect event data independently — each team names fields their own way. `ts` vs `event_time` vs `occurred_at` vs `timestamp` vs `logged_at` all mean "when did this event happen." You can't UNION these, you can't build a unified dashboard, and you can't answer cross-product questions without someone manually maintaining translation logic.

## The Solution

A Streamlit-in-Snowflake application that:

1. **Ingests** raw events as semi-structured JSON (VARIANT) from any source
2. **Classifies** fields using Cortex AI — reads field names + sample values, assigns semantic categories
3. **Profiles** data quality — structural stats (SQL) + AI-driven quality assessment (Cortex AI)
4. **Maps** classified fields to a canonical schema using vector embeddings + cosine similarity
5. **Routes by confidence** — high confidence auto-approves, medium goes to human review, low flags as novel
6. **Compounds knowledge** in a Mapping Data Repository (MDR) — each approved mapping accelerates the next source
7. **Generates** Silver and Gold Dynamic Table pipelines from the MDR

## Architecture

```
RAW (VARIANT)
  → Source Discovery: AI_COMPLETE classifies fields
  → Data Profiling: SQL stats + AI quality assessment
  → AI Mapping: AI_EMBED + VECTOR_COSINE_SIMILARITY against canonical variables
  → Confidence routing: >0.85 auto-approve, 0.70-0.85 human review, <0.70 novel
  → MDR (institutional memory, compounds with each source)
  → Pipeline Builder: generates Silver + Gold Dynamic Tables from MDR
```

## Snowflake Features Used

| Feature | Usage |
|---|---|
| **Cortex AI (AI_COMPLETE)** | Field classification, rationale generation, data quality profiling |
| **Cortex AI (AI_EMBED)** | e5-base-v2 vector embeddings for field-to-canonical matching |
| **VECTOR_COSINE_SIMILARITY** | Native vector comparison — no external vector DB |
| **VARIANT + LATERAL FLATTEN** | Semi-structured JSON ingestion and key extraction |
| **Dynamic Tables** | Auto-refreshing Silver (quality-gated) and Gold (unified schema) layers |
| **Streamlit in Snowflake** | Interactive app — no external infrastructure |

## Setup

### Prerequisites

- Snowflake account with Cortex AI enabled
- Role with CREATE DATABASE, CREATE SCHEMA, CREATE TABLE, CREATE DYNAMIC TABLE privileges
- A warehouse (the script uses `APP_WH`)

### 1. Run the setup script

Execute `setup_event_harmonization.sql` in a Snowflake worksheet. This creates:

- **Database/Schema**: `PATIENTPOINT_DEMO.EVENT_HARMONIZATION`
- **5 raw event tables** with synthetic data (10 events each):
  - `RAW_WAITING_ROOM_EVENTS` — proof of play, ad impressions
  - `RAW_IXR_EVENTS` — exam room touch interactions
  - `RAW_PROGRAMMATIC_EVENTS` — ad bid/impression/click events
  - `RAW_MOBILE_CHECKIN_EVENTS` — patient check-in via mobile app
  - `RAW_PROVIDER_PORTAL_EVENTS` — provider login, content, export activity
- **`EVENT_VARIABLE_EMBEDDINGS`** — 12 canonical event variables with pre-computed embeddings
- **`SOURCE_TYPE_CATALOG`** — stores classification results
- **`MAPPING_SUGGESTIONS`** — stores mapping proposals with confidence scores
- **`MDR`** — Mapping Data Repository (pre-populated with 32 known-correct mappings)
- **`PIPELINE_CONFIG`** — editable prompts, model selection, thresholds

### 2. Deploy the Streamlit app

```bash
snow streamlit deploy --replace \
  --connection <your-connection> \
  --database PATIENTPOINT_DEMO \
  --schema EVENT_HARMONIZATION
```

### 3. Grant permissions (if using a non-SYSADMIN role)

```sql
GRANT USAGE ON DATABASE PATIENTPOINT_DEMO TO ROLE <your_role>;
GRANT USAGE ON SCHEMA PATIENTPOINT_DEMO.EVENT_HARMONIZATION TO ROLE <your_role>;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA PATIENTPOINT_DEMO.EVENT_HARMONIZATION TO ROLE <your_role>;
GRANT CREATE STAGE ON SCHEMA PATIENTPOINT_DEMO.EVENT_HARMONIZATION TO ROLE <your_role>;
GRANT CREATE STREAMLIT ON SCHEMA PATIENTPOINT_DEMO.EVENT_HARMONIZATION TO ROLE <your_role>;
GRANT CREATE DYNAMIC TABLE ON SCHEMA PATIENTPOINT_DEMO.EVENT_HARMONIZATION TO ROLE <your_role>;
```

## The App

Six tabs, each building on the previous:

| Tab | What it does |
|---|---|
| **Architecture** | Pipeline diagram + active configuration summary |
| **Source Discovery** | Preview raw JSON, run AI field classification (editable prompt) |
| **Data Profiling** | Structural stats + AI quality assessment + cross-source comparison matrix |
| **AI Mapping & Review** | Embedding-based mapping with confidence routing and human review |
| **Compounding Value** | MDR management — filter by source, re-target mappings, track reuse metrics |
| **Pipeline Builder** | Configure and generate Silver + Gold Dynamic Tables from MDR |

## Configuration

All prompts, models, and thresholds are stored in `PIPELINE_CONFIG` and editable directly in the app:

| Key | Default | Description |
|---|---|---|
| `classification_model` | `claude-sonnet-4-6` | Model for field classification |
| `profiling_model` | `mistral-large2` | Model for quality profiling (cheaper) |
| `auto_approve_threshold` | `0.85` | Cosine similarity score for auto-approval |
| `review_threshold` | `0.70` | Below this, flagged as novel |

## Files

| File | Description |
|---|---|
| `setup_event_harmonization.sql` | DDL, synthetic data, canonical embeddings, config |
| `streamlit_app.py` | The Streamlit application |
| `snowflake.yml` | Streamlit-in-Snowflake deployment config |
| `pyproject.toml` | Python dependencies |
