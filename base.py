from sqlalchemy import Column , create_engine , Integer , String
from sqlalchemy.orm import declarative_base

engine = create_engine("sqlite:///database.db")
Base = declarative_base()

class TagList (Base):
    __tablename__ = "tags"
    id = Column(Integer , primary_key=True )
    tag_id = Column (Integer)
    count = Column(Integer)
    name = Column("tag_name" , String)

    def __init__(self , tag_id , name , count):
        self.tag_id = tag_id
        self.name = name
        self.count = count


Base.metadata.create_all(engine)