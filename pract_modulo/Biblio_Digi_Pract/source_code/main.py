from .database import *
from .models import *
from .validators import *
from fastapi import FastAPI, Body, BackgroundTasks, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
import logging
import bcrypt
from sqlalchemy import or_, and_, DateTime

Base.metadata.create_all(bind=engine)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="My_Digital_Library",
    description="API para la Gestión de la Biblioteca Digital",
    version="1.0.0", 
    debug=True  # He añadido esta opción porque en la docu vi que era util para ver el registro de errores o causas de los posibles fallos
)

# Esta función (get_db) servirá como generador de sesiones de nuestra BD además de asegurarse su correcta gestion en los diferentes
# endpoints que requieran del uso de conexión. Se indica con Depends
def get_db():
    db = Local_Session()
    try:
        yield db
    finally:
        db.close()
        

# Funcion para cifrar la contraseña del usuario
def hash_password(pwd: str):
    pwd_to_encode = pwd.encode("utf-8")
    sal = bcrypt.gensalt()
    encripted_pwd = bcrypt.hashpw(pwd_to_encode, sal)
    return encripted_pwd.decode("utf-8")


# Crear usuarios y registrarlos en la BD
@app.post("/Usuarios/", status_code=status.HTTP_201_CREATED)
async def create_user(user: User, db: Session = Depends(get_db)):
    logger.info("Petición recibida para crear un nuevo usuario con los datos indicados")
    # Verificamos primero si su nombre o correo ya estan dados ya existen en la BDD.
    if db.query(UserDB).filter(UserDB.contact_mail==user.contact_mail).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El usuario o el correo proporcionados ya existen en la base de datos.")
    logger.info("Cifrando contraseña del usuario...")
    # para la contraseña del usuario la cifraremos haciendo uso de la librería bcrypt
    psswd_str = hash_password(user.hashed_password)
    logger.info("Contraseña cifrada!")
    usr_toadd = UserDB(full_name=user.full_name, contact_mail=user.contact_mail, hashed_password=psswd_str, age=user.age)
    db.add(usr_toadd)
    db.commit()
    # añadimos al usuario a la base de datos
    db.refresh(usr_toadd)
    logger.info(f"Usuario {user.full_name} registrado en la BDD correctamente")
    
    return usr_toadd


# Obtener usuarios por el nombre en caso de haber mas de uno con el mismo nombre, que puede ocurrir, devolver la lista de todos
@app.get("/Usuarios/{name}", status_code=status.HTTP_200_OK)
def get_user(name: str, db: Session = Depends(get_db)):
    logger.info("Petición recibida para obtener la información de un usuario")
    existing = db.query(UserDB).filter(UserDB.full_name==name).all()
    # Aqui indico que coja todos, ya que puede haber un caso en el que existan dos usuarios que comiencen por el mismo nombre pero que no tengan nada que ver
    # y en ese caso entiendo que lo mejor es sacar todos los que se llamen de esa forma y ya decidir con cual te quedas.
    if not(existing):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El usuario no existe en la BDD")
    logger.info("Petición resuelta")
    return existing

# Modificación parcial de un usuario, se prodría haber hecho un put pero entiendo que si te has equivocado en todo lo borras y creas uno nuevo. 
@app.patch("/Usuarios/{user_id}/Perfil_de_usuario", status_code=status.HTTP_200_OK)
def modify_user_fields(user_update: UserUpdate, user_id: int = Path(..., description="ID del usuario a modificar"),  db: Session = Depends(get_db)):
    logger.info(f"Petición recibida para modificar el usuario con ID: {user_id}")
    existing_user = db.query(UserDB).filter(UserDB.user_id==user_id).first()
    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Este usuario no esta registrado en la BDD")
    update_data = user_update.model_dump(exclude_unset=True)
    logger.info(f"Modificando los registros indicados")
    if "hashed_password" in update_data:
        # Si se tiene que actualizar la contraseña llamamos a la función de cifrado
        pwd_ciphered = hash_password(update_data["hashed_password"])
        # setattr he visto en un video que es la forma correcta de modificar las variables de un registro, inicialmente intentaba acceder a esas con un .update a traves de consulta o con [],
        # cosa que segun lei no era muy buena practica
        setattr(existing_user, "hashed_password", pwd_ciphered)
    for key, value in update_data.items():
        if key != "hashed_password":
            setattr(existing_user, key, value)
    db.commit()
    db.refresh(existing_user)
    logger.info(f"Peticion resuelta")
    
    return existing_user
    
        
