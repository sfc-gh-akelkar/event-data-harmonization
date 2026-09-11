-- =============================================================================
-- PatientPoint Event Harmonization Demo — Setup Script
-- Creates synthetic event data from 5 products + canonical reference tables
-- =============================================================================

USE ROLE SYSADMIN;
CREATE DATABASE IF NOT EXISTS PATIENTPOINT_DEMO;
CREATE SCHEMA IF NOT EXISTS PATIENTPOINT_DEMO.EVENT_HARMONIZATION;
USE SCHEMA PATIENTPOINT_DEMO.EVENT_HARMONIZATION;
USE WAREHOUSE APP_WH;

-- =============================================================================
-- 1. RAW EVENT SOURCE TABLES (Bronze — VARIANT)
-- Each product uses different field names for the same concepts
-- =============================================================================

-- Source 1: Waiting Room Displays (proof of play, ad impressions)
CREATE OR REPLACE TABLE RAW_WAITING_ROOM_EVENTS (
    RAW VARIANT,
    INGESTED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    SOURCE_SYSTEM VARCHAR DEFAULT 'waiting_room_displays'
);

INSERT INTO RAW_WAITING_ROOM_EVENTS (RAW)
SELECT PARSE_JSON(column1) FROM VALUES
('{"ts":"2024-08-15T09:14:22Z","screen_id":"WR-4412","ad_unit_id":"AU-881","play_type":"video_30s","duration_sec":30,"venue":"lobby_main","location_code":"CHI-NORTHWESTERN-04","network":"core"}'),
('{"ts":"2024-08-15T09:14:52Z","screen_id":"WR-4412","ad_unit_id":"AU-220","play_type":"static_img","duration_sec":15,"venue":"lobby_main","location_code":"CHI-NORTHWESTERN-04","network":"core"}'),
('{"ts":"2024-08-15T09:15:07Z","screen_id":"WR-4413","ad_unit_id":"AU-881","play_type":"video_30s","duration_sec":30,"venue":"waiting_room_2","location_code":"CHI-NORTHWESTERN-04","network":"core"}'),
('{"ts":"2024-08-15T09:22:01Z","screen_id":"WR-5501","ad_unit_id":"AU-445","play_type":"video_15s","duration_sec":15,"venue":"lobby","location_code":"NYC-MOUNT-SINAI-01","network":"precision"}'),
('{"ts":"2024-08-15T09:22:16Z","screen_id":"WR-5501","ad_unit_id":"AU-446","play_type":"static_img","duration_sec":10,"venue":"lobby","location_code":"NYC-MOUNT-SINAI-01","network":"precision"}'),
('{"ts":"2024-08-15T09:30:00Z","screen_id":"WR-5502","ad_unit_id":"AU-220","play_type":"video_30s","duration_sec":30,"venue":"pediatrics_wait","location_code":"NYC-MOUNT-SINAI-01","network":"core"}'),
('{"ts":"2024-08-15T10:01:15Z","screen_id":"WR-6001","ad_unit_id":"AU-900","play_type":"carousel","duration_sec":45,"venue":"main_lobby","location_code":"LA-CEDARS-02","network":"core"}'),
('{"ts":"2024-08-15T10:01:45Z","screen_id":"WR-6001","ad_unit_id":"AU-901","play_type":"static_img","duration_sec":10,"venue":"main_lobby","location_code":"LA-CEDARS-02","network":"precision"}'),
('{"ts":"2024-08-15T10:05:30Z","screen_id":"WR-6002","ad_unit_id":"AU-220","play_type":"video_15s","duration_sec":15,"venue":"pharmacy_area","location_code":"LA-CEDARS-02","network":"core"}'),
('{"ts":"2024-08-15T10:10:00Z","screen_id":"WR-4412","ad_unit_id":"AU-950","play_type":"video_30s","duration_sec":30,"venue":"lobby_main","location_code":"CHI-NORTHWESTERN-04","network":"core"}');

