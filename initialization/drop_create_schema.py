from database import Base, engine
from dbe.docs import docs_et_tag

if __name__ == "__main__":
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)