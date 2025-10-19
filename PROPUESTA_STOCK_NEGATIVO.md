# 📋 PROPUESTA: Control de Stock Negativo por Almacén y Usuario

**Módulo**: `jobcostphasecat`
**Fecha**: 2025-10-10
**Versión**: 1.0

---

## 🎯 OBJETIVO

Implementar un sistema de control de stock negativo configurable que permita:
1. **Por Almacén**: Definir qué almacenes PUEDEN tener stock negativo
2. **Por Usuario**: Definir qué usuarios PUEDEN hacer salidas aunque no haya existencias
3. **Validación**: Bloquear salidas si no se cumplen las condiciones configuradas

---

## 🏗️ ARQUITECTURA PROPUESTA

### 1. Modelo de Configuración

#### Opción A: Configuración en `res.config.settings` (RECOMENDADA)

**Archivo**: `models/models_resconfigsettings.py`

```python
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Habilitar/Deshabilitar el control
    enable_negative_stock_control = fields.Boolean(
        string='Controlar Stock Negativo en Salidas',
        config_parameter='jobcostphasecat.enable_negative_stock_control',
        default=False,
        help='Si está habilitado, controla que solo almacenes y usuarios autorizados puedan hacer salidas con stock insuficiente'
    )

    # Almacenes permitidos para stock negativo
    allowed_negative_stock_warehouse_ids = fields.Many2many(
        'stock.warehouse',
        'config_warehouse_negative_stock_rel',
        'config_id', 'warehouse_id',
        string='Almacenes con Stock Negativo Permitido',
        help='Almacenes que PUEDEN tener stock negativo. Las salidas en estos almacenes NO serán bloqueadas por falta de stock.'
    )

    # Usuarios autorizados para hacer salidas sin stock
    allowed_negative_stock_user_ids = fields.Many2many(
        'res.users',
        'config_user_negative_stock_rel',
        'config_id', 'user_id',
        string='Usuarios Autorizados para Salidas sin Stock',
        help='Usuarios que PUEDEN hacer salidas aunque no haya existencias. Estos usuarios NO recibirán error de validación.'
    )
```

#### Opción B: Modelo Independiente (ALTERNATIVA)

**Archivo**: `models/stock_negative_config.py`

```python
class StockNegativeConfig(models.Model):
    _name = 'stock.negative.config'
    _description = 'Configuración de Stock Negativo'

    name = fields.Char(string='Nombre', required=True, default='Configuración Stock Negativo')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)

    warehouse_ids = fields.Many2many('stock.warehouse', string='Almacenes Permitidos')
    user_ids = fields.Many2many('res.users', string='Usuarios Autorizados')
```

---

## 🖼️ INTERFAZ DE USUARIO PROPUESTA

### Ubicación: Inventario → Configuración → Ajustes

**Mock-up de la Vista XML**:

```xml
<!-- views/res_config_settings_views.xml -->
<xpath expr="//div[@data-key='stock']" position="inside">
  <h2>Control de Stock Negativo</h2>

  <!-- Toggle principal -->
  <div class="col-12 col-lg-6 o_setting_box" id="negative_stock_control">
    <div class="o_setting_left_pane">
      <field name="enable_negative_stock_control"/>
    </div>
    <div class="o_setting_right_pane">
      <label for="enable_negative_stock_control"/>
      <div class="text-muted">
        Controla las salidas de inventario cuando no hay existencias disponibles
      </div>
    </div>
  </div>

  <!-- Almacenes permitidos (visible solo si está habilitado) -->
  <div class="col-12 o_setting_box"
       attrs="{'invisible': [('enable_negative_stock_control', '=', False)]}">
    <div class="o_setting_right_pane">
      <label for="allowed_negative_stock_warehouse_ids" string="Almacenes con Stock Negativo Permitido"/>
      <div class="text-muted mb-3">
        Selecciona los almacenes que PUEDEN tener stock negativo.
        Las salidas en estos almacenes NO serán bloqueadas por falta de existencias.
      </div>
      <field name="allowed_negative_stock_warehouse_ids"
             widget="many2many_tags"
             placeholder="Seleccionar almacenes..."
             options="{'color_field': 'color', 'no_create': True}"/>
    </div>
  </div>

  <!-- Usuarios autorizados (visible solo si está habilitado) -->
  <div class="col-12 o_setting_box"
       attrs="{'invisible': [('enable_negative_stock_control', '=', False)]}">
    <div class="o_setting_right_pane">
      <label for="allowed_negative_stock_user_ids" string="Usuarios Autorizados para Salidas sin Stock"/>
      <div class="text-muted mb-3">
        Selecciona los usuarios que PUEDEN hacer salidas aunque no haya existencias.
        Estos usuarios NO recibirán error de validación por stock insuficiente.
      </div>
      <field name="allowed_negative_stock_user_ids"
             widget="many2many_tags"
             placeholder="Seleccionar usuarios..."
             options="{'no_create': True}"/>
    </div>
  </div>
</xpath>
```