-- Source 2: iXR Interactive Exam Room Devices (touch events, link sends)
CREATE OR REPLACE TABLE RAW_IXR_EVENTS (
    RAW VARIANT,
    INGESTED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    SOURCE_SYSTEM VARCHAR DEFAULT 'ixr_interactive'
);

INSERT INTO RAW_IXR_EVENTS (RAW)
SELECT PARSE_JSON(column1) FROM VALUES
('{"event_time":"2024-08-15T09:20:33.441Z","kiosk_serial":"IXR-K019","interaction_type":"tap","content_ref":"HI-2201","content_category":"diabetes_education","tap_x":412,"tap_y":305,"session_token":"sess-a8f2c","room_id":"EXAM-204"}'),
('{"event_time":"2024-08-15T09:20:45.102Z","kiosk_serial":"IXR-K019","interaction_type":"swipe","content_ref":"HI-2202","content_category":"diabetes_education","tap_x":null,"tap_y":null,"session_token":"sess-a8f2c","room_id":"EXAM-204"}'),
('{"event_time":"2024-08-15T09:21:10.887Z","kiosk_serial":"IXR-K019","interaction_type":"link_sent","content_ref":"HI-2201","content_category":"diabetes_education","tap_x":null,"tap_y":null,"session_token":"sess-a8f2c","room_id":"EXAM-204","destination":"sms"}'),
('{"event_time":"2024-08-15T09:35:12.100Z","kiosk_serial":"IXR-K022","interaction_type":"tap","content_ref":"HI-3305","content_category":"cardiac_rehab","tap_x":200,"tap_y":150,"session_token":"sess-b4e11","room_id":"EXAM-112"}'),
('{"event_time":"2024-08-15T09:35:44.200Z","kiosk_serial":"IXR-K022","interaction_type":"tap","content_ref":"HI-3306","content_category":"cardiac_rehab","tap_x":350,"tap_y":280,"session_token":"sess-b4e11","room_id":"EXAM-112"}'),
('{"event_time":"2024-08-15T09:36:01.500Z","kiosk_serial":"IXR-K022","interaction_type":"link_sent","content_ref":"HI-3305","content_category":"cardiac_rehab","tap_x":null,"tap_y":null,"session_token":"sess-b4e11","room_id":"EXAM-112","destination":"email"}'),
('{"event_time":"2024-08-15T10:15:00.000Z","kiosk_serial":"IXR-K045","interaction_type":"content_viewed","content_ref":"HI-1100","content_category":"prenatal_care","tap_x":null,"tap_y":null,"session_token":"sess-c9d33","room_id":"EXAM-301"}'),
('{"event_time":"2024-08-15T10:15:22.000Z","kiosk_serial":"IXR-K045","interaction_type":"tap","content_ref":"HI-1101","content_category":"prenatal_care","tap_x":500,"tap_y":400,"session_token":"sess-c9d33","room_id":"EXAM-301"}'),
('{"event_time":"2024-08-15T10:16:05.000Z","kiosk_serial":"IXR-K045","interaction_type":"link_sent","content_ref":"HI-1100","content_category":"prenatal_care","tap_x":null,"tap_y":null,"session_token":"sess-c9d33","room_id":"EXAM-301","destination":"sms"}'),
('{"event_time":"2024-08-15T10:20:00.000Z","kiosk_serial":"IXR-K019","interaction_type":"idle_timeout","content_ref":null,"content_category":null,"tap_x":null,"tap_y":null,"session_token":"sess-a8f2c","room_id":"EXAM-204"}');

-- Source 3: Programmatic Ad Platform (bid/impression/click events)
CREATE OR REPLACE TABLE RAW_PROGRAMMATIC_EVENTS (
    RAW VARIANT,
    INGESTED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    SOURCE_SYSTEM VARCHAR DEFAULT 'programmatic_platform'
);

