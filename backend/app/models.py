from sqlalchemy import Column, String, Integer, Float, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from .db import Base

json_type = JSON().with_variant(JSONB(), 'postgresql')
class Match(Base):
    __tablename__ = 'matches'
    id = Column(String, primary_key=True)
    source = Column(String, nullable=False)
    sha256 = Column(String, nullable=False)
    competition = Column(String, nullable=False, index=True)
    map_id = Column(String, nullable=False, index=True)
    map_name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    team_mapping = Column(json_type, nullable=False)
    payload = Column(json_type, nullable=False)

class KillEvent(Base):
    __tablename__ = 'kill_events'
    id = Column(String, primary_key=True)
    match_id = Column(String, ForeignKey('matches.id', ondelete='CASCADE'), nullable=False, index=True)
    round_num = Column(Integer, nullable=False)
    time_ms = Column(Integer, nullable=False)
    game_time_ms = Column(Integer, nullable=False)
    category = Column(String, nullable=False)  # enemy, self, friendly, unknown
    detail = Column(json_type, nullable=False)
    __table_args__ = (Index('ix_event_round_time', 'match_id', 'round_num', 'time_ms'),)

class Marker(Base):
    __tablename__ = 'markers'
    id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey('kill_events.id', ondelete='CASCADE'), nullable=False, index=True)
    map_id = Column(String, nullable=False, index=True)
    competition = Column(String, nullable=False, index=True)
    team = Column(String, nullable=False, index=True)
    player_id = Column(String, nullable=False, index=True)
    player_name = Column(String, nullable=False)
    side = Column(String, nullable=False)
    kind = Column(String, nullable=False)
    time_ms = Column(Integer, nullable=False)
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    __table_args__ = (Index('ix_marker_filter', 'map_id', 'kind', 'side', 'time_ms'),)
