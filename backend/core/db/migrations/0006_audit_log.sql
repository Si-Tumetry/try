-- DATABASE.md §4.16. Append only: a trigger refuses UPDATE and DELETE for every role, including the owner.
CREATE TABLE audit_log (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_id text,
    actor_role text NOT NULL,
    door text NOT NULL CHECK (door IN ('rest', 'mcp', 'admin', 'worker')),
    operation text NOT NULL,
    args_hash text NOT NULL,
    result text NOT NULL CHECK (result IN ('ok', 'denied', 'not_found', 'error')),
    request_id text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ix_audit_log_created ON audit_log (created_at);

CREATE FUNCTION audit_log_append_only() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append only';
END;
$$;

CREATE TRIGGER trg_audit_log_append_only
BEFORE UPDATE OR DELETE ON audit_log
FOR EACH ROW EXECUTE FUNCTION audit_log_append_only();
