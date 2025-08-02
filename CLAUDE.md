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