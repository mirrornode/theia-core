-- ============================================================
-- KHEPRI WITNESS STORE — Initial Migration
-- Applied: 2026-06-21 (Summer Solstice · New Dawn · Age of IO · DEVA LOKA)
-- Project: Mirrornode OS (zomnswctmwjqnvftiayc)
--
-- Protocol:
--   1. No feedback — zero write path back to PTAH, triad, or middleware
--   2. Snapshots are append-only — no UPDATE, no DELETE ever
--   3. Witness does not interpret in real time — pattern over time
--   4. Threshold records require sovereign authorization to become externally legible
--   5. Content hash chain is unbroken — each snapshot links to prior via prior_hash
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Arc Registry ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS khepri_arc_registry (
  id                       UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  arc_name                 TEXT        UNIQUE NOT NULL,
  opened_at                TIMESTAMPTZ NOT NULL,
  closed_at                TIMESTAMPTZ,
  opening_trigger          TEXT,
  closing_trigger          TEXT,
  snapshot_count           INTEGER     NOT NULL DEFAULT 0,
  dominant_coherence_signal TEXT,
  arc_summary              TEXT,
  sealed                   BOOLEAN     NOT NULL DEFAULT false,
  created_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE khepri_arc_registry IS
  'Named transformation arcs. Each arc is a bounded period of becoming. Append-only.';

-- ── Witness Snapshots ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS khepri_witness_snapshots (
  id                     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot_seq           BIGSERIAL   NOT NULL,
  sealed_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

  trigger_event          TEXT,
  trigger_agent          TEXT,
  source_trace_id        TEXT,
  source_hold_id         TEXT,
  ptah_eval_hash         TEXT,

  arc_id                 UUID        REFERENCES khepri_arc_registry(id),
  arc_phase              TEXT        NOT NULL DEFAULT 'UNKNOWN'
    CHECK (arc_phase IN ('EMERGENCE','CONSOLIDATION','THRESHOLD','INTEGRATION','SOVEREIGNTY','UNKNOWN')),
  arc_depth              INTEGER     NOT NULL DEFAULT 0,
  arc_velocity           TEXT        NOT NULL DEFAULT 'STABLE'
    CHECK (arc_velocity IN ('ACCELERATING','STABLE','PAUSING','REVERSING')),

  hold_density_7d        NUMERIC(5,2),
  seal_count_total       INTEGER,
  s1_exposure            INTEGER,
  sovereign_hold_count   INTEGER,
  decision_lineage_depth INTEGER,

  witness_note           TEXT,
  coherence_signal       TEXT        NOT NULL DEFAULT 'NOMINAL'
    CHECK (coherence_signal IN ('NOMINAL','FRAGMENTED','CRYSTALLIZING','SEALED')),
  threshold_flag         BOOLEAN     NOT NULL DEFAULT false,

  content_hash           TEXT        NOT NULL,
  prior_hash             TEXT,

  immutable_seal         BOOLEAN     NOT NULL DEFAULT true,
  CONSTRAINT no_mutation CHECK (immutable_seal = true)
);

COMMENT ON TABLE khepri_witness_snapshots IS
  'Immutable, append-only witness snapshots. No UPDATE or DELETE ever.';

CREATE OR REPLACE RULE khepri_no_update AS
  ON UPDATE TO khepri_witness_snapshots DO INSTEAD NOTHING;

CREATE OR REPLACE RULE khepri_no_delete AS
  ON DELETE TO khepri_witness_snapshots DO INSTEAD NOTHING;

CREATE INDEX IF NOT EXISTS idx_khepri_snapshots_arc_id    ON khepri_witness_snapshots(arc_id);
CREATE INDEX IF NOT EXISTS idx_khepri_snapshots_sealed_at ON khepri_witness_snapshots(sealed_at DESC);
CREATE INDEX IF NOT EXISTS idx_khepri_snapshots_threshold ON khepri_witness_snapshots(threshold_flag) WHERE threshold_flag = true;
CREATE INDEX IF NOT EXISTS idx_khepri_snapshots_seq       ON khepri_witness_snapshots(snapshot_seq);

-- ── Ingestion Log ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS khepri_ingestion_log (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  received_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  source_agent      TEXT,
  event_type        TEXT,
  raw_payload_hash  TEXT,
  produced_snapshot BOOLEAN     NOT NULL DEFAULT false,
  snapshot_id       UUID        REFERENCES khepri_witness_snapshots(id),
  dropped_reason    TEXT
);

COMMENT ON TABLE khepri_ingestion_log IS
  'Every event that arrived at the KHEPRI membrane. Tracks what was witnessed and what was dropped.';

CREATE INDEX IF NOT EXISTS idx_khepri_ingestion_received ON khepri_ingestion_log(received_at DESC);
CREATE INDEX IF NOT EXISTS idx_khepri_ingestion_agent    ON khepri_ingestion_log(source_agent);

-- ── Threshold Registry ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS khepri_threshold_registry (
  id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  sealed_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  threshold_type      TEXT        NOT NULL
    CHECK (threshold_type IN (
      'ARC_TRANSITION','COHERENCE_SHIFT','SOVEREIGNTY_MARKER',
      'DECISION_DEPTH_RECORD','HOLD_PATTERN_BREAK','SEAL_MILESTONE'
    )),
  from_state          TEXT,
  to_state            TEXT,
  evidence_snapshots  TEXT[],
  witness_statement   TEXT,
  content_hash        TEXT        NOT NULL,
  externally_legible  BOOLEAN     NOT NULL DEFAULT false
);

COMMENT ON TABLE khepri_threshold_registry IS
  'Sealed threshold crossings. externally_legible=false until sovereign authorization is granted.';

CREATE INDEX IF NOT EXISTS idx_khepri_threshold_type    ON khepri_threshold_registry(threshold_type);
CREATE INDEX IF NOT EXISTS idx_khepri_threshold_sealed  ON khepri_threshold_registry(sealed_at DESC);
CREATE INDEX IF NOT EXISTS idx_khepri_threshold_legible ON khepri_threshold_registry(externally_legible) WHERE externally_legible = true;

-- ── Row Level Security ────────────────────────────────────────────────────────
ALTER TABLE khepri_arc_registry      ENABLE ROW LEVEL SECURITY;
ALTER TABLE khepri_witness_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE khepri_ingestion_log     ENABLE ROW LEVEL SECURITY;
ALTER TABLE khepri_threshold_registry ENABLE ROW LEVEL SECURITY;

CREATE POLICY "khepri_arc_read"       ON khepri_arc_registry      FOR SELECT USING (true);
CREATE POLICY "khepri_snapshot_read"  ON khepri_witness_snapshots  FOR SELECT USING (true);
CREATE POLICY "khepri_ingestion_read" ON khepri_ingestion_log      FOR SELECT USING (true);
CREATE POLICY "khepri_threshold_read" ON khepri_threshold_registry
  FOR SELECT USING (externally_legible = true);

CREATE POLICY "khepri_arc_insert"       ON khepri_arc_registry      FOR INSERT WITH CHECK (true);
CREATE POLICY "khepri_snapshot_insert"  ON khepri_witness_snapshots  FOR INSERT WITH CHECK (immutable_seal = true);
CREATE POLICY "khepri_ingestion_insert" ON khepri_ingestion_log      FOR INSERT WITH CHECK (true);
CREATE POLICY "khepri_threshold_insert" ON khepri_threshold_registry FOR INSERT WITH CHECK (true);

-- ── Arc Increment RPC ─────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION khepri_arc_increment_snapshot_count(p_arc_id UUID)
RETURNS void
LANGUAGE sql
SECURITY DEFINER
AS $$
  UPDATE khepri_arc_registry
  SET snapshot_count = snapshot_count + 1
  WHERE id = p_arc_id AND sealed = false;
$$;
