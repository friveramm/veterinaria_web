# Mi Veterinaria - ERP & CRM Clínico

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Bootstrap](https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white)

Plataforma Full Stack desarrollada para la administración integral de centros veterinarios. El sistema digitaliza el agendamiento de citas, el historial clínico de pacientes y las analíticas de negocio, garantizando la integridad de los datos mediante transacciones atómicas en bases de datos relacionales.

---

## Características Técnicas Destacadas

* **Arquitectura de Roles (RBAC):** Vistas y permisos estrictamente separados para Clientes, Veterinarios y Jefatura.
* **Seguridad Transaccional:** Prevención de *Race Conditions* en la generación de Fichas Clínicas utilizando `transaction.atomic()` y secuencias nativas de PostgreSQL.
* **Búsqueda AJAX en Tiempo Real:** Motor de autocompletado y validación de usuarios implementado con JavaScript (*Debouncing*) y la Fetch API para optimizar las consultas al servidor.
* **Algoritmo de Validación:** Integración del algoritmo Módulo 11 en Frontend y Backend para validar la autenticidad de los RUT chilenos.
* **Cálculo Dinámico (Propiedades):** Eliminación de redundancia de datos calculando la edad de los pacientes en tiempo real (años y meses) mediante propiedades `@property` en el ORM.

---

## Demostración del Sistema

<details>
<summary><b>Ver Demo: Portal Público y Navegación Principal</b></summary>
<br>

Exhibición de la página de inicio, carrusel automatizado con consumo asíncrono de APIs externas (The Cat API / Dog CEO API) y navegación responsiva.

(INSERTAR: index-demo-01.gif)
</details>

<details>
<summary><b>Ver Demo: Registro de Clientes Nuevos</b></summary>
<br>

Formulario de registro con validación asíncrona mediante JavaScript (Debouncing) y Fetch API para comprobar disponibilidad de RUT, correo y nombre de usuario en tiempo real.

(INSERTAR: creacion-cliente-demo.gif)
</details>

<details>
<summary><b>Ver Demo: Registro de Mascotas</b></summary>
<br>

Módulo de autogestión donde el cliente puede dar de alta a sus mascotas. El sistema calcula la edad exacta dinámicamente en el backend mediante propiedades del ORM.

(INSERTAR: crear-mascota-demo.gif)
</details>

<details>
<summary><b>Ver Demo: Proceso de Agendamiento de Citas</b></summary>
<br>

Flujo completo para reservar una atención médica en línea, seleccionando sucursales, servicios y profesionales disponibles según bloques de tiempo regulados.

(INSERTAR: agendar-demo.gif)
</details>

<details>
<summary><b>Ver Demo: Intranet Médica (Vista Veterinario)</b></summary>
<br>

Panel privado del cuerpo médico. Incluye la agenda diaria, buscador predictivo de pacientes por RUT y acceso al historial clínico cronológico (Línea de tiempo).

(INSERTAR: vista-vet-demo.gif)
</details>

<details>
<summary><b>Ver Demo: Dashboard Analítico de Administración (Jefatura) y Catálogo en Vivo</b></summary>
<br>

Muestra el panel gerencial con métricas financieras operativas (`Sum`, `Count`, `Avg`) y el flujo dinámico de actualización de la plataforma:

#### Paso A: Gestión en Intranet Administrativa
Creación y alta de un nuevo servicio médico desde el panel privado de Jefatura.

(BORRA ESTE TEXTO Y INSERTAR: dashboard-admin-demo.gif)

#### Paso B: Reflejo Inmediato en Portal Público
Actualización en tiempo real del catálogo clínico en la página principal, demostrando la persistencia de datos y la renderización dinámica del ORM.

(BORRA ESTE TEXTO Y INSERTAR: index-demo-02.gif)
</details>

---

## Tecnologías Utilizadas

* **Backend:** Python 3, Django (Arquitectura MVT)
* **Base de Datos:** PostgreSQL
* **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript Vanilla (ES6+)
* **Integraciones:** The Cat API & Dog CEO API (Consumo asíncrono frontend)

---

## Instalación y Despliegue Local

Sigue estos pasos para ejecutar el proyecto en tu entorno local:

### 1. Clonar el repositorio

```bash
git clone https://github.com/friveramm/veterinaria_web.git
cd veterinaria_web
```

### 2. Crear y activar el entorno virtual

```bash
python3 -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar la base de datos

Asegúrate de tener PostgreSQL ejecutándose localmente. Crea una base de datos y actualiza las credenciales correspondientes en `settings.py`.

Luego aplica las migraciones:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Configurar secuencia nativa de PostgreSQL

Abre la consola de PostgreSQL y ejecuta la siguiente instrucción SQL para habilitar la numeración segura de fichas:

```sql
CREATE SEQUENCE IF NOT EXISTS gestion_ficha_n_ficha_seq START WITH 1;
```

### 6. Ejecutar el servidor

```bash
python manage.py runserver
```

Una vez iniciado el servidor, podrás acceder a la aplicación desde:

```text
http://127.0.0.1:8000/
```

---

## Créditos y Atribuciones

* Icono de pestaña (Favicon): <a href="https://www.flaticon.es/iconos-gratis/gato" target="_blank" title="gato iconos">Gato iconos creados por smalllikeart - Flaticon</a>