"""Schema v2.4, part 1: pg_trgm, three lifecycle v3 event types and the new enum types (F1)

Applies `alembic/sql/0002_schema_v2_4_types.sql`, part 1 of the design migration
docs/design/06_data_model/migration_0002_schema_v2_4.sql (DA-09). It is its own revision because
PostgreSQL cannot use a new enum value in the transaction that adds it; env.py commits after each
revision, so revision 0003 can insert transitions that use `counter_offered` and friends.

Revision ID: 0002
Revises: 0001
"""
from pathlib import Path

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parents[1] / "sql" / "0002_schema_v2_4_types.sql"


def upgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute(SQL_FILE.read_text(encoding="utf-8"))
    cursor.execute("RESET search_path")  # the script sets dm, public for itself


def downgrade() -> None:
    # Enum values cannot be removed in PostgreSQL; going below v2.4 means rebuilding from revision 0001.
    raise NotImplementedError("schema v2.4 is forward-only; drop schema dm and migrate to 0001 instead")