INSERT INTO RAW_PROGRAMMATIC_EVENTS (RAW)
SELECT PARSE_JSON(column1) FROM VALUES
('{"occurred_at":"2024-08-15T09:14:00.000Z","device_identifier":"PROG-DSP-7","event_name":"bid_request","campaign_id":"CMP-2241","creative_id":"CR-445","advertiser":"pharma_co_a","bid_amount_cpm":12.50,"exchange":"ppx_internal"}'),
('{"occurred_at":"2024-08-15T09:14:01.200Z","device_identifier":"PROG-DSP-7","event_name":"bid_response","campaign_id":"CMP-2241","creative_id":"CR-445","advertiser":"pharma_co_a","bid_amount_cpm":12.50,"win":true,"exchange":"ppx_internal"}'),
('{"occurred_at":"2024-08-15T09:14:02.500Z","device_identifier":"PROG-DSP-7","event_name":"impression","campaign_id":"CMP-2241","creative_id":"CR-445","advertiser":"pharma_co_a","bid_amount_cpm":12.50,"viewable":true,"exchange":"ppx_internal"}'),
('{"occurred_at":"2024-08-15T09:14:15.000Z","device_identifier":"PROG-DSP-7","event_name":"click","campaign_id":"CMP-2241","creative_id":"CR-445","advertiser":"pharma_co_a","bid_amount_cpm":null,"click_url":"https://pharma-a.com/landing","exchange":"ppx_internal"}'),
('{"occurred_at":"2024-08-15T09:20:00.000Z","device_identifier":"PROG-DSP-12","event_name":"bid_request","campaign_id":"CMP-3010","creative_id":"CR-890","advertiser":"pharma_co_b","bid_amount_cpm":8.75,"exchange":"ppx_internal"}'),
('{"occurred_at":"2024-08-15T09:20:01.000Z","device_identifier":"PROG-DSP-12","event_name":"bid_response","campaign_id":"CMP-3010","creative_id":"CR-890","advertiser":"pharma_co_b","bid_amount_cpm":8.75,"win":false,"exchange":"ppx_internal"}'),
('{"occurred_at":"2024-08-15T10:00:00.000Z","device_identifier":"PROG-DSP-7","event_name":"impression","campaign_id":"CMP-2241","creative_id":"CR-446","advertiser":"pharma_co_a","bid_amount_cpm":11.00,"viewable":true,"exchange":"ppx_internal"}'),
('{"occurred_at":"2024-08-15T10:00:05.000Z","device_identifier":"PROG-DSP-7","event_name":"click","campaign_id":"CMP-2241","creative_id":"CR-446","advertiser":"pharma_co_a","bid_amount_cpm":null,"click_url":"https://pharma-a.com/product","exchange":"ppx_internal"}'),
('{"occurred_at":"2024-08-15T10:30:00.000Z","device_identifier":"PROG-DSP-20","event_name":"conversion","campaign_id":"CMP-2241","creative_id":"CR-445","advertiser":"pharma_co_a","bid_amount_cpm":null,"conversion_type":"signup","exchange":"ppx_internal"}'),
('{"occurred_at":"2024-08-15T10:45:00.000Z","device_identifier":"PROG-DSP-12","event_name":"impression","campaign_id":"CMP-3010","creative_id":"CR-891","advertiser":"pharma_co_b","bid_amount_cpm":9.00,"viewable":false,"exchange":"ppx_internal"}');

-- Source 4: Mobile Check-in App (patient actions)
CREATE OR REPLACE TABLE RAW_MOBILE_CHECKIN_EVENTS (
    RAW VARIANT,
    INGESTED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    SOURCE_SYSTEM VARCHAR DEFAULT 'mobile_checkin'
);

