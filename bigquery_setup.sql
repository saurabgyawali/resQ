CREATE SCHEMA IF NOT EXISTS `daniel-reyes-uprm`.resqHack
OPTIONS (
  description = 'Dataset for ResQ hackathon prototype',
  location = 'US'
);

CREATE TABLE IF NOT EXISTS `daniel-reyes-uprm.resqHack.UserProfiles` (
  user_id STRING,
  full_name STRING,
  age INT64,
  blood_type STRING,
  conditions JSON,
  allergies JSON,
  medications JSON,
  emergency_contact_name STRING,
  emergency_contact_relationship STRING,
  emergency_contact_phone STRING,
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `daniel-reyes-uprm.resqHack.EmergencyContacts` (
  user_id STRING,
  contact_id STRING,
  name STRING,
  relationship STRING,
  phone STRING,
  is_primary BOOL,
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `daniel-reyes-uprm.resqHack.EmergencySessions` (
  session_id STRING,
  user_id STRING,
  started_at TIMESTAMP,
  last_case STRING,
  escalated BOOL,
  symptom_start_time STRING,
  location_text STRING,
  triage_summary STRING,
  status STRING
);

CREATE TABLE IF NOT EXISTS `daniel-reyes-uprm.resqHack.EmergencyMessages` (
  message_id STRING,
  session_id STRING,
  role STRING,
  modality STRING,
  text STRING,
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `daniel-reyes-uprm.resqHack.AnimationAssets` (
  case_id STRING,
  title STRING,
  local_path STRING,
  mime_type STRING,
  offline_ready BOOL
);

INSERT INTO `daniel-reyes-uprm.resqHack.UserProfiles`
(user_id, full_name, age, blood_type, conditions, allergies, medications, emergency_contact_name, emergency_contact_relationship, emergency_contact_phone, created_at)
VALUES
(
  'demo-user-1',
  'Maria Rivera',
  67,
  'O+',
  JSON '["Type 2 diabetes","Hypertension"]',
  JSON '["Penicillin"]',
  JSON '["Metformin","Lisinopril"]',
  'Daniel Rivera',
  'Son',
  '+1-787-555-0199',
  CURRENT_TIMESTAMP()
);

INSERT INTO `daniel-reyes-uprm.resqHack.EmergencyContacts`
(user_id, contact_id, name, relationship, phone, is_primary, created_at)
VALUES
('demo-user-1', 'contact-1', 'Daniel Rivera', 'Son', '+1-787-555-0199', TRUE, CURRENT_TIMESTAMP());

INSERT INTO `daniel-reyes-uprm.resqHack.AnimationAssets`
(case_id, title, local_path, mime_type, offline_ready)
VALUES
('not_breathing', 'CPR', 'assets/animations/cpr.gif', 'image/gif', TRUE),
('choking', 'Choking', 'assets/animations/choking.gif', 'image/gif', TRUE),
('severe_bleeding', 'Bleeding', 'assets/animations/bleeding.gif', 'image/gif', TRUE),
('stroke', 'Stroke', 'assets/animations/stroke.gif', 'image/gif', TRUE),
('chest_pain', 'Chest Pain', 'assets/animations/chest_pain.gif', 'image/gif', TRUE);