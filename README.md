# 🤖 WhatsApp Chatbot con Google Sheets - Gestión de Clientes y Pedidos

Chatbot automático para WhatsApp que:
- ✅ Responde mensajes con respuestas predefinidas
- ✅ **Registra automáticamente clientes** que escriben
- ✅ **Gestiona pedidos** - historial completo
- ✅ **Evita duplicados** - no repite pedidos
- ✅ **Responde a todos** - clientes nuevos o existentes
- ✅ Sesión persistente, sin reinicio constante
- ✅ Totalmente gratis

---

## 📊 Estructura de Google Sheets

El bot utiliza **3 hojas diferentes**:

### 1. **Respuestas** (Sheet1)
Palabras clave y respuestas del bot

| Pregunta | Respuesta |
|----------|----------|
| hola | ¡Hola! Bienvenido ¿En qué te puedo ayudar? |
| precio | Los precios están disponibles en el catálogo |
| horario | Atendemos de 9 AM a 6 PM |
| pedido | ¿Qué producto deseas? |

### 2. **Clientes** (Auto-creada)
Registro automático de clientes

| Teléfono | Nombre | Primer Contacto | Último Contacto |
|----------|--------|-----------------|------------------|
| 5491112345 | Cliente 1 | 2026-06-16 10:00:00 | 2026-06-16 10:05:00 |
| 5491112346 | Cliente 2 | 2026-06-16 10:10:00 | 2026-06-16 10:15:00 |

### 3. **Pedidos** (Auto-creada)
Historial completo de pedidos

| Teléfono | Producto | Cantidad | Precio | Fecha | Estado | Notas |
|----------|----------|----------|--------|-------|--------|-------|
| 5491112345 | iPhone 15 | 1 | $999 | 2026-06-16 10:05:00 | Pendiente | |
| 5491112345 | AirPods | 2 | $299 | 2026-06-16 10:06:00 | Completado | Entregado |

---

## 🚀 Instalación Rápida

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/Jacobtinoco19/whatsapp-chatbot-sheets.git
cd whatsapp-chatbot-sheets
```

### Paso 2: Ejecutar setup (Windows/Mac/Linux)

**Windows:**
```bash
setup.bat
```

**Mac/Linux:**
```bash
bash setup.sh
```

### Paso 3: Editar configuración

```bash
# Abre .env y agrega tu Google Sheet ID
notepad .env  # Windows
nano .env     # Mac/Linux
```

### Paso 4: Autenticar con Google

```bash
python auth_google.py
```
- Se abrirá un navegador
- Autoriza tu cuenta de Google
- Se creará `token.json`

### Paso 5: Crear Google Sheet

1. Ve a https://sheets.google.com
2. Crea una nueva hoja de cálculo
3. Copia el ID de la URL: `https://docs.google.com/spreadsheets/d/AQUI_VA_EL_ID/edit`
4. Pégalo en `.env` en la variable `GOOGLE_SHEET_ID`

### Paso 6: Agregar respuestas

1. Abre tu Google Sheet
2. En la primera hoja (Respuestas), agrega:
   - **Columna A:** Palabras clave (hola, precio, horario, etc.)
   - **Columna B:** Respuestas del bot

**Ejemplo:**
```
hola → ¡Hola! Bienvenido
precio → ¿Qué producto buscas?
pedido → Claro, ¿qué necesitas?
```

### Paso 7: Ejecutar el bot

```bash
python bot.py
```

**Primera ejecución:**
- Se abrirá un navegador
- Escanea el código QR con WhatsApp
- ¡Listo! Bot activo

---

## 💡 Cómo Funciona

### Flujo de mensajes:

```
Cliente escribe mensaje
         ↓
Bot registra teléfono en "Clientes"
         ↓
Bot busca respuesta en "Respuestas"
         ↓
Bot envía respuesta automática
         ↓
(Opcional) Registra pedido en "Pedidos"
         ↓
Cliente recibe respuesta
```

### Características principales:

1. **Auto-registro de clientes**
   - Cualquier número que escriba es registrado automáticamente
   - Guarda teléfono, nombre, fecha de primer contacto

2. **Respuestas automáticas**
   - Busca palabras clave en el mensaje
   - Responde con coincidencia exacta o similar
   - Se actualiza cada 30 segundos desde Google Sheets