INSERT INTO RAW_MOBILE_CHECKIN_EVENTS (RAW)
SELECT PARSE_JSON(column1) FROM VALUES
('{"timestamp":"2024-08-15T08:45:00Z","terminal_id":"MOB-T100","action":"check_in","form_id":"F-INTAKE-01","patient_hash":"p_a3f8b2","clinic_id":"CHI-NORTHWESTERN-04","app_version":"3.2.1"}'),
('{"timestamp":"2024-08-15T08:45:30Z","terminal_id":"MOB-T100","action":"form_started","form_id":"F-INTAKE-01","patient_hash":"p_a3f8b2","clinic_id":"CHI-NORTHWESTERN-04","app_version":"3.2.1"}'),
('{"timestamp":"2024-08-15T08:48:15Z","terminal_id":"MOB-T100","action":"form_submitted","form_id":"F-INTAKE-01","patient_hash":"p_a3f8b2","clinic_id":"CHI-NORTHWESTERN-04","app_version":"3.2.1"}'),
('{"timestamp":"2024-08-15T08:48:20Z","terminal_id":"MOB-T100","action":"notification_sent","form_id":null,"patient_hash":"p_a3f8b2","clinic_id":"CHI-NORTHWESTERN-04","app_version":"3.2.1","notification_type":"appointment_confirmed"}'),
('{"timestamp":"2024-08-15T09:00:00Z","terminal_id":"MOB-T200","action":"check_in","form_id":"F-INTAKE-02","patient_hash":"p_b7c4d1","clinic_id":"NYC-MOUNT-SINAI-01","app_version":"3.2.1"}'),
('{"timestamp":"2024-08-15T09:00:45Z","terminal_id":"MOB-T200","action":"form_started","form_id":"F-INTAKE-02","patient_hash":"p_b7c4d1","clinic_id":"NYC-MOUNT-SINAI-01","app_version":"3.2.1"}'),
('{"timestamp":"2024-08-15T09:03:20Z","terminal_id":"MOB-T200","action":"form_submitted","form_id":"F-INTAKE-02","patient_hash":"p_b7c4d1","clinic_id":"NYC-MOUNT-SINAI-01","app_version":"3.2.1"}'),
('{"timestamp":"2024-08-15T09:10:00Z","terminal_id":"MOB-T100","action":"content_viewed","form_id":null,"patient_hash":"p_a3f8b2","clinic_id":"CHI-NORTHWESTERN-04","app_version":"3.2.1","content_shown":"health_tip_daily"}'),
('{"timestamp":"2024-08-15T09:15:00Z","terminal_id":"MOB-T300","action":"check_in","form_id":"F-INTAKE-01","patient_hash":"p_e2f9a0","clinic_id":"LA-CEDARS-02","app_version":"3.1.9"}'),
('{"timestamp":"2024-08-15T09:15:30Z","terminal_id":"MOB-T300","action":"form_abandoned","form_id":"F-INTAKE-01","patient_hash":"p_e2f9a0","clinic_id":"LA-CEDARS-02","app_version":"3.1.9"}');

-- Source 5: Provider Portal (web activity events)
CREATE OR REPLACE TABLE RAW_PROVIDER_PORTAL_EVENTS (
    RAW VARIANT,
    INGESTED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    SOURCE_SYSTEM VARCHAR DEFAULT 'provider_portal'
);