---

## 📊 VISTA PREVIA (Mockup)

```
┌─────────────────────────────────────────────────────────────────┐
│  INVENTARIO → CONFIGURACIÓN → AJUSTES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ╔═══════════════════════════════════════════════════════════╗ │
│  ║  Control de Stock Negativo                                ║ │
│  ╚═══════════════════════════════════════════════════════════╝ │
│                                                                 │
│  ┌─┐                                                           │
│  │✓│ Controlar Stock Negativo en Salidas                      │
│  └─┘                                                           │
│     Controla las salidas de inventario cuando no hay          │
│     existencias disponibles                                    │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐│
│  │ Almacenes con Stock Negativo Permitido                    ││
│  │                                                            ││
│  │ [Almacén Central] [Almacén Panamá] [Almacén Chorrera] [+] ││
│  │                                                            ││
│  │ Las salidas en estos almacenes NO serán bloqueadas        ││
│  └───────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐│
│  │ Usuarios Autorizados para Salidas sin Stock               ││
│  │                                                            ││
│  │ [Admin] [Usuario Almacén] [Gerente Operaciones] [+]       ││
│  │                                                            ││
│  │ Estos usuarios NO recibirán error de stock insuficiente   ││
│  └───────────────────────────────────────────────────────────┘│
│                                                                 │
│                                    [Guardar]  [Descartar]      │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ LÓGICA DE VALIDACIÓN

### Pseudocódigo de la Validación

```python
def button_validate(self):
    """Override del método button_validate en stock.picking"""

    # 1. Verificar si el control está habilitado
    control_enabled = self.env['ir.config_parameter'].sudo().get_param(
        'jobcostphasecat.enable_negative_stock_control',
        'False'
    ).lower() == 'true'

    if not control_enabled:
        return super().button_validate()  # ← Comportamiento normal de Odoo

    # 2. Solo validar en transferencias de SALIDA
    if self.picking_type_id.code != 'outgoing':
        return super().button_validate()  # ← Ignorar recepciones/transferencias internas

    # 3. Obtener almacenes y usuarios permitidos
    allowed_warehouses = self.env['stock.warehouse'].search([
        ('id', 'in', self._get_allowed_warehouses())
    ])
    allowed_users = self.env['res.users'].search([
        ('id', 'in', self._get_allowed_users())
    ])

    # 4. Verificar EXCEPCIONES (NO validar si se cumple alguna)
    warehouse = self.picking_type_id.warehouse_id
    current_user = self.env.user

    # EXCEPCIÓN 1: El almacén está en la lista de permitidos
    if warehouse in allowed_warehouses:
        return super().button_validate()  # ← Permitir stock negativo

    # EXCEPCIÓN 2: El usuario está en la lista de autorizados
    if current_user in allowed_users:
        return super().button_validate()  # ← Permitir sin validación

    # 5. VALIDAR STOCK - Solo si NO se cumplió ninguna excepción
    for move in self.move_ids:
        if move.state in ('done', 'cancel'):
            continue

        # Obtener stock disponible REAL (puede ser negativo)
        available_qty = self.env['stock.quant']._get_available_quantity(
            move.product_id,
            move.location_id,
            lot_id=move.lot_ids[:1] if move.lot_ids else None,
            package_id=move.package_id,
            owner_id=move.owner_id,
            strict=False,
            allow_negative=True  # ← Ver valor REAL
        )

        # Si intenta sacar más de lo disponible → ERROR
        if move.quantity_done > available_qty:
            raise ValidationError(_(
                '❌ Stock Insuficiente\n\n'
                'Producto: %(product)s\n'
                'Ubicación: %(location)s\n'
                'Disponible: %(available).2f %(uom)s\n'
                'Solicitado: %(requested).2f %(uom)s\n'
                'Faltante: %(missing).2f %(uom)s\n\n'
                '💡 Nota: Solo almacenes y usuarios autorizados pueden hacer salidas con stock insuficiente.\n'
                'Contacta al administrador si necesitas autorización.'
            ) % {
                'product': move.product_id.display_name,
                'location': move.location_id.complete_name,
                'available': available_qty,
                'requested': move.quantity_done,
                'missing': move.quantity_done - available_qty,
                'uom': move.product_uom.name,
            })

    # 6. Si todo está OK, continuar con validación normal
    return super().button_validate()
