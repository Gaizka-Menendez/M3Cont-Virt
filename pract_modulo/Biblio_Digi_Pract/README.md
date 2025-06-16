Author: Gaizka Menéndez Hernández

**Gestión de una Biblioteca de forma digital**.

La idea de esta práctica es desarrollar lo que podría ser una web online de una Biblioteca donde se llevane a cabo la gestión de los usuarios y de los libros de la misma. Es decir, que los usuarios puedan interactuar con la web de forma que puedan pedir préstamos o devolver libros y que todo esto quede registrado. Esta es la funcionalidad que busco conseguir.

A continuación voy a detallar un poco que es lo que ocurre en cada una de las clases del "source_code". Cada clase representa una funcionalidad o parte de la aplicación y así cumplimos el principio de Separación de Responsabilidades.



1. **database.py (BBDD de la app)**
    * Aquí se encuentra todo aquello relativo a la creación de la base de datos. Usamos la librería SQLAlchemy para definir la url de conexión a la BBDD, crear el engine, definimos la forma de crear las sesiones para operar sobre la BBDD y lo necesario para añadir tablas a nuestra BBDD.


2. **models.py y validators.py (schema class para la API y sus validaciones correspondientes)**

    * Esta clase es la que gestiona las validaciones pertinentes a los diferentes parámetros y variables creadas en cada una de las clases que componen la app. A continuación voy a explicar un poco las decisiones tomadas y el porque de las mismas.

        * Para la clase `Book` que representa los libros de la bilbioteca, se ha definido a través de varios campos que sirven a identificar un libro por nombre, autor, id y otros campos que permitan llevar el registro de los mismos en el sistema o BDD. Estos se validan los campos de nombre, autor y el género al que pertenece. Sus métodos validadores comprueban que el nombre de los mismos contienen vocales (reutilizando un poco lo visto en clase) y para los autores nos aseguramos que se especifiquen con un String compuesto de lo que sería 3 palabras, 1 para el nombre y otras dos para sus dos primeros apellidos. Para los tres campos se establece un número mínimo de caracteres y en el caso de géneros mínimo a 1 género tiene que pertenecer un libro.

        * La clase `Film`, muy similar al esquema de Book pero además con un campo actors que es una lista (casting de los actores que participaron en la misma). En su clase validadora se validan las películas de forma similar a como se validaban los campos de los libros.

     * Ambas lógicas anteriormente explicadas se han representado haciendo uso de Herencia de una clase Item_Library puesto que gran parte de sus campos son identicos y eran generalizables. Esto se hizo también de cara a definir una serie de atributos y funciones que tendráin en comun, como por ejemplo la disponibilidad (available) y las funciones que permitirían modificar ese estado. Además esto permite en un futuro que más items de la biblioteca sean alquilables y sea facil su implementación.

        * La clase `Loan` hace referencia al préstamo de un libro y/o una película como máximo. He de reconocer que mi intención inicial era permitir que se pudiesen alquilar más de un item de cada tipo pero a la hora de la implementación vi que era más complejo y que debería de modificar algunos endpoints y clases ya definidas y por tema tiempos y planificación no me daría tiempo, por lo tanto lo dejo como una posible futura mejora. Su lógica de creacion es compleja y surge de varias verificaciones previas, existencia del usuario y de los productos, pasando por su disponibilidad y ya finalmente indicar que productos se quieren alquilar.

        * La clase `User` referencia al usuario de nuestra Biblioteca, con campos que permiten identificar a cada uno de ellos inequivocamente. Algunos de sus campos mas relevantes para nuestra lógica de negocio son: contact_mail, hashed_password (su contraseña cifrada con bcrypt), user_id y su nombre full_name. Cada uno con sus validaciones específicas. Cabe destacar que para la implantación de algunos endpoints o funciones se tuvo que incluir un validador adicional para un "UserUpdate" para reflejar el tema de las actualizaciones de los perfiles de los usuarios" puesto que con las restricciones de validacion de User no permitía que se pasasen algunos parámetros opcionales y otros no.

        * La clase `Genre` es una clase básica que permite asociar el género que posee cada item de la biblioteca, solo dispone de nombre e id.
    


