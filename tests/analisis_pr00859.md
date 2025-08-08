# Análisis PR00859 - Botón Descartar no visible

## 🔍 Problema Reportado
- **Purchase Request**: PR00859
- **Estado mostrado en UI**: "Confirmed"
- **Purchase Orders relacionadas**: Estado "Cancelada"
- **Problema**: No aparece el botón "Descartar"

## 📋 Condiciones para que aparezca el botón "Descartar"

### 1. Condiciones de XML (views_ethics_purchase_request.xml:111-117)
```xml
<button name="action_descarted" 
        string="Descartar" 
        type="object" 
        groups="account.group_account_manager,purchase.group_purchase_manager"
        attrs="{'invisible': [('state', '!=', 'to_approve')]}"
        confirm="¿Está seguro de que desea descartar esta solicitud de compra? Esta acción no se puede deshacer."
        class="btn-danger"/>
```

**Requisitos del XML:**
- ✅ **Grupos requeridos**: `account.group_account_manager` O `purchase.group_purchase_manager`
- ❌ **Estado requerido**: `state` == `'to_approve'` (NO `'confirm'`)

### 2. Condiciones del método Python (models_ethics_purchase_request.py:617-645)
```python
def action_descarted(self):
    # 1. Verificar permisos de usuario
    if not (self.env.user.has_group('account.group_account_manager') or 
            self.env.user.has_group('purchase.group_purchase_manager')):
        raise UserError(_("Solo los aprobadores pueden descartar solicitudes."))
    
    # 2. Verificar estado
    if self.state != 'to_approve':
        raise UserError(_("Solo se pueden descartar solicitudes en estado 'Confirmado'."))
    
    # 3. Verificar Purchase Orders relacionadas
    related_pos = self.env['purchase.order'].search([('request_id', '=', self.id)])
    for po in related_pos:
        if po.state in ['locked', 'purchase']:
            raise UserError(_(
                "No se puede descartar esta solicitud. "
                "La Orden de Compra %s está en estado '%s'. "
                "Las SdP relacionadas no pueden estar en estado 'Bloqueada' o 'Orden de Compra'."
            ) % (po.name, po.state))
```

## 🚨 DIAGNÓSTICO DEL PROBLEMA

### Problema Principal: Estado Incorrecto
El botón solo aparece cuando `state == 'to_approve'`, pero reportas que está en "Confirmed".

**Estados posibles en Purchase Request:**
- `draft` - Borrador
- `waiting_for_verifier` - Esperando Verificador
- `waiting_for_audit` - Esperando Auditoría  
- `waiting_for_buyer` - Esperando Comprador
- `waiting_for_approver` - Esperando Aprobador
- `to_approve` - **Confirmado** ← REQUERIDO PARA BOTÓN
- `confirm` - Confirmado (diferente de `to_approve`)
- `descarted` - Descartado
- `cancel` - Cancelado

### 💡 Posibles Causas

#### Causa 1: Confusión entre estados `to_approve` vs `confirm`
- **UI muestra**: "Confirmed" 
- **Estado real**: Podría ser `confirm` (no `to_approve`)
- **Solución**: Verificar en Developer Mode el estado real del campo

#### Causa 2: Purchase Request no ha llegado al estado correcto
- **Flujo esperado**: `draft` → ... → `to_approve` → `confirm`
- **Estado actual**: Posiblemente `confirm` (ya aprobado)
- **Problema**: Una vez aprobado (`confirm`), ya no se puede descartar

## 🔧 Pasos para Verificar y Solucionar

### 1. Verificar Estado Real
```python
# En consola de Odoo o Developer Mode
pr = env['purchase.request'].browse(ID_DE_PR00859)
print(f"Estado real: {pr.state}")
```

### 2. Verificar Permisos de Usuario
```python
user = env.user
print(f"Tiene group_account_manager: {user.has_group('account.group_account_manager')}")
print(f"Tiene group_purchase_manager: {user.has_group('purchase.group_purchase_manager')}")
```

### 3. Verificar Purchase Orders Relacionadas
```python
pos = env['purchase.order'].search([('request_id', '=', ID_DE_PR00859)])
for po in pos:
    print(f"PO: {po.name}, Estado: {po.state}")
```

## 🚨 Escenarios Posibles

### Escenario A: Estado ya es `confirm` (Aprobado)
**Problema**: La PR ya fue aprobada y pasó de `to_approve` a `confirm`
**Solución**: 
1. Si necesitas descartarla, debes revertir el estado a `to_approve`
2. O modificar las condiciones del botón para permitir `confirm`

### Escenario B: Usuario sin permisos
**Problema**: Usuario no tiene grupos requeridos
**Solución**: Asignar grupos `account.group_account_manager` o `purchase.group_purchase_manager`

### Escenario C: Purchase Orders bloqueadas
**Problema**: Aunque las PO estén "Canceladas", podrían estar en estado `locked` o `purchase`
**Solución**: Verificar estados reales de las PO

## 📝 Pruebas Recomendadas

### Prueba 1: Verificación de Estado
1. Ir a PR00859 en modo Developer
2. Verificar campo `state`
3. Confirmar si es `to_approve` o `confirm`

### Prueba 2: Test de Visibilidad del Botón
```python
def test_boton_visibilidad():
    pr = env['purchase.request'].browse(ID_PR00859)
    
    # Test condición XML
    boton_visible = pr.state == 'to_approve'
    print(f"Botón debería ser visible: {boton_visible}")
    
    # Test condiciones método
    user = env.user
    tiene_permisos = (user.has_group('account.group_account_manager') or 
                     user.has_group('purchase.group_purchase_manager'))
    
    pos = env['purchase.order'].search([('request_id', '=', pr.id)])
    po_bloqueadas = any(po.state in ['locked', 'purchase'] for po in pos)
    
    puede_ejecutar = boton_visible and tiene_permisos and not po_bloqueadas
    print(f"Método se puede ejecutar: {puede_ejecutar}")
```

### Prueba 3: Simulación de Cambio de Estado
```python
# SOLO SI ES NECESARIO Y TIENES RESPALDO
pr = env['purchase.request'].browse(ID_PR00859)
if pr.state == 'confirm':
    # Cambiar temporalmente para probar botón
    pr.state = 'to_approve'
    # Ahora debería aparecer el botón
    # IMPORTANTE: Evaluar impacto antes de hacer esto en producción
```

## 🎯 Recomendación Final

**Lo más probable es que PR00859 esté en estado `confirm` (ya aprobado) en lugar de `to_approve` (pendiente de aprobación).**

Para confirmar esto:
1. Verificar el estado real en Developer Mode
2. Si está en `confirm`, evaluar si realmente necesitas descartar una solicitud ya aprobada
3. Si es necesario, considerar modificar la lógica para permitir descartar solicitudes aprobadas bajo ciertas condiciones

¿Quieres que revisemos el estado actual de PR00859 directamente en la interfaz de Odoo?