3. **Gestión de pedidos**
   - Registra automáticamente cada pedido
   - Evita duplicados (mismo pedido en 5 minutos)
   - Marca como "Pendiente" o "Completado"

4. **Historial completo**
   - Todo guardado en Google Sheets
   - Acceso desde cualquier dispositivo
   - Compartible con tu equipo

---

## ⚙️ Configuración Avanzada

### Archivo `.env`

```
# Google Sheets
GOOGLE_SHEET_ID=tu_id_aqui
GOOGLE_SHEET_RANGE=Sheet1!A:B

# Comportamiento
LOG_LEVEL=INFO
RECONNECT_INTERVAL=30          # Segundos para reconectar
REFRESH_INTERVAL=30            # Segundos para actualizar datos
SIMILARITY_THRESHOLD=0.7       # 0-1, similitud para responder

# Rutas
SESSION_PATH=./sessions/
LOGS_PATH=./logs/

# Opciones avanzadas
DEBUG_MODE=False
MAX_RETRIES=5
TIMEOUT_SECONDS=60
```

---

## 📱 Ejemplos de Uso

### Ejemplo 1: Tienda de ropa

**Google Sheets - Respuestas:**
```
pregunta          → respuesta
hola              → ¡Hola! Bienvenido a nuestra tienda
qu   É productos  → Tenemos camisetas, pantalones, zapatos
precio camiseta   → Las camisetas cuestan $25
haremos pedido    → Perfecto, registramos tu pedido. ¿Qué talla?
```

**Google Sheets - Pedidos** (auto-generado):
```
5491112345 → Camiseta → 1 → $25 → 2026-06-16 10:00 → Pendiente
5491112345 → Pantalon → 1 → $40 → 2026-06-16 10:05 → Completado
```

### Ejemplo 2: Servicio técnico

**Respuestas:**
```
soporte          → ¿Cuál es tu problema técnico?
error            → Por favor describe el error que ves
reiniciar        → Intenta reiniciar tu dispositivo
necesito técnico → Un técnico te contactará pronto
```

---

## 🔍 Monitoreo

### Ver logs:

```bash
# Windows
type logs\bot.log

# Mac/Linux
cat logs/bot.log
```

### Ver datos en tiempo real:

1. Abre tu Google Sheet
2. Verifica las hojas:
   - **Respuestas:** Tus preguntas/respuestas
   - **Clientes:** Clientes que escribieron
   - **Pedidos:** Historial de pedidos

---

## 🛠️ Solución de Problemas

### "No se conecta a WhatsApp"
- Verifica Node.js: `node --version`
- Elimina carpeta `sessions/` y escanea QR nuevamente

### "No encuentra Google Sheet"
- Verifica `GOOGLE_SHEET_ID` en `.env`
- Asegúrate de compartir la hoja contigo mismo

### "No registra clientes"
- Verifica hoja "Clientes" existe en Google Sheets
- Comprueba permisos de la hoja

### "Error de autenticación"
- Elimina `token.json`
- Ejecuta: `python auth_google.py`

---

## 🔐 Seguridad

⚠️ **Importante:**
- Nunca compartas `token.json`
- Nunca commits `token.json` a GitHub (está en `.gitignore`)
- Nunca compartas `.env` con credenciales
- Usa permisos limitados en Google Sheets

---

## 📊 Estadísticas (Próximamente)

- Total de clientes
- Pedidos por mes
- Respuestas más usadas
- Tasa de conversion
- Reportes automáticos

---

## 🚀 Próximas Características

- [ ] Dashboard web de estadísticas
- [ ] Envío de imágenes desde Google Drive
- [ ] Respuestas automáticas por horario
- [ ] Integración con PayPal/Stripe
- [ ] Multi-idioma
- [ ] Respuestas por IA (ChatGPT)
- [ ] Notificaciones por email
- [ ] API REST para integraciones

---

## 📞 Contacto & Soporte

¿Preguntas? Abre un issue en GitHub

---

## 💡 Tips Pro

1. **Usa palabras clave cortas** - Facilita el reconocimiento
2. **Actualiza respuestas regularmente** - El bot se auto-actualiza
3. **Revisa pedidos frecuentemente** - Google Sheets se actualiza en tiempo real
4. **Haz backups** - Descarga tu Google Sheet regularmente
5. **Prueba con amigos** - Antes de usar con muchos clientes

---

**Creado con ❤️ para automatizar tu negocio**
