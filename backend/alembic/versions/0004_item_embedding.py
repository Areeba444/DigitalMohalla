"""Schema v2.4, part 3: item_embedding for meaning-based search (A9, ADR-0016)

Applies `alembic/sql/0004_item_embedding.sql`: the pgvector extension and the `item_embedding`
table of the design migration, created only where the server offers pgvector. Additive only.

Revision ID: 0004
Revises: 0003
"""
from pathlib import Path

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parents[1] / "sql" / "0004_item_embedding.sql"


def upgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute(SQL_FILE.read_text(encoding="utf-8"))
    cursor.execute("RESET search_path")  # the script sets dm, public for itself


def downgrade() -> None:
    raise NotImplementedError("schema v2.4 is forward-only; drop schema dm and migrate to 0001 instead")
