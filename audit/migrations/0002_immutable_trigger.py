"""PostgreSQL trigger that blocks UPDATE/DELETE on the audit table (HMS-SR-004, SAD ADR-07).

Skipped on SQLite (local quick-start); CI and Docker run PostgreSQL, so it is enforced there.
"""
from django.db import migrations

CREATE = """
CREATE OR REPLACE FUNCTION audit_log_immutable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_auditlog is append-only';
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER audit_log_no_update_delete
    BEFORE UPDATE OR DELETE ON audit_auditlog
    FOR EACH ROW EXECUTE FUNCTION audit_log_immutable();
"""
DROP = """
DROP TRIGGER IF EXISTS audit_log_no_update_delete ON audit_auditlog;
DROP FUNCTION IF EXISTS audit_log_immutable();
"""


def forwards(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(CREATE)


def backwards(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(DROP)


class Migration(migrations.Migration):
    dependencies = [("audit", "0001_initial")]
    operations = [migrations.RunPython(forwards, backwards)]