INSERT INTO RAW_PROVIDER_PORTAL_EVENTS (RAW)
SELECT PARSE_JSON(column1) FROM VALUES
('{"logged_at":"2024-08-15T08:30:00Z","user_device":"desktop_chrome","activity_type":"login","page_url":"/dashboard","search_query":null,"provider_id":"DR-1001","org_id":"CHI-NORTHWESTERN-04"}'),
('{"logged_at":"2024-08-15T08:30:15Z","user_device":"desktop_chrome","activity_type":"page_view","page_url":"/patients/schedule","search_query":null,"provider_id":"DR-1001","org_id":"CHI-NORTHWESTERN-04"}'),
('{"logged_at":"2024-08-15T08:31:00Z","user_device":"desktop_chrome","activity_type":"search","page_url":"/patients","search_query":"diabetes type 2","provider_id":"DR-1001","org_id":"CHI-NORTHWESTERN-04"}'),
('{"logged_at":"2024-08-15T08:32:00Z","user_device":"desktop_chrome","activity_type":"page_view","page_url":"/patients/P-44821","search_query":null,"provider_id":"DR-1001","org_id":"CHI-NORTHWESTERN-04"}'),
('{"logged_at":"2024-08-15T08:35:00Z","user_device":"desktop_chrome","activity_type":"export","page_url":"/reports/monthly","search_query":null,"provider_id":"DR-1001","org_id":"CHI-NORTHWESTERN-04","export_format":"pdf"}'),
('{"logged_at":"2024-08-15T09:00:00Z","user_device":"mobile_safari","activity_type":"login","page_url":"/dashboard","search_query":null,"provider_id":"DR-2050","org_id":"NYC-MOUNT-SINAI-01"}'),
('{"logged_at":"2024-08-15T09:00:30Z","user_device":"mobile_safari","activity_type":"page_view","page_url":"/content/library","search_query":null,"provider_id":"DR-2050","org_id":"NYC-MOUNT-SINAI-01"}'),
('{"logged_at":"2024-08-15T09:01:00Z","user_device":"mobile_safari","activity_type":"content_activated","page_url":"/content/HI-2201","search_query":null,"provider_id":"DR-2050","org_id":"NYC-MOUNT-SINAI-01","content_assigned_to":"EXAM-204"}'),
('{"logged_at":"2024-08-15T09:05:00Z","user_device":"desktop_edge","activity_type":"login","page_url":"/dashboard","search_query":null,"provider_id":"DR-3100","org_id":"LA-CEDARS-02"}'),
('{"logged_at":"2024-08-15T09:05:30Z","user_device":"desktop_edge","activity_type":"page_view","page_url":"/analytics/engagement","search_query":null,"provider_id":"DR-3100","org_id":"LA-CEDARS-02"}');


-- =============================================================================
-- 2. CANONICAL EVENT VARIABLE EMBEDDINGS (Target Schema)
-- Pre-embedded reference table — the "SDTM spec" for events
-- =============================================================================

CREATE OR REPLACE TABLE EVENT_VARIABLE_EMBEDDINGS (
    VARIABLE_NAME VARCHAR,
    VARIABLE_LABEL VARCHAR,
    VARIABLE_DESCRIPTION VARCHAR,
    DATA_TYPE VARCHAR,
    EMBEDDING VECTOR(FLOAT, 768)
);

-- Populate embeddings using AI_EMBED
INSERT INTO EVENT_VARIABLE_EMBEDDINGS (VARIABLE_NAME, VARIABLE_LABEL, VARIABLE_DESCRIPTION, DATA_TYPE, EMBEDDING)
SELECT 'EVENT_TIMESTAMP', 'Event Timestamp', 'The date and time when the event occurred', 'TIMESTAMP_NTZ',
       AI_EMBED('e5-base-v2', 'EVENT_TIMESTAMP | Event Timestamp | The date and time when the event occurred');
INSERT INTO EVENT_VARIABLE_EMBEDDINGS (VARIABLE_NAME, VARIABLE_LABEL, VARIABLE_DESCRIPTION, DATA_TYPE, EMBEDDING)
SELECT 'EVENT_TYPE', 'Event Type', 'Category or classification of the event such as impression click interaction or system', 'VARCHAR',
       AI_EMBED('e5-base-v2', 'EVENT_TYPE | Event Type | Category or classification of the event such as impression click interaction or system');
