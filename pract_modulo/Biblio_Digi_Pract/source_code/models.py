from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import * 
from abc import ABC, abstractmethod



class UserDB(Base):
    
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True, nullable=False)
    date_added = Column(DateTime(timezone=True), server_default=func.now())
    hashed_password = Column(String, nullable=False)
    contact_mail = Column(String, unique=True, index=True, nullable=False)
    age = Column(Integer, index=True, nullable=True)
    
    loans = relationship("Loan_DB", back_populates="user_resp")
    
    
    # def __init__(self, name: str, mail: str, passwd: str,  age: int = None):
    #     self.full_name = name
    #     self.contact_mail = mail
    #     self.hashed_password = passwd
    #     self.age = age
    

# La idea es que tanto las peliculas como los libros tengan atributos en comun y aplicando herencia posteriormente cada uno tenga sus particularidades
class Library_Item:
    
    def __init__(self, name: str):
        self._name = name
        self._available = True
        # self.genre_id = genre
    
    @property
    def name(self):
        return self._name
    
    @property
    def status(self):
        return self.available # si esta disponible o no en nuestra web para alquilar este item
    
    def item_took(self):
        self.available = False
    
    def item_returned(self):
        self.available = True
        
    @abstractmethod
    def get_item_type(self):
        pass # para decir que está aquilando el usuario
    
    @abstractmethod
    def get_ref_numb(self):
        pass


class Film_DB(Base, Library_Item):
    
    __tablename__ = "films"
    
    ref_number = Column(Integer, primary_key=True, index=True)
    # It is typically not desirable to have “autoincrement” enabled on a column that refers to another via foreign key, as such a column is required to refer to a value that originates from elsewhere.
    name = Column(String, unique=True, index=True)
    actors = Column(String, nullable=True) # Aquí hemos quitado el indice (index=True) porque la lista de actores se pasara como un string donde vendran separados por comas
    available = Column(Boolean, default=True, nullable=False) # Inicialmente lo declaramos a true porque si lo hemos añadido a la BDD es porque lo tenemos
    date_registered = Column(DateTime(timezone=True), server_default=func.now())
    genre_id = Column(Integer, ForeignKey("genero.genre_id"), nullable=False)
    
    genres = relationship("Genre_DB", back_populates="films")
    loans = relationship("Loan_DB", back_populates="film_loaned")
    
    
    # def __init__(self, name: str, actors: str):
    #     super().__init__(name)
    #     self.actors = actors

       
    def get_item_type(self):
        return "Film"
    
    def get_ref_numb(self):
        return self.ref_number
    
    def actors_listing(self):
        actors_list = self.actors.split(",")
        l = dict()
        if actors_list:
            elem_added = 0
            l["Info"] = "Film casting"
            for a in actors_list:
                l[f"A{elem_added}"] = a.strip()
                elem_added +=1
        return l   
        


class Book_DB(Base, Library_Item):
    
    __tablename__ = "books"
    
    ref_number = Column(Integer, primary_key=True, index=True)
    # It is typically not desirable to have “autoincrement” enabled on a column that refers to another via foreign key, as such a column is required to refer to a value that originates from elsewhere.
    name = Column(String, unique=True, index=True)
    author = Column(String, index=True)
    available = Column(Boolean, default=True, nullable=False) # Inicialmente lo declaramos a true porque si lo hemos añadido a la BDD es porque lo tenemos
    date_registered = Column(DateTime(timezone=True), server_default=func.now())
    genre_id = Column(Integer, ForeignKey("genero.genre_id"), nullable=False)
    
    genres = relationship("Genre_DB", back_populates="books")
    loans = relationship("Loan_DB", back_populates="book_loaned")
    
    
    # def __init__(self, name: str, author: str):
    #     super().__init__(name)
    #     self.author = author
              
    def get_item_type(self):
        return "Book"
    
    def get_ref_numb(self):
        return self.ref_number
    

class Genre_DB(Base):
    
    __tablename__ = "genero"
    
    genre_id = Column(Integer, primary_key=True, index=True)
    genre_name = Column(String, unique=True, index=True, nullable=False)

    books = relationship("Book_DB", back_populates="genres")
    films = relationship("Film_DB", back_populates="genres")
    
    
    # def __init__(self, name):
    #     self.genre_name = name

    


class Loan_DB(Base):
    
    __tablename__ = "prestamo"
    
    loan_id = Column(Integer, primary_key=True, index=True)
    loan_date = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False) # Un préstamo siempre tiene un usuario
    book_ref_number = Column(Integer, ForeignKey("books.ref_number"), nullable=True)
    film_ref_number = Column(Integer, ForeignKey("films.ref_number"), nullable=True)
    return_date = Column(DateTime(timezone=True), nullable=True)
    
    user_resp = relationship("UserDB", back_populates="loans")
    book_loaned = relationship("Book_DB", back_populates="loans")
    film_loaned = relationship("Film_DB", back_populates="loans")
    
    # def __init__(self, user_id: int, book_ref_number: int, film_ref_number: int):
    #     self.user_id=user_id
    #     self.book_ref_number=book_ref_number
    #     self.film_ref_number=film_ref_number
    


# Estas tablas para las relaciones N:M de mi diagrama. Tablas de asociación Many to Many
    
# film_genre_association_table = Table(
#         "film_genre_association", Base.metadata,
#         Column("film_ref_number", Integer, ForeignKey("films.ref_number"), primary_key=True),
#         Column("genre_id", Integer, ForeignKey("genero.genre_id"), primary_key=True)
#     )
    
    
# book_genre_association_table = Table(
#         "book_genre_association", Base.metadata,
#         Column("book_ref_number", Integer, ForeignKey("books.ref_number"), primary_key=True),
#         Column("genre_id", Integer, ForeignKey("genero.genre_id"), primary_key=True)
#     )
    