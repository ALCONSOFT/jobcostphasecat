# -*- coding: utf-8 -*-
"""
Pruebas para re-aprobación de Purchase Requests con Purchase Orders canceladas
Autor: Claude Code
Fecha: 2025-01-28

Verifica que se pueda re-aprobar una Purchase Request después de cancelar
todas las Purchase Orders relacionadas (caso PR00851).
"""

import logging
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TestReApprovalWithCancelledPO(TransactionCase):
    
    def setUp(self):
        super().setUp()
        
        # Crear proveedor
        self.vendor = self.env['res.partner'].create({
            'name': 'Proveedor Test Re-aprobación',
            'is_company': True,
            'supplier_rank': 1,
        })
        
        # Crear producto con proveedor
        self.product = self.env['product.product'].create({
            'name': 'Producto Test Re-aprobación',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
        })
        
        # Asignar proveedor al producto
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'partner_id': self.vendor.id,
            'price': 150.0,
        })
        
        # Obtener warehouse y picking type
        self.warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if not self.warehouse:
            self.warehouse = self.env['stock.warehouse'].create({
                'name': 'Test Warehouse Re-approval',
                'code': 'TWR',
                'company_id': self.env.company.id,
            })
        
        self.picking_type = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', self.warehouse.id),
            ('code', '=', 'incoming')
        ], limit=1)

    def test_re_approval_with_all_cancelled_po(self):
        """Test: Permitir re-aprobación cuando todas las PO están canceladas"""
        _logger.info("🧪 Test: Re-aprobación con todas las Purchase Orders canceladas")
        
        # 1. Crear Purchase Request
        pr = self.env['purchase.request'].create({
            'name': 'PR-RE-APPROVAL-TEST',
            'state': 'to_approve',
            'warehouse_id': self.warehouse.id,
            'picking_type_id': self.picking_type.id,
        })
        
        # 2. Agregar línea con proveedor
        pr_line = self.env['purchase.request.line'].create({
            'purchase_request_id': pr.id,
            'product_id': self.product.id,
            'product_qty': 10.0,
            'product_uom': self.product.uom_id.id,
            'name': self.product.name,
        })
        pr_line.vendor_ids = [(6, 0, [self.vendor.id])]
        
        # 3. Primera aprobación (debe funcionar)
        pr.action_confirm()
        self.assertEqual(pr.state, 'confirm', "Primera aprobación debe ser exitosa")
        
        # 4. Verificar que se crearon Purchase Orders
        purchase_orders = self.env['purchase.order'].search([('pr_ref_id', '=', pr.id)])
        self.assertTrue(purchase_orders, "Deben crearse Purchase Orders en la primera aprobación")
        
        # 5. Cancelar todas las Purchase Orders (simular situación PR00851)
        for po in purchase_orders:
            po.button_cancel()
            self.assertEqual(po.state, 'cancel', f"PO {po.name} debe estar cancelada")
        
        # 6. Cambiar estado de PR para simular necesidad de re-aprobación
        pr.state = 'to_approve'
        
        # 7. Intentar segunda aprobación (debe funcionar ahora)
        pr.action_confirm()
        self.assertEqual(pr.state, 'confirm', "Re-aprobación debe ser exitosa con PO canceladas")
        
        # 8. Verificar que se crearon nuevas Purchase Orders
        new_purchase_orders = self.env['purchase.order'].search([
            ('pr_ref_id', '=', pr.id),
            ('state', '!=', 'cancel')
        ])
        self.assertTrue(new_purchase_orders, "Deben crearse nuevas Purchase Orders en la re-aprobación")
        
        _logger.info("✅ Re-aprobación exitosa con Purchase Orders canceladas")

    def test_block_re_approval_with_active_po(self):
        """Test: Bloquear re-aprobación cuando hay Purchase Orders activas"""
        _logger.info("🧪 Test: Bloqueo de re-aprobación con Purchase Orders activas")
        
        # 1. Crear Purchase Request
        pr = self.env['purchase.request'].create({
            'name': 'PR-BLOCK-REAPPROVAL-TEST',
            'state': 'to_approve',
            'warehouse_id': self.warehouse.id,
            'picking_type_id': self.picking_type.id,
        })
        
        # 2. Agregar línea con proveedor
        pr_line = self.env['purchase.request.line'].create({
            'purchase_request_id': pr.id,
            'product_id': self.product.id,
            'product_qty': 5.0,
            'product_uom': self.product.uom_id.id,
            'name': self.product.name,
        })
        pr_line.vendor_ids = [(6, 0, [self.vendor.id])]
        
        # 3. Primera aprobación
        pr.action_confirm()
        self.assertEqual(pr.state, 'confirm')
        
        # 4. Verificar Purchase Orders creadas
        purchase_orders = self.env['purchase.order'].search([('pr_ref_id', '=', pr.id)])
        self.assertTrue(purchase_orders)
        
        # 5. Dejar las Purchase Orders ACTIVAS (no cancelar)
        for po in purchase_orders:
            self.assertNotEqual(po.state, 'cancel', "PO debe estar activa para esta prueba")
        
        # 6. Intentar cambiar estado para re-aprobar
        pr.state = 'to_approve'
        
        # 7. Intentar segunda aprobación (debe fallar)
        with self.assertRaises(UserError) as context:
            pr.action_confirm()
        
        # 8. Verificar mensaje de error mejorado
        error_msg = str(context.exception)
        self.assertIn("Ya existen Solicitudes de Pedido (SdP) ACTIVAS", error_msg)
        self.assertIn("Para re-aprobar esta SdC", error_msg)
        
        _logger.info("✅ Re-aprobación correctamente bloqueada con Purchase Orders activas")

    def test_mixed_cancelled_and_active_po(self):
        """Test: Bloquear si hay mezcla de PO canceladas y activas"""
        _logger.info("🧪 Test: Bloqueo con mezcla de Purchase Orders")
        
        # 1. Crear Purchase Request
        pr = self.env['purchase.request'].create({
            'name': 'PR-MIXED-PO-TEST',
            'state': 'to_approve',
            'warehouse_id': self.warehouse.id,
            'picking_type_id': self.picking_type.id,
        })
        
        # 2. Agregar líneas para generar múltiples PO
        for i in range(2):
            pr_line = self.env['purchase.request.line'].create({
                'purchase_request_id': pr.id,
                'product_id': self.product.id,
                'product_qty': 3.0 + i,
                'product_uom': self.product.uom_id.id,
                'name': f"{self.product.name} - Línea {i+1}",
            })
            pr_line.vendor_ids = [(6, 0, [self.vendor.id])]
        
        # 3. Primera aprobación
        pr.action_confirm()
        
        # 4. Obtener Purchase Orders
        purchase_orders = self.env['purchase.order'].search([('pr_ref_id', '=', pr.id)])
        self.assertTrue(len(purchase_orders) >= 1, "Debe haber al menos 1 Purchase Order")
        
        # 5. Cancelar solo ALGUNAS Purchase Orders (simular estado mixto)
        if len(purchase_orders) > 1:
            purchase_orders[0].button_cancel()  # Cancelar la primera
            # Dejar las demás activas
        else:
            # Si solo hay una PO, crear otra manualmente para simular estado mixto
            po_cancelled = purchase_orders[0]
            po_cancelled.button_cancel()
            
            # Crear una PO activa manualmente
            self.env['purchase.order'].create({
                'partner_id': self.vendor.id,
                'pr_ref_id': pr.id,
                'state': 'draft',  # Estado activo
            })
        
        # 6. Intentar re-aprobación
        pr.state = 'to_approve'
        
        with self.assertRaises(UserError) as context:
            pr.action_confirm()
        
        # 7. Debe fallar porque hay PO activas
        error_msg = str(context.exception)
        self.assertIn("Ya existen Solicitudes de Pedido (SdP) ACTIVAS", error_msg)
        
        _logger.info("✅ Correctamente bloqueado con mezcla de Purchase Orders")

    def test_chatter_message_on_re_approval(self):
        """Test: Verificar mensaje en chatter durante re-aprobación"""
        _logger.info("🧪 Test: Mensaje en chatter durante re-aprobación")
        
        # 1. Crear y aprobar PR
        pr = self.env['purchase.request'].create({
            'name': 'PR-CHATTER-TEST',
            'state': 'to_approve',
            'warehouse_id': self.warehouse.id,
            'picking_type_id': self.picking_type.id,
        })
        
        pr_line = self.env['purchase.request.line'].create({
            'purchase_request_id': pr.id,
            'product_id': self.product.id,
            'product_qty': 7.0,
            'product_uom': self.product.uom_id.id,
            'name': self.product.name,
        })
        pr_line.vendor_ids = [(6, 0, [self.vendor.id])]
        
        pr.action_confirm()
        
        # 2. Cancelar todas las PO
        purchase_orders = self.env['purchase.order'].search([('pr_ref_id', '=', pr.id)])
        for po in purchase_orders:
            po.button_cancel()
        
        # 3. Contar mensajes antes de re-aprobación
        initial_message_count = len(pr.message_ids)
        
        # 4. Re-aprobar
        pr.state = 'to_approve'
        pr.action_confirm()
        
        # 5. Verificar que se agregó mensaje de re-aprobación
        final_message_count = len(pr.message_ids)
        self.assertGreater(final_message_count, initial_message_count, 
                          "Debe agregarse mensaje de re-aprobación al chatter")
        
        # 6. Verificar contenido del mensaje más reciente
        latest_message = pr.message_ids[0]  # Último mensaje
        self.assertIn("RE-APROBACIÓN DETECTADA", latest_message.body)
        self.assertIn("Purchase Orders canceladas", latest_message.body)
        
        _logger.info("✅ Mensaje de re-aprobación correctamente registrado en chatter")

    def test_re_approval_comprehensive_scenario(self):
        """Test: Escenario completo PR00851 - De problema a solución"""
        _logger.info("\n" + "="*70)
        _logger.info("📋 ESCENARIO COMPLETO PR00851: RE-APROBACIÓN CON SdP CANCELADAS")
        _logger.info("="*70)
        
        # === FASE 1: SITUACIÓN INICIAL PROBLEMÁTICA ===
        _logger.info("\n🔍 FASE 1: Situación inicial (similar a PR00851)")
        
        pr = self.env['purchase.request'].create({
            'name': 'PR00851-COMPREHENSIVE',
            'state': 'to_approve',
            'warehouse_id': self.warehouse.id,
            'picking_type_id': self.picking_type.id,
        })
        
        # Agregar producto CON proveedor (ya solucionamos el problema de productos sin proveedor)
        pr_line = self.env['purchase.request.line'].create({
            'purchase_request_id': pr.id,
            'product_id': self.product.id,
            'product_qty': 15.0,
            'product_uom': self.product.uom_id.id,
            'name': self.product.name,
        })
        pr_line.vendor_ids = [(6, 0, [self.vendor.id])]
        
        # === FASE 2: PRIMERA APROBACIÓN ===
        _logger.info("\n✅ FASE 2: Primera aprobación exitosa")
        pr.action_confirm()
        self.assertEqual(pr.state, 'confirm')
        
        # Verificar creación de Purchase Orders
        purchase_orders = self.env['purchase.order'].search([('pr_ref_id', '=', pr.id)])
        initial_po_count = len(purchase_orders)
        _logger.info(f"   • Se crearon {initial_po_count} Purchase Orders")
        
        # === FASE 3: CANCELACIÓN DE PURCHASE ORDERS ===
        _logger.info("\n❌ FASE 3: Cancelación de todas las Purchase Orders")
        for po in purchase_orders:
            po.button_cancel()
            _logger.info(f"   • PO {po.name} cancelada (Estado: {po.state})")
        
        # === FASE 4: INTENTO DE RE-APROBACIÓN ===
        _logger.info("\n🔄 FASE 4: Intento de re-aprobación")
        pr.state = 'to_approve'  # Simular necesidad de re-aprobación
        
        # Antes de la mejora: Esto habría fallado con "Ya existen SdP..."
        # Después de la mejora: Debe funcionar
        pr.action_confirm()
        
        # === FASE 5: VERIFICACIÓN DE RESULTADOS ===
        _logger.info("\n✅ FASE 5: Verificación de resultados")
        
        # Verificar estado final
        self.assertEqual(pr.state, 'confirm', "PR debe estar en estado 'confirm'")
        _logger.info("   • Estado de PR: confirm ✅")
        
        # Verificar nuevas Purchase Orders
        all_purchase_orders = self.env['purchase.order'].search([('pr_ref_id', '=', pr.id)])
        active_purchase_orders = all_purchase_orders.filtered(lambda po: po.state != 'cancel')
        
        self.assertTrue(active_purchase_orders, "Deben existir nuevas Purchase Orders activas")
        _logger.info(f"   • Purchase Orders totales: {len(all_purchase_orders)}")
        _logger.info(f"   • Purchase Orders activas: {len(active_purchase_orders)}")
        _logger.info(f"   • Purchase Orders canceladas: {len(all_purchase_orders) - len(active_purchase_orders)}")
        
        # Verificar mensaje de re-aprobación en chatter
        re_approval_messages = pr.message_ids.filtered(
            lambda m: "RE-APROBACIÓN DETECTADA" in (m.body or "")
        )
        self.assertTrue(re_approval_messages, "Debe haber mensaje de re-aprobación en chatter")
        _logger.info("   • Mensaje de re-aprobación en chatter ✅")
        
        # === CONCLUSIÓN ===
        _logger.info("\n🎉 CONCLUSIÓN: ESCENARIO PR00851 RESUELTO EXITOSAMENTE")
        _logger.info("   ✅ Re-aprobación permitida con Purchase Orders canceladas")
        _logger.info("   ✅ Nuevas Purchase Orders creadas correctamente")  
        _logger.info("   ✅ Mensaje informativo registrado en chatter")
        _logger.info("   ✅ Flujo de trabajo restaurado completamente")
        _logger.info("="*70)
        
        # Test siempre pasa - es documentativo
        self.assertTrue(True, "Escenario PR00851 completamente resuelto")