```

---

## 🔄 DIAGRAMA DE FLUJO

```
                    ┌─────────────────────┐
                    │ Usuario hace clic   │
                    │ en "Validar" (🟢)   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ ¿Control habilitado?│
                    └──────────┬──────────┘
                               │
                    ┌──────────┴───────────┐
                    │                      │
                   SÍ                     NO
                    │                      │
                    ▼                      ▼
         ┌──────────────────┐    ┌────────────────┐
         │ ¿Es transferencia│    │ Validar normal │
         │ de SALIDA?       │    │ (Odoo default) │
         └─────────┬────────┘    └────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
       SÍ                    NO
        │                     │
        ▼                     ▼
┌────────────────┐   ┌────────────────┐
│ Verificar      │   │ Validar normal │
│ EXCEPCIONES    │   │ (Odoo default) │
└───────┬────────┘   └────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│ ¿Almacén en lista de permitidos?    │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴───────────┐
    │                      │
   SÍ                     NO
    │                      │
    ▼                      ▼
┌────────────┐   ┌──────────────────────┐
│ PERMITIR   │   │ ¿Usuario autorizado? │
│ (sin error)│   └──────────┬───────────┘
└────────────┘              │
                 ┌──────────┴───────────┐
                 │                      │
                SÍ                     NO
                 │                      │
                 ▼                      ▼
         ┌────────────┐      ┌──────────────────┐
         │ PERMITIR   │      │ VALIDAR STOCK    │
         │ (sin error)│      │ move por move    │
         └────────────┘      └─────────┬────────┘
                                       │
                             ┌─────────┴─────────┐
                             │                   │
                      qty_done <= disponible   qty_done > disponible
                             │                   │
                             ▼                   ▼
                      ┌────────────┐      ┌──────────────┐
                      │ VALIDAR ✅ │      │ ERROR ❌     │
                      └────────────┘      │ "Stock       │
                                          │ Insuficiente"│
                                          └──────────────┘
```

---

## 📝 EJEMPLOS DE USO

### Ejemplo 1: Usuario Normal en Almacén Normal
```
Usuario: Juan Pérez (NO autorizado)
Almacén: Almacén Central (NO permitido para negativo)
Producto: Tornillo M8
Stock disponible: 0 unidades
Intenta sacar: 5 unidades

RESULTADO: ❌ ERROR
"Stock Insuficiente
Producto: Tornillo M8
Disponible: 0.00 Unidades
Solicitado: 5.00 Unidades
Faltante: 5.00 Unidades"
```

### Ejemplo 2: Almacén Configurado como Permitido
```
Usuario: Juan Pérez (NO autorizado)
Almacén: Almacén Panamá (SÍ permitido para negativo) ← En configuración
Producto: Tornillo M8
Stock disponible: 0 unidades
Intenta sacar: 5 unidades

RESULTADO: ✅ PERMITIDO (sin error)
Stock final: -5 unidades
```

### Ejemplo 3: Usuario Autorizado
```
Usuario: Admin (SÍ autorizado) ← En configuración
Almacén: Almacén Central (NO permitido para negativo)
Producto: Tornillo M8
Stock disponible: 0 unidades
Intenta sacar: 5 unidades

RESULTADO: ✅ PERMITIDO (sin error)
Stock final: -5 unidades
```

### Ejemplo 4: Control Deshabilitado
```
Control: DESHABILITADO (checkbox sin marcar)
Usuario: Cualquiera
Almacén: Cualquiera
Producto: Tornillo M8
Stock disponible: 0 unidades
Intenta sacar: 5 unidades

