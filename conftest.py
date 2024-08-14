from database import engine, Session
from models import Base 
import pytest


# Configura la base de datos de prueba.
@pytest.fixture(scope='module')
def setup_database():
    # Crear las tablas en la base de datos de prueba.
    Base.metadata.create_all(engine)
    session = Session()
    session.commit()
    yield
    # Elimina las tablas después de las pruebas, excepto Region y Comuna.
    for table in reversed(Base.metadata.sorted_tables):
        if table.name not in ['region', 'comuna']:
            engine.execute(f'DROP TABLE IF EXISTS {table.name}')
    session.close()

# Configura la sesión de la base de datos de prueba.
@pytest.fixture(scope='function')
def session():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

# Fixture para limpiar objetos después de cada test
@pytest.fixture(autouse=True)
def cleanup_objects(session):
    yield
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()