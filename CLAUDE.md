# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Odoo 16 module named `jobcostphasecat` (Job Cost by phases and categories) that provides project management functionality by phases and categories. It's part of a larger Odoo 16 installation managed via Docker.

## Architecture

### Core Models
- `project.category` - Job cost categories with cost type relationships
- `project.costtype` - Cost types for job cost management
- Extended models inheriting from standard Odoo modules:
  - `purchase.request` - Purchase requests with vehicle, warehouse, and audit workflow
  - `purchase.order` - Purchase orders with enhanced approval flows
  - `stock.picking`, `stock.move` - Inventory operations with analytic tracking
  - `account.move` - Invoice integration with vehicle and analytic data

### Key Features
- Multi-state approval workflow for purchase requests and orders
- Vehicle fleet integration across purchase and inventory workflows  
- Analytic account distribution for project cost tracking
- Email template system with attachment handling
- Custom reporting for purchase requests and orders
- Warehouse-based access restrictions

### Dependencies
The module depends on several other modules:
- `bi_odoo_project_phases` - Project phase management
- `stock_analytic` - Inventory analytic account integration
- `ethics_purchase_request` - Base purchase request functionality
- `purchase_discount` - Purchase order discount features
- `account_fleet` - Vehicle integration in accounting
- `email_template_qweb` - Enhanced email templates

## Development Commands

### Docker Operations
```bash
# Start the Odoo 16 development environment
docker-compose up -d

# Update the module after changes
docker-compose exec web030 odoo -c /etc/odoo/odoo.conf -u jobcostphasecat -d p16_TSI_2

# View logs
docker-compose logs -f web030

# Stop services
docker-compose down
```

### Database Management
The module uses PostgreSQL on port 32030 with database `p16_TSI_2`.

## File Structure

### Models (`models/`)
- `models.py` - Core category and cost type models
- `models_ethics_purchase_request.py` - Purchase request extensions
- `models_purchase.py` - Purchase order extensions
- `models_stock*.py` - Inventory operation extensions
- `account_move.py` - Invoice/accounting extensions

### Views (`views/`)
- `views_ethics_purchase_request.xml` - Purchase request UI
- `views_purchase_order.xml` - Purchase order UI
- `view_picking.xml` - Inventory transfer UI
- `views_categories.xml` - Category management UI

### Reports (`report/`)
- `purchase_request_report_template.xml` - Purchase request report layout
- `purchase_order_report.xml` - Purchase order report customization

### Security (`security/`)
- `ir.model.access.csv` - Model access permissions
- `purchase_request_rules.xml` - Record-level security rules

## Development Notes

- The module extends core Odoo purchase and inventory workflows
- State management includes custom states like `waiting_for_audit`, `waiting_for_price_revision`
- Vehicle integration requires proper fleet module configuration
- Email templates support QWeb rendering and attachment merging
- Analytic account integration requires proper project/account setup

## Testing

No specific test framework is configured - verify functionality through the Odoo web interface after module updates.

---

## 🔔 PROTOCOLO OBLIGATORIO - Sistema de Bitácoras

### Recordatorios Automáticos para Claude Code

**Al INICIO de cada sesión, Claude Code DEBE:**

1. ✅ Verificar si existe `.sessions/YYYY-MM-DD.md` del día actual
2. ✅ Si NO existe, preguntar al usuario:
   ```
   ⚠️ No he detectado bitácora de hoy (.sessions/2025-10-09.md)
   ¿Quieres que la cree con una plantilla base? (y/n)
   ```
3. ✅ Si existe, leerla para entender el contexto de la sesión actual

**Durante la sesión:**

- Mantener registro mental de cambios importantes
- Sugerir actualizar la bitácora después de cambios significativos

**Al FINALIZAR la sesión, Claude Code DEBE recordar:**

1. ✅ Actualizar `.sessions/YYYY-MM-DD.md` con:
   - Cambios realizados
   - Decisiones técnicas tomadas
   - Archivos modificados
   - Pendientes para próxima sesión

2. ✅ Actualizar `ENVIRONMENT_STATUS.md` si hubo deploy a algún ambiente

3. ✅ Preguntar:
   ```
   📝 ¿Deseas que actualice la bitácora con el resumen de la sesión? (y/n)
   ```

### Sistema de Archivos de Seguimiento

#### `.sessions/YYYY-MM-DD.md` - Bitácora Diaria
- Registro de actividades del día
- Decisiones técnicas tomadas
- Cambios realizados en código
- Pendientes y próximos pasos
- Contexto importante para futuras sesiones

#### `ENVIRONMENT_STATUS.md` - Estado de Ambientes
- Estado actual de desarrollo, pruebas y producción
- Último commit deployado en cada ambiente
- Issues conocidos por ambiente
- Historial de deploys

### Git Hook Pre-Commit

El sistema tiene un git hook que RECORDARÁ al usuario actualizar la bitácora antes de cada commit.

**Comportamiento del hook:**
- ✅ Verifica existencia de `.sessions/YYYY-MM-DD.md`
- ✅ Verifica si fue actualizada hoy
- ⚠️ Pregunta al usuario si desea continuar sin bitácora actualizada
- ❌ Permite cancelar el commit para actualizar primero

### Plantilla de Bitácora

```markdown
# YYYY-MM-DD - Título de la Sesión

## 🎯 Objetivo de la Sesión
[Describe qué se planea hacer]

## ✅ Cambios Realizados
- Cambio 1
- Cambio 2

## 🔍 Decisiones Técnicas
- Decisión 1: Razón
- Decisión 2: Razón

## 📋 Pendiente
- [ ] Tarea pendiente 1
- [ ] Tarea pendiente 2

## 🔄 Archivos Modificados
- archivo1.py (descripción)
- archivo2.xml (descripción)

## 💡 Contexto para Claude Code
[Información importante que Claude debe recordar en próximas sesiones]
```

### Flujo de Trabajo Recomendado

```
1. Inicio de sesión
   ↓
2. Claude Code verifica bitácora del día
   ↓
3. Trabajo de desarrollo
   ↓
4. Actualización periódica de bitácora
   ↓
5. Al hacer commit: Git hook verifica bitácora
   ↓
6. Al finalizar: Claude sugiere actualizar resumen
   ↓
7. (Opcional) Actualizar ENVIRONMENT_STATUS.md si hubo deploy
```

### Beneficios del Sistema

- 📝 **Trazabilidad completa** de cambios y decisiones
- 🔄 **Continuidad** entre sesiones de desarrollo
- 🤖 **Claude Code informado** del contexto actual
- 🎯 **Seguimiento** de pendientes y próximos pasos
- 📊 **Visibilidad** del estado de cada ambiente

### Comandos Útiles

```bash
# Crear bitácora del día manualmente
cp .sessions/2025-10-09.md .sessions/$(date +%Y-%m-%d).md

# Ver última bitácora
ls -lt .sessions/ | head -2

# Verificar estado de ambientes
cat ENVIRONMENT_STATUS.md
```

---