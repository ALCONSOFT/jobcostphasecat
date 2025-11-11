# 🔧 INSTRUCCIONES PARA ACTUALIZAR EL MÓDULO jobcostphasecat

## ⚠️ IMPORTANTE: Debes seguir TODOS estos pasos

### Paso 1: Acceder a Odoo
1. Abre tu navegador
2. Ve a: **http://localhost:8030**
3. Inicia sesión con tu usuario

---

### Paso 2: Activar Modo Desarrollador
1. Click en tu **nombre de usuario** (esquina superior derecha)
2. Click en **"Ajustes"** o **"Settings"**
3. Baja hasta el FINAL de la página
4. Busca: **"Activar el modo de desarrollador"**
5. Click en ese enlace
6. Espera que la página recargue

---

### Paso 3: Ir a Aplicaciones
1. Click en el menú **Aplicaciones** (Apps) - icono de 9 cuadrados
2. En el cuadro de búsqueda, **QUITA** el filtro "Aplicaciones"
   - Click en la X del filtro "Aplicaciones"
3. Busca: **jobcostphasecat**

---

### Paso 4: Actualizar el Módulo
1. Deberías ver el módulo **jobcostphasecat**
2. Click en el módulo
3. Click en el botón **"Actualizar"** o **"Upgrade"**
4. **ESPERA** que termine la actualización (puede tardar 30-60 segundos)
5. Verás un mensaje de éxito

---

### Paso 5: Limpiar Caché del Navegador
**Windows/Linux:**
- Presiona: **Ctrl + Shift + R**

**Mac:**
- Presiona: **Cmd + Shift + R**

**O bien:**
- Presiona **F5** varias veces

---

### Paso 6: Probar el Formulario Nuevo
1. Ve a **Compra** → **Órdenes** → **Órdenes de Compra**
2. Abre cualquier orden (ej: PA02663)
3. Click en la pestaña **"Productos"**
4. **HAZ DOBLE CLICK** en cualquier línea de producto
5. **¡Deberías ver el formulario nuevo completo!**

---

## ✅ Lo que DEBERÍAS ver en el nuevo formulario:

### Header:
- Barra de estado: Draft → Sent → Waiting → Purchase → Done
- Botón "Ver Historial Completo"

### Secciones:
- 📋 Información General
- 🎯 Proyecto y Distribución
- 📊 Cantidades y Unidades
- 💰 Precios y Descuentos
- 💵 Impuestos y Totales
- ⚙️ Opciones y Configuración (con **🔴 Ocultar en Reportes**)
- 📦 Movimientos de Stock

### Pestañas:
- 📚 Historial de Compras
- 📄 Facturación
- 🔍 Información Técnica
- 📊 Resumen Completo

---

## ❌ Si AÚN no funciona:

Ejecuta este comando en la terminal:

```bash
docker exec dc_odoo16_alconsoft-web030-1 bash -c "odoo -c /etc/odoo/odoo.conf -u jobcostphasecat -d dev16_TSI_251105 --stop-after-init"
```

Luego reinicia el contenedor:

```bash
docker-compose restart web030
```

Y vuelve a probar después de 30 segundos.

---

## 📞 Si nada funciona:
Avísame qué ves exactamente y te ayudo a diagnosticar el problema.
