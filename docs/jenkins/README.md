# Jenkins: construcción e instalación en DEV local

El proyecto TicketGo no genera un ejecutable de escritorio: se construye y se instala como una aplicación de microservicios. El pipeline usa los `Dockerfile` del repositorio para construir las imágenes y `docker-compose.yml` para levantar la aplicación en localhost.

## Requisitos en la máquina del agente

- Jenkins LTS y una versión de Java compatible con esa versión de Jenkins.
- Plugins de Jenkins **Git**, **Pipeline** y **JUnit**.
- Un agente Jenkins en Windows o Linux.
- Python 3.10 o superior con soporte para `venv`, disponible como `python` (Windows) o `python3` (Linux) en el `PATH`.
- Docker Desktop iniciado, con Docker Compose v2 disponible como `docker compose`.
- La cuenta de Windows que ejecuta Jenkins debe poder acceder al motor de Docker.

La cuenta que ejecuta el agente Jenkins debe tener acceso al motor de Docker; en Windows con Docker Desktop, una cuenta de servicio sin acceso al motor no podrá construir ni iniciar contenedores.

## Instalar Jenkins y crear el job

1. Instala Jenkins LTS usando el instalador oficial para Windows y completa el asistente inicial desde `http://localhost:8080`.
2. En **Manage Jenkins > Plugins**, confirma que estén instalados **Git**, **Pipeline** y **JUnit**.
3. En Jenkins, selecciona **New Item**, asigna un nombre y elige **Pipeline**.
4. En **Pipeline**, selecciona **Pipeline script from SCM**, elige Git, pega la URL del repositorio y configura las credenciales si el repositorio las requiere.
5. Selecciona la rama que contiene el `Jenkinsfile` y deja `Jenkinsfile` como **Script Path**.
6. Guarda el job y selecciona **Build Now**.

Antes de ejecutar el job, sube al repositorio el `Jenkinsfile` y las pruebas. Configura el servicio Jenkins para que use una cuenta de Windows con acceso al motor de Docker.

## Etapas y resultado esperado

1. **Preparar dependencias** instala pytest y las dependencias de las pruebas.
2. **Ejecutar pruebas unitarias** ejecuta `python -m pytest` y publica el resultado en **Test Result** de Jenkins (actualmente son 15 pruebas).
3. **Construir imágenes** ejecuta `docker compose build`.
4. **Instalar en DEV - localhost** inicia el stack con `docker compose up -d --wait` y muestra el estado con `docker compose ps`.

El pipeline se detiene si fallan las pruebas o la construcción. Al terminar correctamente, se pueden revisar el reporte de pruebas, la consola del build y los servicios en `http://localhost:3000` (frontend) y `http://localhost:8000` a `http://localhost:8003` (APIs). Para detener el ambiente local, ejecutar `docker compose down` desde el workspace del job.

## Evidencias para la entrega

Guarda capturas reales de la máquina que ejecuta Jenkins:

- Jenkins instalado y accesible en el navegador.
- Configuración del job mostrando el pipeline asociado al repositorio.
- Build terminado con estado **Success** y las cuatro etapas completadas.
- **Test Result** mostrando el conteo y el resultado de las 15 pruebas.
- Consola con la construcción de imágenes y la instalación en DEV.
- `docker compose ps` con los servicios activos y la aplicación abierta en localhost.

Las capturas deben obtenerse después de ejecutar el job; no se incluyen imágenes simuladas en el repositorio.
