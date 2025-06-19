from db.database import Base, engine
from models import *

Base.metadata.create_all(bind=engine)