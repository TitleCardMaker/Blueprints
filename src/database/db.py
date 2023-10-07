from json import dumps

from sqlalchemy import (
    Column, DateTime, Integer, String, ForeignKey, create_engine, func, or_
)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


DATABASE_URL = 'sqlite:///./blueprints.db'


# Define the SQLite database connection
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})

# Create a session to interact with the database
SessionLocal = sessionmaker(
    bind=engine, expire_on_commit=False, autocommit=False, autoflush=False,
)
db = SessionLocal()

# Create a base class for declarative table definitions
Base = declarative_base()


# SQL Tables
class Series(Base):
    __tablename__ = 'series'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    path_name = Column(String, nullable=False)

    # Database arguments
    imdb_id = Column(String, default=None)
    tmdb_id = Column(Integer, default=None)
    tvdb_id = Column(Integer, default=None)

    blueprints = relationship('Blueprint', back_populates='series')


class Blueprint(Base):
    __tablename__ = 'blueprints'

    id = Column(Integer, primary_key=True)
    series_id = Column(Integer, ForeignKey('series.id'))
    blueprint_number = Column(Integer, nullable=False)

    creator = Column(String, nullable=False)
    created = Column(DateTime, nullable=False, default=func.now())
    json = Column(String, nullable=False)

    series = relationship('Series', back_populates='blueprints')


# Create the tables in the database only if they do not exist
Base.metadata.create_all(engine, checkfirst=True)


def create_new_blueprint(
        series_name: str,
        series_year: int,
        fallback_path_name: str,
        database_ids: dict,
        creator: str,
        blueprint_json: str,
    ) -> tuple[Series, Blueprint]:
    """
    Create a Blueprint (and optionally a Series) for the given data.
    """

    id_conditions = []
    if database_ids.get('imdb'):
        id_conditions.append(Series.imdb_id==database_ids['imdb'])
    if database_ids.get('tmdb'):
        id_conditions.append(Series.tmdb_id==database_ids['tmdb'])
    if database_ids.get('tvdb'):
        id_conditions.append(Series.tvdb_id==database_ids['tvdb_id'])

    # Try and find by database ID
    series = db.query(Series).filter(or_(*id_conditions)).first()
    if not id_conditions or not series:
        # If not found, match by name + year
        series = db.query(Series)\
            .filter_by(name=series_name, year=series_year)\
            .first()

    # If not found, create new Series
    if not series:
        ids = {f'{id_type}_id': id_ for id_type, id_ in database_ids.items()}
        series = Series(
            name=series_name, year=series_year, path_name=fallback_path_name,
            **ids
        )
        db.add(series)
        db.commit()
        print(f'Added {series_name} ({series_year}) to Database as Series[{series.id}]')
    
    # Series exists; create Blueprint
    if (created := blueprint_json.get('created')):
        from datetime import datetime
        created = datetime.strptime(created, '%Y-%m-%dT%H:%M:%S')

    blueprint = Blueprint(
        series_id=series.id, blueprint_number=len(series.blueprints),
        creator=creator, created=created, json=dumps(blueprint_json),
    )
    db.add(blueprint)
    db.commit()
    print(f'Created Blueprint[{blueprint.id}]')

    return series, blueprint