INSERT INTO EVENT_VARIABLE_EMBEDDINGS (VARIABLE_NAME, VARIABLE_LABEL, VARIABLE_DESCRIPTION, DATA_TYPE, EMBEDDING)
SELECT 'DEVICE_ID', 'Device Identifier', 'Unique identifier for the physical or logical device generating the event', 'VARCHAR',
       AI_EMBED('e5-base-v2', 'DEVICE_ID | Device Identifier | Unique identifier for the physical or logical device generating the event');
INSERT INTO EVENT_VARIABLE_EMBEDDINGS (VARIABLE_NAME, VARIABLE_LABEL, VARIABLE_DESCRIPTION, DATA_TYPE, EMBEDDING)
SELECT 'DEVICE_TYPE', 'Device Type', 'Category of device such as screen kiosk mobile terminal or desktop browser', 'VARCHAR',
       AI_EMBED('e5-base-v2', 'DEVICE_TYPE | Device Type | Category of device such as screen kiosk mobile terminal or desktop browser');
INSERT INTO EVENT_VARIABLE_EMBEDDINGS (VARIABLE_NAME, VARIABLE_LABEL, VARIABLE_DESCRIPTION, DATA_TYPE, EMBEDDING)
SELECT 'SESSION_ID', 'Session Identifier', 'Grouping identifier that links related events from a single user session or interaction sequence', 'VARCHAR',
       AI_EMBED('e5-base-v2', 'SESSION_ID | Session Identifier | Grouping identifier that links related events from a single user session or interaction sequence');
INSERT INTO EVENT_VARIABLE_EMBEDDINGS (VARIABLE_NAME, VARIABLE_LABEL, VARIABLE_DESCRIPTION, DATA_TYPE, EMBEDDING)
SELECT 'USER_ACTION', 'User Action', 'The specific action taken by the user or system such as tap swipe view submit click play or send', 'VARCHAR',
       AI_EMBED('e5-base-v2', 'USER_ACTION | User Action | The specific action taken by the user or system such as tap swipe view submit click play or send');
INSERT INTO EVENT_VARIABLE_EMBEDDINGS (VARIABLE_NAME, VARIABLE_LABEL, VARIABLE_DESCRIPTION, DATA_TYPE, EMBEDDING)
SELECT 'CONTENT_ID', 'Content Identifier', 'Reference to the specific content item displayed or interacted with such as ad unit health info or creative', 'VARCHAR',
       AI_EMBED('e5-base-v2', 'CONTENT_ID | Content Identifier | Reference to the specific content item displayed or interacted with such as ad unit health info or creative');
INSERT INTO EVENT_VARIABLE_EMBEDDINGS (VARIABLE_NAME, VARIABLE_LABEL, VARIABLE_DESCRIPTION, DATA_TYPE, EMBEDDING)
SELECT 'CONTENT_TYPE', 'Content Type', 'Category of content such as video ad static image health education form or page', 'VARCHAR',
       AI_EMBED('e5-base-v2', 'CONTENT_TYPE | Content Type | Category of content such as video ad static image health education form or page');
INSERT INTO EVENT_VARIABLE_EMBEDDINGS (VARIABLE_NAME, VARIABLE_LABEL, VARIABLE_DESCRIPTION, DATA_TYPE, EMBEDDING)
SELECT 'LOCATION_ID', 'Location Identifier', 'Physical or logical location where the device is deployed such as clinic site or room', 'VARCHAR',
       AI_EMBED('e5-base-v2', 'LOCATION_ID | Location Identifier | Physical or logical location where the device is deployed such as clinic site or room');
INSERT INTO EVENT_VARIABLE_EMBEDDINGS (VARIABLE_NAME, VARIABLE_LABEL, VARIABLE_DESCRIPTION, DATA_TYPE, EMBEDDING)
SELECT 'DURATION_MS', 'Duration Milliseconds', 'Length of time the event or interaction lasted measured in milliseconds', 'NUMBER',
       AI_EMBED('e5-base-v2', 'DURATION_MS | Duration Milliseconds | Length of time the event or interaction lasted measured in milliseconds');
