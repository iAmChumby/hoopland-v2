from sqlalchemy import create_engine, Column, Integer, String, JSON, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (
        # Allow same player in multiple seasons
        UniqueConstraint("source_id", "season", "league", name="uq_player_season"),
    )

    id = Column(Integer, primary_key=True)
    source_id = Column(String, nullable=False)  # NBA/ESPN ID (NOT unique alone)
    league = Column(String, nullable=False)  # 'NBA' or 'NCAA'
    season = Column(String, nullable=False)  # '2023-24'
    name = Column(String, nullable=False)
    team_id = Column(String)
    raw_stats = Column(JSON)  # The full API payload
    appearance = Column(JSON)  # Cached CV results: skin_tone, hair_color


def init_db(db_path="sqlite:///hoopland.db"):
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
