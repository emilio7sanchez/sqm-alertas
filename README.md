# Alerta de ofertas laborales SQM / SQM Litio

Cada 2 horas, GitHub revisa las ofertas de:
- https://www.trabajaensqm.com
- https://trabajaen.sqmlitio.com

Si aparece una oferta nueva, te llega un mail a Gmail con el cargo, la ciudad, el tipo de contrato, las fechas y el link para postular.
`seen.json` guarda las ofertas que ya se revisaron (31 al 16-11-2026), así que no recibirás avisos de las que ya estaban publicadas.

## Instalación (una sola vez, unos 10 minutos)

### 1. Crear una contraseña de aplicación de Gmail
1. Entra a https://myaccount.google.com/security y activa la **Verificación en 2 pasos** si todavía no la tienes.
2. Entra a https://myaccount.google.com/apppasswords
3. Escribe un nombre (por ejemplo `Alertas SQM`) y presiona **Crear**.
4. Copia la clave de 16 letras. Solo se muestra una vez.

### 2. Crear el repositorio en GitHub
1. Crea una cuenta gratis en https://github.com si no tienes una.
2. Ve a https://github.com/new, ponle de nombre `sqm-alertas`, márcalo como **Private** y presiona **Create repository**.
3. En la página siguiente, haz clic en **uploading an existing file**.
4. Arrastra **todo el contenido** de esta carpeta: `check_sqm.py`, `seen.json`, `README.md` y la carpeta `.github`.
   La carpeta `.github` es necesaria, porque ahí está la programación cada 2 horas.
5. Presiona **Commit changes**.

### 3. Guardar las claves como secretos
En el repositorio ve a **Settings → Secrets and variables → Actions → New repository secret** y crea estos tres:

| Nombre | Valor |
|---|---|
| `GMAIL_USER` | tu dirección de Gmail |
| `GMAIL_APP_PASSWORD` | la clave de 16 letras del paso 1 |
| `MAIL_TO` | el correo donde quieres recibir los avisos (puede ser el mismo) |

### 4. Probar
Ve a la pestaña **Actions → Alerta ofertas SQM → Run workflow**. Si termina en verde, ya está funcionando.
No llegará ningún mail hasta que SQM publique una oferta nueva.

## Notas
- Si GitHub no ve actividad en el repositorio durante 60 días, pausa la alerta y te avisa por mail. Para reactivarla, ve a **Actions → Enable workflow**. Cada oferta nueva registra actividad, así que esto solo debería pasar si SQM deja de publicar por mucho tiempo.
- Para cambiar la frecuencia, edita la línea `cron` en `.github/workflows/check.yml` (por ejemplo, `0 * * * *` revisa cada hora).
- Si un sitio no responde, GitHub marca esa ejecución en rojo y te avisa por mail. Las ofertas no se pierden: se revisan de nuevo en la siguiente ejecución.
