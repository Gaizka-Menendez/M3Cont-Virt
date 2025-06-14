from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

LIBRARY_DATABASE_URL = "sqlite:///./library_app.db"

engine = create_engine(LIBRARY_DATABASE_URL, connect_args={"check_same_thread": False})
Local_Session = sessionmaker(bind=engine, autocommit=False, autoflush=False) 
# autocommit es False porque nosotros somos los que queremos confirmar cuando commitear esos cambios
# bind = engine cada sesion creada que use el engine creado
Base = declarative_base()
# clase base para nuestros modelos, es decir cada clase declarada con Base le indicamos a SQL Alchemy que esa clase en concreto será una tabla de la BBDD