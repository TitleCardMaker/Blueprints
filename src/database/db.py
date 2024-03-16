from datetime import datetime
from json import dumps
from pathlib import Path
from sys import exit as sys_exit
from typing import Any, Iterable, Optional

from sqlalchemy import Column, ForeignKey, Table, create_engine, func, or_
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
)

__all__ = (
    'DATABASE_URL', 'db', 'Base', 'Series', 'Blueprint', 'Set',
    'create_new_blueprint', 'create_new_set',
)


DATABASE_URL = 'sqlite:///./blueprints.db'


# Define the SQLite database connection
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})

# Create a session to interact with the database
SessionLocal = sessionmaker(
    bind=engine, expire_on_commit=False, autocommit=False, autoflush=False,
)
db = SessionLocal()

# Create a base class for declarative table definitions
class Base(DeclarativeBase):
    ...

# Association tables
association_table = Table(
    'association_table',
    Base.metadata,
    Column('blueprint_id', ForeignKey('blueprints.id'), primary_key=True),
    Column('set_id', ForeignKey('sets.id'), primary_key=True),
)

# SQL Tables
class Series(Base):
    __tablename__ = 'series'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    year: Mapped[int]
    path_name: Mapped[str]

    # Database arguments
    imdb_id: Mapped[Optional[str]]
    tmdb_id: Mapped[Optional[int]]
    tvdb_id: Mapped[Optional[int]]

    blueprints: Mapped[list['Blueprint']] = relationship(back_populates='series')


class Blueprint(Base):
    __tablename__ = 'blueprints'

    id: Mapped[int] = mapped_column(primary_key=True)
    series_id: Mapped[int] = mapped_column(ForeignKey('series.id'))
    blueprint_number: Mapped[int]

    creator: Mapped[str]
    created: Mapped[datetime] = mapped_column(default=func.now())
    json: Mapped[str]

    series: Mapped['Series'] = relationship(back_populates='blueprints')
    sets: Mapped[list['Set']] = relationship(
        secondary=association_table, back_populates='blueprints'
    )


class Set(Base):
    __tablename__ = 'sets'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    blueprints: Mapped[list[Blueprint]] = relationship(
        secondary=association_table, back_populates='sets',
    )

# Create the tables in the database only if they do not exist
Base.metadata.create_all(engine, checkfirst=True)


def create_new_blueprint(
        series_name: str,
        series_year: int,
        fallback_path_name: str,
        database_ids: dict,
        creator: str,
        blueprint_json: dict[str, Any],
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
        id_conditions.append(Series.tvdb_id==database_ids['tvdb'])

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

    # Get Bluprint number
    blueprint_number = db.query(func.max(Blueprint.blueprint_number))\
        .filter_by(series_id=series.id)\
        .scalar()
    if blueprint_number is None:
        blueprint_number = 0
    else:
        blueprint_number +=1 

    if (created := blueprint_json.pop('created', None)):
        created = datetime.strptime(created, '%Y-%m-%dT%H:%M:%S')

    # Create Blueprint, add to Database
    blueprint = Blueprint(
        series_id=series.id, blueprint_number=blueprint_number,
        creator=creator, created=created, json=dumps(blueprint_json),
    )
    db.add(blueprint)
    db.commit()
    print(f'Created Blueprint[{blueprint.id}]')

    return series, blueprint


def _find_blueprint(path: str | Path, /) -> Blueprint:
    """
    Get the Blueprint object associated with the given blueprint
    subfolder.

    Args:
        path: Path to the Blueprint being queried.

    Returns:
        Blueprint object from the database.

    Raises:
        SystemExit (1): The associated Series or Blueprint cannot be
            found.
    """

    # Find associated Series
    path = Path(path)
    series = db.query(Series)\
        .filter_by(path_name=path.parent.name)\
        .first()
    if not series:
        print(f'Cannot find Series associated with "{path}"')
        sys_exit(1)

    # Find Blueprint
    blueprint = db.query(Blueprint)\
        .filter_by(series_id=series.id,
                   blueprint_number=int(path.name))\
        .first()
    if not blueprint:
        print(f'Cannot find Blueprint #{path.name} for Series[{series.id}] {series.name}')
        sys_exit(1)

    return blueprint


def create_new_set(name: str, blueprint_paths: Iterable[str]) -> Set:
    """
    Create a new Set of the given data. This parses all provided paths
    and finds the associated Blueprint objects for adding to the
    association table.
    """

    bp_set = Set(
        name=name,
        blueprints=[_find_blueprint(path) for path in blueprint_paths],
    )

    db.add(bp_set)
    db.commit()

    return bp_set