RESULTADO: ✅ PERMITIDO (comportamiento Odoo estándar)
Stock final: -5 unidades
```

---

## 🔐 SEGURIDAD Y PERMISOS

### Acceso a Configuración
- Solo usuarios con permisos de **"Administrador de Inventario"** pueden:
  - Habilitar/deshabilitar el control
  - Modificar lista de almacenes permitidos
  - Modificar lista de usuarios autorizados

### Auditoría
- Cada validación bloqueada se registra en log del sistema
- Mensaje incluye: usuario, almacén, producto, cantidades

---

## 📁 ARCHIVOS A CREAR/MODIFICAR

### Nuevos Archivos
Ninguno (se usa infraestructura existente)

### Archivos a Modificar

1. **`models/models_resconfigsettings.py`**
   - Agregar 3 campos nuevos (enable, warehouses, users)

2. **`views/res_config_settings_views.xml`**
   - Agregar sección "Control de Stock Negativo"
   - 3 campos con visibilidad condicional

3. **`models/models_stock_picking.py`**
   - Override del método `button_validate()`
   - Lógica de validación según configuración

4. **`__manifest__.py`**
   - Actualizar versión
   - Documentar cambio

---

## ⚡ RENDIMIENTO

### Impacto en Performance
- **Mínimo**: Solo se ejecuta en transferencias de SALIDA
- **2-3 queries adicionales**:
  1. Lectura de parámetro de configuración
  2. Búsqueda de almacenes permitidos (en memoria)
  3. Búsqueda de usuarios autorizados (en memoria)
- **Por cada move**: 1 query de stock disponible

### Optimizaciones Incluidas
- Cache de configuración en memoria
- Early return si control deshabilitado
- Solo validar moves no done/cancel

---

## 🧪 PLAN DE TESTING

### Test Manual
1. ✅ Control deshabilitado → Comportamiento Odoo estándar
2. ✅ Control habilitado + Usuario NO autorizado + Almacén NO permitido → Error
3. ✅ Control habilitado + Usuario SÍ autorizado → Permitir
4. ✅ Control habilitado + Almacén SÍ permitido → Permitir
5. ✅ Control habilitado + Stock suficiente → Permitir
6. ✅ Solo en salidas (ignorar recepciones/transferencias internas)

### Test de Regresión
- ✅ No afectar transferencias de recepción
- ✅ No afectar transferencias internas
- ✅ No afectar ajustes de inventario

---

## 🚀 VENTAJAS DE ESTA PROPUESTA

✅ **Flexible**: Control granular por almacén y usuario
✅ **Configurable**: Sin necesidad de código, desde UI
✅ **Auditable**: Logs y mensajes de error detallados
✅ **Reversible**: Se puede desactivar en cualquier momento
✅ **Compatible**: No rompe funcionalidad existente
✅ **Performante**: Mínimo impacto en rendimiento
✅ **Escalable**: Fácil agregar más almacenes/usuarios

---

## ❓ PREGUNTAS PARA APROBAR

Antes de implementar, por favor confirma:

1. ✅ ¿La ubicación en "Inventario → Configuración → Ajustes" es correcta?
2. ✅ ¿Los nombres de los campos son descriptivos?
3. ✅ ¿La lógica de excepciones (almacén O usuario) es la esperada?
4. ✅ ¿El mensaje de error es claro para los usuarios finales?
5. ✅ ¿Prefieres Opción A (res.config.settings) u Opción B (modelo independiente)?
6. ✅ ¿Algún cambio en la UI/UX propuesta?

---

## 📊 RESUMEN EJECUTIVO

Esta propuesta implementa un **sistema de control de stock negativo configurable** que:

1. **Permite** que ciertos almacenes tengan stock negativo (lista configurable)
2. **Permite** que ciertos usuarios hagan salidas sin restricción (lista configurable)
3. **Bloquea** a todos los demás con un mensaje de error claro y detallado
4. **Se puede activar/desactivar** fácilmente desde Configuración de Inventario
5. **No afecta** el rendimiento ni la funcionalidad existente

**Tiempo estimado de implementación**: 2-3 horas
**Riesgo**: Bajo (cambios aislados, fácil de revertir)
**Impacto**: Alto (control completo sobre stock negativo)

---

## 🔔 PRÓXIMOS PASOS

Si apruebas esta propuesta, procederé a:

1. ✅ Modificar `models/models_resconfigsettings.py`
2. ✅ Modificar `views/res_config_settings_views.xml`
3. ✅ Modificar `models/models_stock_picking.py`
4. ✅ Actualizar `__manifest__.py`
5. ✅ Testing completo
6. ✅ Documentar en bitácora del día
7. ✅ Crear commit con documentación

---

**¿Apruebas esta propuesta para proceder con la implementación?** 🤔