INSERT INTO EVENT_VARIABLE_EMBEDDINGS (VARIABLE_NAME, VARIABLE_LABEL, VARIABLE_DESCRIPTION, DATA_TYPE, EMBEDDING)
SELECT 'USER_ID', 'User Identifier', 'Hashed or anonymized identifier for the patient or user involved in the event', 'VARCHAR',
       AI_EMBED('e5-base-v2', 'USER_ID | User Identifier | Hashed or anonymized identifier for the patient or user involved in the event');
INSERT INTO EVENT_VARIABLE_EMBEDDINGS (VARIABLE_NAME, VARIABLE_LABEL, VARIABLE_DESCRIPTION, DATA_TYPE, EMBEDDING)
SELECT 'SOURCE_PRODUCT', 'Source Product', 'The PatientPoint product or platform that generated this event', 'VARCHAR',
       AI_EMBED('e5-base-v2', 'SOURCE_PRODUCT | Source Product | The PatientPoint product or platform that generated this event');


-- =============================================================================
-- 3. OPERATIONAL TABLES
-- =============================================================================

-- Source Type Catalog — AI classification results
CREATE OR REPLACE TABLE SOURCE_TYPE_CATALOG (
    SOURCE_SYSTEM VARCHAR,
    FIELD_NAME VARCHAR,
    INFERRED_DATA_TYPE VARCHAR,
    SAMPLE_VALUES VARCHAR,
    AI_FIELD_CLASSIFICATION VARCHAR,
    AI_EVENT_CONCEPT VARCHAR,
    CONFIDENCE_SCORE FLOAT,
    CATALOGED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Mapping Suggestions — AI-proposed mappings with confidence routing
CREATE OR REPLACE TABLE MAPPING_SUGGESTIONS (
    SOURCE_SYSTEM VARCHAR,
    SOURCE_FIELD VARCHAR,
    TARGET_VARIABLE VARCHAR,
    TARGET_LABEL VARCHAR,
    SIMILARITY_SCORE FLOAT,
    AI_RATIONALE VARCHAR,
    STATUS VARCHAR DEFAULT 'PENDING',  -- PENDING, AUTO_APPROVED, APPROVED, REJECTED, NOVEL
    REVIEWED_BY VARCHAR,
    REVIEWED_AT TIMESTAMP,
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- MDR (Mapping Data Repository) — approved mappings for reuse
CREATE OR REPLACE TABLE MDR (
    SOURCE_FIELD_PATTERN VARCHAR,
    SOURCE_EVENT_CONCEPT VARCHAR,
    TARGET_VARIABLE VARCHAR,
    TARGET_LABEL VARCHAR,
    APPROVED_BY VARCHAR,
    APPROVAL_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    SOURCE_ORIGIN VARCHAR,
    TIMES_REUSED NUMBER DEFAULT 0
);

-- =============================================================================
-- Done. Verify:
-- =============================================================================
SELECT 'RAW_WAITING_ROOM_EVENTS' AS TABLE_NAME, COUNT(*) AS ROWS FROM RAW_WAITING_ROOM_EVENTS
UNION ALL SELECT 'RAW_IXR_EVENTS', COUNT(*) FROM RAW_IXR_EVENTS
UNION ALL SELECT 'RAW_PROGRAMMATIC_EVENTS', COUNT(*) FROM RAW_PROGRAMMATIC_EVENTS
UNION ALL SELECT 'RAW_MOBILE_CHECKIN_EVENTS', COUNT(*) FROM RAW_MOBILE_CHECKIN_EVENTS
UNION ALL SELECT 'RAW_PROVIDER_PORTAL_EVENTS', COUNT(*) FROM RAW_PROVIDER_PORTAL_EVENTS
UNION ALL SELECT 'EVENT_VARIABLE_EMBEDDINGS', COUNT(*) FROM EVENT_VARIABLE_EMBEDDINGS;
