"""Core schema v2.3 (design step A6)

Applies `alembic/sql/0001_schema_v2_3.sql`, the frozen baseline from
docs/design/06_data_model/schema.sql: tables, the transition table, the event and audit triggers,
the hash chain and the double-booking exclusion constraint. The lifecycle rules live in the database
by design (R2 in the schema header). Do not edit the SQL file; later changes are new migrations.

Revision ID: 0001
Revises:
"""
from pathlib import Path

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parents[1] / "sql" / "0001_schema_v2_3.sql"


def upgrade() -> None:
    sql = SQL_FILE.read_text(encoding="utf-8")
    # The script wraps itself in BEGIN/COMMIT; Alembic already runs the migration in a transaction.
    lines = [ln for ln in sql.splitlines() if ln.strip() not in ("BEGIN;", "COMMIT;")]
    cursor = op.get_bind().connection.cursor()
    cursor.execute("\n".join(lines))
    cursor.execute("RESET search_path")  # the script sets dm, public for itself


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS dm CASCADE")
