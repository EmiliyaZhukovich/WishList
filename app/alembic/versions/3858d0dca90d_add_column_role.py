"""add column role

Revision ID: 3858d0dca90d
Revises: 7c838b076a09
Create Date: 2025-12-22 10:22:28.685830

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3858d0dca90d'
down_revision: Union[str, Sequence[str], None] = '7c838b076a09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    role_enum = postgresql.ENUM('USER', name='roleenum', create_type=False)

    # Проверяем, существует ли тип
    connection = op.get_bind()

    # Создаем тип ENUM если не существует
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'roleenum') THEN
                CREATE TYPE roleenum AS ENUM ('USER');
            END IF;
        END$$;
    """)

    # Добавляем колонку role с default значением 'USER'
    op.add_column('users',
        sa.Column('role',
            sa.Enum('USER', name='roleenum'),
            nullable=False,
            server_default='USER'
        )
    )


def downgrade() -> None:
    op.drop_column('users', 'role')

    op.execute("DROP TYPE IF EXISTS roleenum")