3. **main.py -> Operaciones CRUD y endpoints**
    
    Esta clase contiene toda la lógica de creación de la API además de donde se encuentran los diferentes métodos que permiten la interacción con el sistema a través de diferentes tipos de request. Entre sus funcionalidades se encuentran:

    * Crear, leer, actualizar y eliminar (`CRUD`) libros, autores, usuarios.
    * Registrar nuevos usuarios.
    * Realizar préstamos y devoluciones de libros.
    * Gestionar el stock de libros.
    * Cifrado de la contraseña de los usuarios.

    Sus diferentes endpoints y descripción de cada uno son los siguientes:

    * `POST /Usuarios/` -> Crea y registra un nuevo usuario.
    * `GET /Usuarios/{name}` -> Obtiene la información de uno o más usuarios por nombre.
    * `PATCH /Usuarios/{user_id}/Perfil_de_usuario` -> Modifica parcialmente los datos de un usuario existente.
    * `POST /Libros/` -> Crea y registra un nuevo libro, opcionalmente añadiendo un nuevo género a través de un parámetro pasado por url y capturandolo a través de una query.
    * `GET /Libros/{name}` -> Obtiene la información de un libro por su nombre.
    * `POST /Peliculas/` -> Crea y registra una nueva película, opcionalmente añadiendo un nuevo género a través de un parámetro pasado por url y capturandolo a través de una query.
    * `GET /Peliculas/{name}` -> Obtiene la información de una película por su nombre.
    * `GET /Peliculas/{name}/actors` -> Obtiene la lista de actores de una película específica.
    * `POST /Generos/` -> Crea y registra un nuevo género.
    * `GET /Generos/{name}` -> Obtiene la información de un género específico.
    * `POST /Realizar_un_prestamo/` -> Registra un nuevo préstamo de un libro y/o una película. Validando existencia del usuario, de los artículos y su disponibilidad a ser alquilados. 
    * `PATCH /Devolver_prestamo/` -> Gestiona la devolución de un préstamo específico.
    * `DELETE /Libros/{ref_number}/` -> Borra un libro por su número de referencia.
    * `DELETE /Peliculas/{ref_number}/` -> Borra una película por su número de referencia.


Adicionalmente a lo comentado anteriormente, para clarificar las relaciones entre clases y la lógica de mi app que originalmente pretendía. Diseñé un archivo sketch de drawio de un modelo entidad relación que se encuentra disponible en la carpeta other_resources además de la batería de pruebas ejecutada y probada en la demo.


4. **Contenerización de la aplicación. Separación de la API de la BDD**

El archivo Dockerfile representa la imagen que dispondrá de la parte correspondiente a la aplicación de nuestra biblioteca. Aqui se define que nuestra API escuchará por el puerto 8000


En el docker compose se define la red que usaremos para nuestra aplicación, denominada library-net. Se levantan dos contenedores, un contenedor para la api y otro para la BDD. El puerto de mi host a traves de donde puedo acceder a la Api es el 8080 y el del contenedor desde donde escucha es el 8000 como hemos definifo en el Dockerfile.

En el archivo docker-compose se define este despliegue, utilicé la documentación de docker oficial para estos casos de uso con docker-compose: [text](https://docs.docker.com/guides/databases/). Como mi tipo de conexión desde el módulo de Programación avanzada la diseñé con sqlite me daba problemas de conexion entre contenedores y la cambié a PostgreSQL.

Por otro lado, se define un "control de salud" o healthcheck, esto es debido a que cuando ejecutaba la instrucción `docker-compose up -d --build` había veces que uno de los dos contenedores no se levantaba. Me di cuenta cuando trataba de probar los métodos CRUD de mi api, porque el contenedor de la BDD no terminaba de arrancar a tiempo para conectarse al otro contenedor que contenía la API. Buscando por el error me encontré con este artículo: [text](https://medium.com/@saklani1408/configuring-healthcheck-in-docker-compose-3fa6439ee280) donde se explicaba como resolverlo.
