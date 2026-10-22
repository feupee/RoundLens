"""Esquema inicial. Migrações futuras devem usar alterações explícitas."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
revision='0001'
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    j=sa.JSON().with_variant(JSONB(),'postgresql')
    op.create_table('matches',sa.Column('id',sa.String,primary_key=True),sa.Column('source',sa.String,nullable=False),sa.Column('sha256',sa.String,nullable=False),sa.Column('competition',sa.String,nullable=False),sa.Column('map_id',sa.String,nullable=False),sa.Column('map_name',sa.String,nullable=False),sa.Column('version',sa.String,nullable=False),sa.Column('team_mapping',j,nullable=False),sa.Column('payload',j,nullable=False))
    op.create_table('kill_events',sa.Column('id',sa.String,primary_key=True),sa.Column('match_id',sa.String,sa.ForeignKey('matches.id',ondelete='CASCADE'),nullable=False),sa.Column('round_num',sa.Integer,nullable=False),sa.Column('time_ms',sa.Integer,nullable=False),sa.Column('game_time_ms',sa.Integer,nullable=False),sa.Column('category',sa.String,nullable=False),sa.Column('detail',j,nullable=False))
    op.create_table('markers',sa.Column('id',sa.String,primary_key=True),sa.Column('event_id',sa.String,sa.ForeignKey('kill_events.id',ondelete='CASCADE'),nullable=False),sa.Column('map_id',sa.String,nullable=False),sa.Column('competition',sa.String,nullable=False),sa.Column('team',sa.String,nullable=False),sa.Column('player_id',sa.String,nullable=False),sa.Column('player_name',sa.String,nullable=False),sa.Column('side',sa.String,nullable=False),sa.Column('kind',sa.String,nullable=False),sa.Column('time_ms',sa.Integer,nullable=False),sa.Column('x',sa.Float),sa.Column('y',sa.Float))
    for table,cols in [('matches',['competition','map_id']),('kill_events',['match_id']),('markers',['event_id','map_id','competition','team','player_id'])]:
        for col in cols:op.create_index(f'ix_{table}_{col}',table,[col])
    op.create_index('ix_event_round_time','kill_events',['match_id','round_num','time_ms'])
    op.create_index('ix_marker_filter','markers',['map_id','kind','side','time_ms'])

def downgrade():
    for table in ['markers','kill_events','matches']:op.drop_table(table)
