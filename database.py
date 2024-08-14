from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Variables para los componentes de la conexión.
USER = 'b4b6bc8e814c28'
PASSWORD = '14e1b66b'
HOST = 'us-cluster-east-01.k8s.cleardb.net'
DATABASE = 'heroku_e9b0dc7aefbadfa'
LLAVE = b'_5#y2L"F4Q8z\n\xec]/'

TESTING = os.environ.get('TESTING', 'False')

if TESTING == 'True':
    engine = create_engine('sqlite:///:memory:', echo=True)
else:
    # Crear el engine utilizando las variables de conexión reales.
    engine = create_engine(
        f'mysql://{USER}:{PASSWORD}@{HOST}/{DATABASE}',
        pool_recycle=3600,
        pool_pre_ping=True
    )

# Crea una instancia de Session.
Session = sessionmaker(bind=engine)
session = Session()

# Función para obtener la instancia de la sesión.
def get_session():
    return session
