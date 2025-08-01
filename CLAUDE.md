# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is an Odoo 16 addon called "jobcostphasecat" (Job Cost by Phases and Categories) - a comprehensive project management module that extends Odoo's core functionality to handle project phases, categories, and cost management across purchase requests, purchase orders, stock operations, and invoicing.

## Architecture & Structure

### Core Module Design
- **Base**: Inherits from multiple Odoo modules including `bi_odoo_project_phases`, `stock_analytic`, `ethics_purchase_request`, `purchase`, `purchase_discount`, `account_fleet`
- **Purpose**: Provides phase and category management across procurement and inventory workflows
- **Integration**: Deep integration with Odoo's purchase, stock, and accounting modules

### Key Model Extensions
- **Purchase Workflow**: Extended purchase requests, purchase orders with phases, categories, vehicles, and analytic accounts
- **Stock Operations**: Enhanced stock pickings, moves, and move lines with analytic data
- **Accounting**: Invoice integration with fleet management and analytic distributions
- **Configuration**: Centralized settings for warehouse-user relationships and default values

### Directory Structure
```
models/           # Core business logic and model extensions
views/            # XML view definitions and UI layouts  
report/           # Custom reports and templates
security/         # Access rights and security rules
data/             # Data files and email templates
static/           # Static assets (images, CSV data)
```

## Development Commands

### Running Odoo
```bash
# Start Odoo server from parent directory
cd /Users/alconor/proyectos/devenv/odoo16c
python3 odoo-bin -c odoo16c.conf
```

### Database Operations
```bash
# Quick database analysis (from odoo16c directory)
./resumen_rapido.sh
```

## Key Functionality Areas

### Purchase Request & Order Management
- Multi-state workflow: draft → sent → waiting_for_price_revision → waiting_for_price_approval → waiting_for_approval → waiting_for_audit → waiting_for_buyer
- Phase and category tracking throughout procurement lifecycle
- Vehicle assignment and analytic account distribution
- Discount management (line-level and global)
- Email integration with attachment merging

### Stock & Inventory Integration
- Analytic account propagation from purchase to stock operations
- Phase/category inheritance in stock moves and pickings
- Warehouse-specific default configurations
- Internal transfer enhancements with purchase request linking

### Reporting & Analytics
- Custom purchase request reports
- Enhanced purchase order reports with custom headers
- Analytics integration for cost tracking by phase/category

## Configuration Management

### Settings Location
- Configuration options in `models/models_resconfigsettings.py`
- User-warehouse relationships in `models/models_stock_warehouse.py`
- Default values management in `models/models_valores_defaults.py`

### Key Configuration Areas
- Phase requirement enforcement for purchase requests and stock transfers
- Template duplication controls for stock operations
- Warehouse access restrictions by user
- Email template customizations with purchase request/order links

## Security & Access Control

### Security Files
- `security/ir.model.access.csv` - Model access definitions
- `security/security_view.xml` - UI security groups
- `security/purchase_request_rules.xml` - Record-level rules

### Key Security Groups
- Purchase approval workflows with multi-level authorization
- Warehouse access restrictions
- Document deletion restrictions for finalized states

## Testing & Quality Assurance

This is an Odoo addon, so testing follows Odoo conventions:
- Unit tests should inherit from `odoo.tests.common.TransactionCase`
- Integration tests for workflow state transitions
- Test data setup using Odoo's demo data patterns

## Development Notes

### Code Patterns
- Model inheritance using `_inherit` for extending existing Odoo models
- State management with `selection` fields and workflow methods
- Computed fields with `@api.depends` decorators
- XML view inheritance for UI customizations

### Important Dependencies
- Requires specific third-party modules (see `__manifest__.py` depends list)
- Integrates with Odoo's purchase, stock, and account modules
- Uses analytic accounting features extensively

### Change Management
- Detailed change log maintained in `__manifest__.py` description
- Version format: YYYY.MM.DD with time stamps
- Feature additions carefully documented with implementation dates