from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '69f0c68ac5bc'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)

    op.create_table('github_installations',
    sa.Column('id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('account_login', sa.String(length=100), nullable=False),
    sa.Column('account_type', sa.String(length=20), nullable=False),
    sa.Column('repository_selection', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_github_installations_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_github_installations')),
    sa.UniqueConstraint('user_id', name=op.f('uq_github_installations_user_id'))
    )
    op.create_table('tracked_repositories',
    sa.Column('id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('installation_id', sa.BigInteger(), nullable=False),
    sa.Column('full_name', sa.String(length=200), nullable=False),
    sa.Column('default_branch', sa.String(length=255), nullable=False),
    sa.Column('description', sa.String(length=1000), nullable=True),
    sa.Column('language', sa.String(length=50), nullable=True),
    sa.Column('is_private', sa.Boolean(), nullable=False),
    sa.Column('stars', sa.Integer(), nullable=False),
    sa.Column('pr_number', sa.Integer(), nullable=True),
    sa.Column('pr_url', sa.String(length=500), nullable=True),
    sa.Column('pr_merged_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('scan_dispatched_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['installation_id'], ['github_installations.id'], name=op.f('fk_tracked_repositories_installation_id_github_installations'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_tracked_repositories_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tracked_repositories'))
    )
    with op.batch_alter_table('tracked_repositories', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_tracked_repositories_installation_id'), ['installation_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_tracked_repositories_user_id'), ['user_id'], unique=False)

    op.create_table('scans',
    sa.Column('id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('repository_id', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('trigger', sa.String(length=40), nullable=False),
    sa.Column('commit_sha', sa.String(length=40), nullable=False),
    sa.Column('run_url', sa.String(length=500), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('bom', sa.JSON(), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['repository_id'], ['tracked_repositories.id'], name=op.f('fk_scans_repository_id_tracked_repositories'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_scans'))
    )
    with op.batch_alter_table('scans', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_scans_repository_id'), ['repository_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('scans', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_scans_repository_id'))

    op.drop_table('scans')
    with op.batch_alter_table('tracked_repositories', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_tracked_repositories_user_id'))
        batch_op.drop_index(batch_op.f('ix_tracked_repositories_installation_id'))

    op.drop_table('tracked_repositories')
    op.drop_table('github_installations')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_email'))

    op.drop_table('users')
