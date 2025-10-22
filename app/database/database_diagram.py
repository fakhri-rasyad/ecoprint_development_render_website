from sqlalchemy_schemadisplay import create_schema_graph
from sqlalchemy import create_engine, MetaData

engine = create_engine("sqlite:///ecoprint.db")
metadata = MetaData()
metadata.reflect(engine)

graph = create_schema_graph(metadata=metadata, engine=engine)
graph.write_png("schema.png")