# Creacíon y registro de un libro, para este caso pense que si el genero del libro no existia convendria añadirlo para ya tenerlo de cara a futuras adiciones
@app.post("/Libros/", status_code=status.HTTP_201_CREATED)
def create_book(book: Book, genre_name: Optional[str] = Query(None, description="Nombre del género a añadir (opcional)"), db: Session = Depends(get_db)):
    logger.info(f"Recibida petición para añadir a la BDD el libro {book.name}")
    logger.info("Procesando el genero del libro pasado por parámetro")
    if genre_name:
        genre = db.query(Genre_DB).filter(Genre_DB.genre_name==genre_name).first()
        if genre is None: #Si no existe ese género en la BDD lo incluimos
            logger.info(f"El género '{genre_name}' no existe. Creando nuevo género.")
            new_genre = Genre_DB(genre_name=genre_name)
            db.add(new_genre)
            db.commit()
            db.refresh(new_genre)
            logger.info(f"El género '{genre_name}' se ha registrado correctamente.")
        else:
            new_genre = genre
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "Debe especificarse el género de la nueva película")
    
    existing = db.query(Book_DB).filter(Book_DB.name==book.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este libro ya se ha registrado")
    b = Book_DB(name=book.name, author=book.author)
    b.genre_id = new_genre.genre_id
    db.add(b)
    db.commit()
    db.refresh(b)
    logger.info(f"Libro {b.name} registrado en la BDD correctamente")
    
    return b


@app.get("/Libros/{name}", status_code=status.HTTP_200_OK)
def get_book(name: str, db: Session = Depends(get_db)):
    logger.info("Petición recibida para obtener la información de un libro")
    existing = db.query(Book_DB).filter(Book_DB.name==name).first()
    if not(existing):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El libro no esta registrado en la BDD")
    logger.info("Petición resuelta")
    return existing



# /Peliculas/?genre_name=Accion el parámetro genre_name lo que hace es que se pase ese parámetro en la ruta también de forma

# Esta función la plantee de forma que tu creases una película y despues que a traves de un parámetro pasado por entrada (en este caso lo vi en stackoverflow) se pudiesen adjuntar 4
# parámetros adicionales como el género de una película a la URL wue apunta ese endpoint
@app.post("/Peliculas/", status_code=status.HTTP_201_CREATED)
def create_film(film: Film, genre_name: Optional[str] = Query(None, description="Nombre del género a añadir (opcional)"), db: Session = Depends(get_db)):
    logger.info(f"Recibida petición para añadir a la BDD la pelicula {film.name}")
    logger.info("Procesando el genero pasado por parámetro")
    if genre_name:
        genre = db.query(Genre_DB).filter(Genre_DB.genre_name==genre_name).first()
        if genre is None:
            logger.info(f"El género '{genre_name}' no existe. Creando nuevo género.")
            new_genre = Genre_DB(genre_name=genre_name)
            db.add(new_genre)
            db.commit()
            db.refresh(new_genre)
            logger.info(f"El género '{genre_name}' se ha registrado correctamente.")
        else:
            new_genre = genre
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "Debe especificarse el género de la nueva película")
    # Ahora que ya hemos gestionado el tema del género vamos a ver que hacemos con la película
    
    existing = db.query(Film_DB).filter(Film_DB.name==film.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esta pelicula ya se encuentra registrada")

    # film.genre_id=new_genre.genre_id 
    f = Film_DB(name=film.name, actors=film.actors)
    f.genre_id = new_genre.genre_id
    db.add(f)
    db.commit()
    db.refresh(f)
    logger.info(f"Pelicula {f.name} registrada en la BDD correctamente")
    
    return f


@app.get("/Peliculas/{name}", status_code=status.HTTP_200_OK)
def get_film(name: str, db: Session = Depends(get_db)):
    logger.info("Petición recibida para obtener la información de una pelicula")
    existing = db.query(Film_DB).filter(Film_DB.name==name).first()
    if not(existing):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La pelicula no esta registrada en la BDD")
    logger.info("Petición resuelta")
    return existing


@app.get("/Peliculas/{name}/actors", status_code=status.HTTP_200_OK)
def get_film_actors(name: str, db: Session = Depends(get_db)):
    logger.info("Petición recibida para obtener la información de una pelicula")
    existing = db.query(Film_DB).filter(Film_DB.name==name).first()
    if not(existing):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La pelicula no esta registrada en la BDD")
    logger.info("Petición resuelta")
    return existing.actors_listing()


@app.post("/Generos/", status_code=status.HTTP_201_CREATED)
def create_genre(gen: Genre, db: Session = Depends(get_db)):
    logger.info(f"Recibida petición para añadir a la BDD la pelicula {gen.genre_name}")
    existing = db.query(Genre_DB).filter(Genre_DB.genre_name==gen.genre_name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este género ya se encuentra registrado")
    g = Genre_DB(genre_name=gen.genre_name)
    db.add(g)
    db.commit()
    db.refresh(g)
    logger.info(f"Género {g.genre_name} registrado en la BDD correctamente")
    
    return g


@app.get("/Generos/{name}", status_code=status.HTTP_200_OK)
def get_genre(name: str, db: Session = Depends(get_db)):
    logger.info("Petición recibida para obtener la información de un genero en concreto")
    existing = db.query(Genre_DB).filter(Genre_DB.genre_name==name).first()
    if not(existing):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Este género no esta registrado en la BDD")
    logger.info("Petición resuelta")
    return existing


# Esta funcion permite verificar si es posible realizar un préstamo analizando la disponibilidad de lo que pide el usuario en una solicitud. En caso de alguno de los productos no estar disponibles 
# devolverá el error 409 de que no se puede acceder a ese recurso
@app.post("/Realizar_un_prestamo/", status_code=status.HTTP_201_CREATED)
def loan_articles( user: User, book: Book = None, film: Film = None, db: Session = Depends(get_db)):
    logger.info("Petición recibida para realizar un préstamo")
    ref_book = None
    ref_film = None
    if book is None and film is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Error, no se puede realizar un préstamo de nada")
    existing_user = db.query(UserDB).filter(and_(UserDB.full_name==user.full_name, UserDB.contact_mail==user.contact_mail)).first()
    if existing_user:
        logger.info("Analisis del libro solicitado")
        if book:
            existing_book = db.query(Book_DB).filter(Book_DB.name==book.name).first()
            if not(existing_book) or not(existing_book.available):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Error, el recurso con nombre {book.name} no existe o no se encuentra disponible")
            logger.info("Libro disponible!")
            existing_book.item_took() # con las funciones de la clase abstaracte decimos que han cogido ese item
            db.add(existing_book)
            # db.refresh(existing_book)
            ref_book = existing_book.ref_number
        logger.info("Analisis de la película solicitada") 
        if film:  
            existing_film = db.query(Film_DB).filter(Film_DB.name==film.name).first()
            if not(existing_film) or not(existing_film.available):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Error, el recurso con nombre {film.name} no existe o no se encuentra disponible")
            logger.info("Pelicula disponible!")
            existing_film.item_took()
            db.add(existing_film)
            # db.refresh(existing_film)
            ref_film = existing_film.ref_number
        logger.info("Analisis completado. Procediendo a registrar el prestamo")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario que se indica que realiza el préstamo no existe")
    id_user = existing_user.user_id
    l = Loan_DB(user_id=id_user, book_ref_number=ref_book, film_ref_number=ref_film)
    db.add(l)
    db.commit()
    db.refresh(l)
    
    return l

# Aqui lo que se pretende es poder gestionar el tema de las devoluciones de los prestamos.
@app.patch("/Devolver_prestamo/", status_code=status.HTTP_200_OK)
def loan_returned(loan: Loan, db: Session = Depends(get_db)):
    logger.info("Petición recibida para devolver un préstamo")
    logger.info("Verificamos que el préstamo es correcto")
    # Aqui verificamos la casuística del préstamo, si sera de libro y peli, solo libro o solo peli
    if loan.film_ref_number and loan.book_ref_number:
        existing_loan = db.query(Loan_DB).filter(and_(Loan_DB.user_id==loan.user_id, Loan_DB.book_ref_number==loan.book_ref_number, Loan_DB.film_ref_number==loan.film_ref_number)).first()
    elif loan.film_ref_number and loan.book_ref_number is None:
        existing_loan = db.query(Loan_DB).filter(and_(Loan_DB.user_id==loan.user_id, Loan_DB.film_ref_number==loan.film_ref_number)).first()
    elif loan.film_ref_number is None and loan.book_ref_number:
        existing_loan = db.query(Loan_DB).filter(and_(Loan_DB.user_id==loan.user_id, Loan_DB.book_ref_number==loan.book_ref_number)).first()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puede existir un préstamo donde no se haya prestado nada!!")
    if(existing_loan):
        logger.info("Procedemos a ver que es exactamente lo que se ha prestado")
        if existing_loan.book_ref_number:
            existing_book = db.query(Book_DB).filter(Book_DB.ref_number==existing_loan.book_ref_number).first()
            existing_book.item_returned() # Empleamos las funciones declaradas en la clase abstracta para reflejar la devolución de los item
            db.add(existing_book)
            # db.refresh(existing_book)
        if existing_loan.film_ref_number:
            existing_film = db.query(Film_DB).filter(Film_DB.ref_number==existing_loan.film_ref_number).first()
            existing_film.item_returned()
            db.add(existing_film)
            # db.refresh(existing_film)
    else:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe el prestamo")       
    existing_loan.return_date = func.now()
    db.add(existing_loan)
    db.commit()
    db.refresh(existing_loan)
    
    return existing_loan

# Funciones para borrar los item de la BDD, libros y películas. Para el caso de géneros, usuarios o prestamos no lo considero interesante pues siempre conviene tener registros de esas tablas
@app.delete("/Libros/{ref_number}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(ref_number: int, db: Session = Depends(get_db)):
    logger.info(f"Petición de borrado del libro con referencia: {ref_number}")
    existing_book = db.query(Book_DB).filter(Book_DB.ref_number==ref_number).first()
    if existing_book:
        db.delete(existing_book)
        db.commit()
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "No se ha encontrado el registro correspondiente al libro que hay que borrar")
    
    
@app.delete("/Peliculas/{ref_number}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_film(ref_number: int, db: Session = Depends(get_db)):
    logger.info(f"Petición de borrado del libro con referencia: {ref_number}")
    existing_film = db.query(Film_DB).filter(Film_DB.ref_number==ref_number).first()
    if existing_film:
        db.delete(existing_film)
        db.commit()
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "No se ha encontrado el registro correspondiente a la pelicula que hay que borrar")