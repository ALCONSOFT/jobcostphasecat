# -*- coding: utf-8 -*-
"""
Pruebas para validación de proveedores en estado 'Esperando Comprador'
Autor: Claude Code
Fecha: 2025-01-28

Verifica que no se pueda enviar a aprobación una Purchase Request desde
el estado 'waiting_for_buyer' si existen productos sin proveedores asignados.
"""

import logging
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TestWaitingForBuyerValidation(TransactionCase):
    
    def setUp(self):
        super().setUp()
        
        # Crear proveedor
        self.vendor = self.env['res.partner'].create({
            'name': 'Proveedor Test Buyer',
            'is_company': True,
            'supplier_rank': 1,
        })
        
        # Crear producto SIN proveedor
        self.product_without_vendor = self.env['product.product'].create({
            'name': 'Producto Sin Proveedor',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
        })
        
        # Crear producto CON proveedor
        self.product_with_vendor = self.env['product.product'].create({
            'name': 'Producto Con Proveedor',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
        })
        
        # Asignar proveedor solo al segundo producto
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_with_vendor.product_tmpl_id.id,
            'partner_id': self.vendor.id,
            'price': 100.0,
        })
        
        # Obtener warehouse y picking type
        self.warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if not self.warehouse:
            self.warehouse = self.env['stock.warehouse'].create({
                'name': 'Test Warehouse Buyer',
                'code': 'TWB',
                'company_id': self.env.company.id,
            })
        
        self.picking_type = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', self.warehouse.id),
            ('code', '=', 'incoming')
        ], limit=1)

    def test_block_approval_with_missing_vendors(self):
        """Test: Bloquear envío a aprobación con productos sin proveedor"""
        _logger.info("🧪 Test: Bloqueo de envío a aprobación con productos sin proveedor")
        
        # 1. Crear Purchase Request en estado waiting_for_buyer
        pr = self.env['purchase.request'].create({
            'name': 'PR-BUYER-VALIDATION-BLOCK',
            'state': 'waiting_for_buyer',
            'warehouse_id': self.warehouse.id,
            'picking_type_id': self.picking_type.id,
        })
        
        # 2. Agregar producto SIN proveedor
        pr_line_without_vendor = self.env['purchase.request.line'].create({
            'purchase_request_id': pr.id,
            'product_id': self.product_without_vendor.id,
            'product_qty': 5.0,
            'product_uom': self.product_without_vendor.uom_id.id,
            'name': self.product_without_vendor.name,
        })
        # NO asignar vendedor: pr_line_without_vendor.vendor_ids = []
        
        # 3. Agregar producto CON proveedor
        pr_line_with_vendor = self.env['purchase.request.line'].create({
            'purchase_request_id': pr.id,
            'product_id': self.product_with_vendor.id,
            'product_qty': 3.0,
            'product_uom': self.product_with_vendor.uom_id.id,
            'name': self.product_with_vendor.name,
        })
        pr_line_with_vendor.vendor_ids = [(6, 0, [self.vendor.id])]
        
        # 4. Intentar enviar a aprobación (debe fallar)
        with self.assertRaises(ValidationError) as context:
            pr.action_submit_for_approver()
        
        # 5. Verificar mensaje de error
        error_msg = str(context.exception)
        self.assertIn("⚠️ ADVERTENCIA: No se puede enviar a aprobación", error_msg)
        self.assertIn("Existen productos sin proveedor asignado", error_msg)
        self.assertIn("Producto Sin Proveedor", error_msg)
        self.assertIn("Cant: 5.0", error_msg)
        
        # 6. Verificar que el estado NO cambió
        self.assertEqual(pr.state, 'waiting_for_buyer', "Estado debe permanecer en waiting_for_buyer")
        
        _logger.info("✅ Envío a aprobación correctamente bloqueado por productos sin proveedor")

    def test_allow_approval_with_all_vendors(self):
        """Test: Permitir envío a aprobación cuando todos los productos tienen proveedor"""
        _logger.info("🧪 Test: Permitir envío a aprobación con todos los proveedores asignados")
        
        # 1. Crear Purchase Request en estado waiting_for_buyer
        pr = self.env['purchase.request'].create({
            'name': 'PR-BUYER-VALIDATION-ALLOW',
            'state': 'waiting_for_buyer',
            'warehouse_id': self.warehouse.id,
            'picking_type_id': self.picking_type.id,
        })
        
        # 2. Agregar SOLO productos CON proveedor
        pr_line1 = self.env['purchase.request.line'].create({
            'purchase_request_id': pr.id,
            'product_id': self.product_with_vendor.id,
            'product_qty': 10.0,
            'product_uom': self.product_with_vendor.uom_id.id,
            'name': self.product_with_vendor.name,
        })
        pr_line1.vendor_ids = [(6, 0, [self.vendor.id])]
        
        # 3. Intentar enviar a aprobación (debe funcionar)
        pr.action_submit_for_approver()
        
        # 4. Verificar que el estado cambió correctamente
        self.assertEqual(pr.state, 'waiting_for_approver', 
                        "Estado debe cambiar a waiting_for_approver")
        
        # 5. Verificar mensaje informativo en chatter
        latest_message = pr.message_ids[0] if pr.message_ids else None
        self.assertIsNotNone(latest_message, "Debe haber mensaje en chatter")
        self.assertIn("✅ SdC enviada a aprobación", latest_message.body)
        self.assertIn("Todos los productos tienen proveedores", latest_message.body)
        
        _logger.info("✅ Envío a aprobación permitido con todos los proveedores asignados")

    def test_multiple_products_without_vendors(self):
        """Test: Lista detallada de múltiples productos sin proveedor"""
        _logger.info("🧪 Test: Mensaje detallado con múltiples productos sin proveedor")
        
        # 1. Crear más productos sin proveedor
        product2 = self.env['product.product'].create({
            'name': 'Segundo Producto Sin Proveedor',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
        })
        
        product3 = self.env['product.product'].create({
            'name': 'Tercer Producto Sin Proveedor',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
        })
        
        # 2. Crear Purchase Request
        pr = self.env['purchase.request'].create({
            'name': 'PR-MULTIPLE-MISSING-VENDORS',
            'state': 'waiting_for_buyer',
            'warehouse_id': self.warehouse.id,
            'picking_type_id': self.picking_type.id,
        })
        
        # 3. Agregar múltiples productos sin proveedor
        products_without_vendors = [
            (self.product_without_vendor, 5.0),
            (product2, 7.5),
            (product3, 12.0)
        ]
        
        for product, qty in products_without_vendors:
            self.env['purchase.request.line'].create({
                'purchase_request_id': pr.id,
                'product_id': product.id,
                'product_qty': qty,
                'product_uom': product.uom_id.id,
                'name': product.name,
            })
        
        # 4. Intentar enviar a aprobación
        with self.assertRaises(ValidationError) as context:
            pr.action_submit_for_approver()
        
        # 5. Verificar que el mensaje incluye todos los productos
        error_msg = str(context.exception)
        self.assertIn("Producto Sin Proveedor", error_msg)
        self.assertIn("Segundo Producto Sin Proveedor", error_msg)
        self.assertIn("Tercer Producto Sin Proveedor", error_msg)
        self.assertIn("Cant: 5.0", error_msg)
        self.assertIn("Cant: 7.5", error_msg)
        self.assertIn("Cant: 12.0", error_msg)
        
        _logger.info("✅ Mensaje detallado correcto para múltiples productos sin proveedor")

    def test_ignore_section_lines_in_validation(self):
        """Test: Ignorar líneas de sección en la validación"""
        _logger.info("🧪 Test: Ignorar líneas de sección/nota en validación")
        
        # 1. Crear Purchase Request
        pr = self.env['purchase.request'].create({
            'name': 'PR-SECTION-LINES-TEST',
            'state': 'waiting_for_buyer',
            'warehouse_id': self.warehouse.id,
            'picking_type_id': self.picking_type.id,
        })
        
        # 2. Agregar línea de sección (sin producto)
        self.env['purchase.request.line'].create({
            'purchase_request_id': pr.id,
            'display_type': 'line_section',
            'name': 'SECCIÓN DE PRODUCTOS',
            'product_qty': 0,
        })
        
        # 3. Agregar línea de nota (sin producto)
        self.env['purchase.request.line'].create({
            'purchase_request_id': pr.id,
            'display_type': 'line_note',
            'name': 'Nota: Productos especiales',
            'product_qty': 0,
        })
        
        # 4. Agregar producto CON proveedor
        pr_line = self.env['purchase.request.line'].create({
            'purchase_request_id': pr.id,
            'product_id': self.product_with_vendor.id,
            'product_qty': 8.0,
            'product_uom': self.product_with_vendor.uom_id.id,
            'name': self.product_with_vendor.name,
        })
        pr_line.vendor_ids = [(6, 0, [self.vendor.id])]
        
        # 5. Envío a aprobación debe funcionar (ignorar líneas sin producto)
        pr.action_submit_for_approver()
        
        # 6. Verificar transición exitosa
        self.assertEqual(pr.state, 'waiting_for_approver', 
                        "Debe permitir aprobación ignorando líneas de sección/nota")
        
        _logger.info("✅ Líneas de sección/nota correctamente ignoradas en validación")

    def test_comprehensive_waiting_for_buyer_scenario(self):
        """Test: Escenario completo de validación en estado waiting_for_buyer"""
        _logger.info("\n" + "="*70)
        _logger.info("📋 ESCENARIO COMPLETO: VALIDACIÓN EN ESTADO 'ESPERANDO COMPRADOR'")
        _logger.info("="*70)
        
        # === FASE 1: CREACIÓN DE PR CON PRODUCTOS MIXTOS ===
        _logger.info("\n🔍 FASE 1: Creación de PR con productos mixtos")
        
        pr = self.env['purchase.request'].create({
            'name': 'PR-COMPREHENSIVE-BUYER-VALIDATION',
            'state': 'waiting_for_buyer',
            'warehouse_id': self.warehouse.id,
            'picking_type_id': self.picking_type.id,
        })
        
        # Producto CON proveedor
        line_ok = self.env['purchase.request.line'].create({
            'purchase_request_id': pr.id,
            'product_id': self.product_with_vendor.id,
            'product_qty': 15.0,
            'product_uom': self.product_with_vendor.uom_id.id,
            'name': self.product_with_vendor.name,
        })
        line_ok.vendor_ids = [(6, 0, [self.vendor.id])]
        
        # Producto SIN proveedor
        self.env['purchase.request.line'].create({
            'purchase_request_id': pr.id,
            'product_id': self.product_without_vendor.id,
            'product_qty': 20.0,
            'product_uom': self.product_without_vendor.uom_id.id,
            'name': self.product_without_vendor.name,
        })
        # No asignar proveedor intencionalmente
        
        _logger.info(f"   • PR creada: {pr.name}")
        _logger.info(f"   • Estado inicial: {pr.state}")
        _logger.info(f"   • Líneas totales: {len(pr.pr_lines)}")
        
        # === FASE 2: INTENTO DE APROBACIÓN (DEBE FALLAR) ===
        _logger.info("\n❌ FASE 2: Intento de envío a aprobación (debe fallar)")
        
        with self.assertRaises(ValidationError) as context:
            pr.action_submit_for_approver()
        
        error_msg = str(context.exception)
        _logger.info(f"   • Error capturado: {error_msg[:100]}...")
        
        # Verificar estado sin cambios
        self.assertEqual(pr.state, 'waiting_for_buyer')
        _logger.info(f"   • Estado permanece: {pr.state} ✅")
        
        # === FASE 3: CORRECCIÓN DE PROVEEDORES ===
        _logger.info("\n🔧 FASE 3: Corrección - Asignar proveedores faltantes")
        
        # Encontrar línea sin proveedor y asignarle uno
        line_without_vendor = pr.pr_lines.filtered(lambda l: l.product_id == self.product_without_vendor)
        line_without_vendor.vendor_ids = [(6, 0, [self.vendor.id])]
        
        _logger.info(f"   • Proveedor asignado a: {self.product_without_vendor.name}")
        
        # === FASE 4: SEGUNDO INTENTO (DEBE FUNCIONAR) ===
        _logger.info("\n✅ FASE 4: Segundo intento de envío a aprobación")
        
        pr.action_submit_for_approver()
        
        # Verificar transición exitosa
        self.assertEqual(pr.state, 'waiting_for_approver')
        _logger.info(f"   • Estado cambió a: {pr.state} ✅")
        
        # Verificar mensaje en chatter
        success_messages = pr.message_ids.filtered(
            lambda m: "✅ SdC enviada a aprobación" in (m.body or "")
        )
        self.assertTrue(success_messages)
        _logger.info("   • Mensaje de éxito registrado en chatter ✅")
        
        # === CONCLUSIÓN ===
        _logger.info("\n🎉 CONCLUSIÓN: VALIDACIÓN 'ESPERANDO COMPRADOR' FUNCIONAL")
        _logger.info("   ✅ Validación bloquea productos sin proveedor")
        _logger.info("   ✅ Permite aprobación con todos los proveedores asignados")  
        _logger.info("   ✅ Mensajes informativos correctos")
        _logger.info("   ✅ Flujo de trabajo controlado correctamente")
        _logger.info("="*70)