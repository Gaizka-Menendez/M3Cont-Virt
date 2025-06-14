from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DB_HOST = os.getenv('DB_HOST', 'localhost') 
DB_PORT = os.getenv('DB_PORT', '5432')     
DB_USER = os.getenv('DB_USER', 'user_biblioteca') 
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password_biblioteca') 
DB_NAME = os.getenv('DB_NAME', 'db_biblioteca') 

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
Local_Session = sessionmaker(bind=engine, autocommit=False, autoflush=False) 
# autocommit es False porque nosotros somos los que queremos confirmar cuando commitear esos cambios
# bind = engine cada sesion creada que use el engine creado
Base = declarative_base()
# clase base para nuestros modelos, es decir cada clase declarada con Base le indicamos a SQL Alchemy que esa clase en concreto será una tabla de la BBDD

# Esta función (get_db) servirá como generador de sesiones de nuestra BD además de asegurarse su correcta gestion en los diferentes
# endpoints que requieran del uso de conexión. Se indica con Depends
def get_db():
    db = Local_Session()
    try:
        yield db
    finally:
        db.close()