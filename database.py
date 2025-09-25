from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from vial.config import app_config
import pc_configuration

engine = create_engine(app_config.get(pc_configuration.DB_CONNECTION_STRING))
DBSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
