# ChromaticBot - Guía de Despliegue en Northflank

Esta guía te ayudará a desplegar ChromaticBot (Backend y Frontend) en Northflank.

## Requisitos Previos

1. Cuenta en [Northflank](https://northflank.com/)
2. Cuenta de Spotify Developer con una aplicación creada en [Spotify Dashboard](https://developer.spotify.com/dashboard)
3. Repositorios de GitHub para Backend y Frontend
4. (Opcional) Cuenta de MongoDB Atlas para la base de datos

## Parte 1: Desplegar el Backend (FastAPI)

### 1.1 Crear el Servicio en Northflank

1. Inicia sesión en Northflank
2. Crea un nuevo proyecto o selecciona uno existente
3. Click en **"Create Service"** → **"Build service"**
4. Selecciona tu repositorio de GitHub del backend
5. Configuración:
   - **Name**: `chromatic-bot-backend` (o el nombre que prefieras)
   - **Dockerfile path**: `Dockerfile`
   - **Port**: `8080`

### 1.2 Configurar Variables de Entorno

En la sección **Environment Variables**, agrega las siguientes variables:

#### Variables Requeridas:

```bash
# CORS - URL del frontend (actualizarás esto después de desplegar el frontend)
# Admite varios orígenes separados por comas
CLIENT_ORIGIN=https://your-frontend-url.northflank.app

# Base de datos MongoDB (opcional - solo si usas caché)
DB_URL=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=chromatic_db
DB_COLLECTION=albums
```

#### Variables Opcionales:

```bash
# Logging (debug, info, warning, error)
LOG_LEVEL=info
```

### 1.3 Configurar el Build

- **Build Command**: (automático, usa el Dockerfile)
- **Start Command**: (automático, usa el CMD del Dockerfile: uvicorn con 2 workers en el puerto 8080)

### 1.4 Desplegar

1. Click en **"Deploy"**
2. Espera a que el build termine
3. Una vez desplegado, copia la URL pública (algo como: `https://chromatic-bot-backend-xxxxx.northflank.app`)

### 1.5 Verificar el Despliegue

Visita `https://tu-backend-url.northflank.app/docs` para ver la documentación interactiva de FastAPI.

---

## Parte 2: Desplegar el Frontend (Angular)

### 2.1 Crear el Servicio en Northflank

La URL del backend ya **no** se configura en el código: el contenedor la lee
en runtime de la variable de entorno `API_BASE_URL` y genera
`assets/config.json` al arrancar. La misma imagen sirve para cualquier entorno.

1. En Northflank, click en **"Create Service"** → **"Build service"**
2. Selecciona tu repositorio de GitHub del frontend
3. Configuración:
   - **Name**: `chromatic-bot-frontend`
   - **Dockerfile path**: `Dockerfile`
   - **Port**: `80`

### 2.2 Configurar Variables de Entorno

```bash
# URL pública del backend (la que copiaste en el paso 1.4)
API_BASE_URL=https://tu-backend-url.northflank.app
```

### 2.3 Configurar el Build

- **Build Command**: (automático, usa el Dockerfile)
- **Start Command**: (automático, el entrypoint de nginx genera la config y arranca)

### 2.4 Desplegar

1. Click en **"Deploy"**
2. Espera a que el build termine
3. Una vez desplegado, copia la URL pública

---

## Parte 3: Configurar Spotify OAuth

### 3.1 Actualizar Spotify Redirect URI

1. Ve al [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Selecciona tu aplicación
3. Click en **"Settings"**
4. En **"Redirect URIs"**, agrega:
   ```
   https://tu-frontend-url.northflank.app/callback
   ```
5. Guarda los cambios

### 3.2 Actualizar CORS en el Backend

Vuelve a Northflank, al servicio del backend:

1. Ve a **Environment Variables**
2. Actualiza `CLIENT_ORIGIN` con la URL real del frontend:
   ```
   CLIENT_ORIGIN=https://tu-frontend-url.northflank.app
   ```
3. **Restart** el servicio para aplicar los cambios

---

## Parte 4: Verificación Final

### 4.1 Verificar el Backend

1. Visita `https://tu-backend-url.northflank.app/health`
2. Deberías ver un status `200 OK`

### 4.2 Verificar el Frontend

1. Visita `https://tu-frontend-url.northflank.app`
2. Deberías ver la página de inicio de ChromaticBot
3. Click en **"Login to Spotify"**
4. Autoriza la aplicación
5. Deberías ser redirigido de vuelta y ver tu nombre

### 4.3 Probar la Funcionalidad

1. Selecciona un período de tiempo (1 mes, 6 meses, todo el tiempo)
2. Ajusta la cantidad de canciones
3. Selecciona un modo de ordenamiento (hue, saturation, brightness)
4. Click en **"Start"**
5. Deberías ver tus álbumes ordenados cromáticamente
6. Click en **"Generate Poster"** para crear una imagen compartible

---

## Parte 5: Configuración de MongoDB (Opcional)

Si quieres usar caché de MongoDB:

### 5.1 Crear Cluster en MongoDB Atlas

1. Ve a [MongoDB Atlas](https://cloud.mongodb.com/)
2. Crea un cluster gratuito (M0)
3. Crea un usuario de base de datos
4. Whitelist todas las IPs (`0.0.0.0/0`) para Northflank
5. Obtén la connection string

### 5.2 Configurar en Northflank

En el backend, agrega las variables de entorno:

```bash
DB_URL=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=chromatic_db
DB_COLLECTION=albums
```

---

## Troubleshooting

### Error: CORS

**Síntoma**: Error de CORS en el frontend al hacer requests al backend

**Solución**:
- Verifica que `CLIENT_ORIGIN` en el backend tenga la URL correcta del frontend
- Asegúrate de haber reiniciado el servicio del backend después de cambiar las variables

### Error: Spotify OAuth Redirect

**Síntoma**: Error al hacer login con Spotify

**Solución**:
- Verifica que la Redirect URI en Spotify Dashboard sea exactamente: `https://tu-frontend-url.northflank.app/callback`
- No olvides el `/callback` al final
- No uses `http://`, solo `https://`

### Error: Cannot find module

**Síntoma**: Build falla con errores de módulos no encontrados

**Solución Backend**:
- Verifica que `pyproject.toml` y `pdm.lock` estén en el repositorio
- Asegúrate de que el Dockerfile use `pdm install --check --prod --no-editable`

**Solución Frontend**:
- Verifica que `package.json` y `package-lock.json` estén en el repositorio
- Asegúrate de que el Dockerfile use `npm ci` (no `npm install`)

### Error: Port already in use

**Síntoma**: El servicio no inicia porque el puerto está en uso

**Solución**:
- Backend: Verifica que el puerto en Northflank sea `8080`
- Frontend: Verifica que el puerto en Northflank sea `80`

---

## Monitoreo y Logs

### Ver Logs en Tiempo Real

1. Ve a tu servicio en Northflank
2. Click en la pestaña **"Logs"**
3. Puedes filtrar por nivel (info, error, warning)

### Métricas

1. Click en la pestaña **"Metrics"**
2. Puedes ver CPU, memoria, requests, etc.

---

## Costos

Northflank ofrece un tier gratuito que es suficiente para este proyecto:

- **Backend**: ~512MB RAM, 0.2 vCPU
- **Frontend**: ~256MB RAM, 0.1 vCPU
- **Bandwidth**: 100GB/mes

Si excedes estos límites, considera:
- Optimizar las requests (usar caché de MongoDB)
- Configurar auto-scaling
- Actualizar al tier de pago

---

## Actualizaciones

### Deploy Automático

Northflank puede configurarse para hacer deploy automático cuando haces push a `main`:

1. Ve a tu servicio
2. Click en **"CI/CD"**
3. Habilita **"Auto-deploy on push"**
4. Selecciona la rama (`main` o `master`)

### Deploy Manual

1. Ve a tu servicio
2. Click en **"Deploy"**
3. Selecciona el commit o branch
4. Click en **"Deploy"**

---

## Recursos Adicionales

- [Documentación de Northflank](https://northflank.com/docs)
- [Spotify Web API](https://developer.spotify.com/documentation/web-api)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Angular Deployment](https://angular.io/guide/deployment)

---

## Checklist Final

Antes de considerar el despliegue completo:

- [ ] Backend desplegado y funcionando
- [ ] Frontend desplegado y funcionando
- [ ] `CLIENT_ORIGIN` configurado correctamente en el backend
- [ ] `API_BASE_URL` configurado correctamente en el frontend
- [ ] Spotify Redirect URI actualizado
- [ ] Login con Spotify funciona
- [ ] Requests al backend funcionan (sin errores de CORS)
- [ ] Visualización de álbumes funciona
- [ ] Generación de poster funciona
- [ ] Ordenamiento por hue/saturation/brightness funciona
- [ ] Cambio de idioma funciona
- [ ] (Opcional) MongoDB configurado y funcionando

---

¡Listo! Tu aplicación ChromaticBot debería estar completamente funcional en Northflank. 🎨🎵
