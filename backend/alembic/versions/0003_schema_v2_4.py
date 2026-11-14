"""Schema v2.4, part 2: membership decisions, listings, search logs, notifications, job runs, lifecycle v3 (F1)

Applies `alembic/sql/0003_schema_v2_4.sql`, part 2 of the design migration
docs/design/06_data_model/migration_0002_schema_v2_4.sql (DA-09, DA-23): new tables and columns, the
lifecycle v3 guards (`event_validate_v3`: dispute exits by item possession, ADR-0009; counter-offer,
ADR-0015), and the five new `allowed_transition` rows. Every change is additive, so revision 0001 is
untouched. The pgvector table `item_embedding` is added later by the A9 migration (ADR-0016).

Revision ID: 0003
Revises: 0002
"""
from pathlib import Path

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parents[1] / "sql" / "0003_schema_v2_4.sql"


def upgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute(SQL_FILE.read_text(encoding="utf-8"))
    cursor.execute("RESET search_path")  # the script sets dm, public for itself


def downgrade() -> None:
    raise NotImplementedError("schema v2.4 is forward-only; drop schema dm and migrate to 0001 instead")
