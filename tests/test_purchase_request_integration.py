# -*- coding: utf-8 -*-

"""
PRUEBAS DE INTEGRACIÓN para Purchase Request
Prueban interacciones entre múltiples componentes y el chatter
"""

from odoo.tests.common import TransactionCase
from unittest.mock import patch


class TestPurchaseRequestIntegration(TransactionCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Crear datos de prueba más completos
        cls.warehouse_1 = cls.env['stock.warehouse'].create({
            'name': 'MUPA - PUERTO',
            'code': 'MUPA',
        })
        
        cls.warehouse_2 = cls.env['stock.warehouse'].create({
            'name': 'Z de Importaciones',
            'code': 'ZIMP',
        })
        
        cls.picking_type_1 = cls.env['stock.picking.type'].create({
            'name': 'Recepciones MUPA',
            'code': 'incoming',
            'warehouse_id': cls.warehouse_1.id,
            'sequence_code': 'IN',
        })
        
        cls.picking_type_2 = cls.env['stock.picking.type'].create({
            'name': 'Recepciones Z Importaciones',
            'code': 'incoming',
            'warehouse_id': cls.warehouse_2.id,
            'sequence_code': 'IN',
        })
        
        cls.analytic_1 = cls.env['account.analytic.account'].create({
            'name': 'Proyecto ABC-2024',
        })
        
        cls.analytic_2 = cls.env['account.analytic.account'].create({
            'name': 'Proyecto DEF-2025',
        })
        
        # Crear usuario de prueba
        cls.test_user = cls.env['res.users'].create({
            'name': 'Usuario Prueba',
            'login': 'test_user',
            'email': 'test@example.com',
        })

    def test_warehouse_change_updates_picking_type(self):
        """
        PRUEBA DE INTEGRACIÓN: Cambiar warehouse debe actualizar picking_type_id correctamente
        """
        # Arrange: crear purchase request con warehouse inicial
        pr = self.env['purchase.request'].create({
            'name': 'TEST-INTEGRATION-001',
            'warehouse_id': self.warehouse_1.id,
            'picking_type_id': self.picking_type_1.id,
        })
        
        # Act: cambiar warehouse usando onchange
        pr.warehouse_id = self.warehouse_2.id
        pr._onchange_warehouse()
        
        # Assert: picking_type_id debe actualizarse al del nuevo warehouse
        self.assertEqual(pr.picking_type_id.warehouse_id, self.warehouse_2,
                        "picking_type_id debe actualizarse al nuevo warehouse")

    def test_picking_type_change_creates_chatter_message(self):
        """
        PRUEBA DE INTEGRACIÓN: Cambio de picking_type_id debe crear mensaje en chatter
        """
        # Arrange: crear purchase request
        pr = self.env['purchase.request'].create({
            'name': 'TEST-CHATTER-001',
            'warehouse_id': self.warehouse_1.id,
            'picking_type_id': self.picking_type_1.id,
        })
        
        # Limpiar mensajes existentes para la prueba
        initial_message_count = len(pr.message_ids)
        
        # Act: cambiar picking_type_id usando write
        pr.with_user(self.test_user).write({
            'picking_type_id': self.picking_type_2.id
        })
        
        # Assert: debe haberse creado un mensaje en el chatter
        new_message_count = len(pr.message_ids)
        self.assertGreater(new_message_count, initial_message_count,
                          "Debe crearse un mensaje en el chatter")
        
        # Verificar contenido del mensaje
        latest_message = pr.message_ids[0]  # Los mensajes se ordenan por fecha desc
        self.assertIn('Tipo de Operación Modificado', latest_message.body,
                     "El mensaje debe mencionar el cambio de tipo de operación")
        self.assertIn('MUPA', latest_message.body,
                     "El mensaje debe mencionar el warehouse anterior")
        self.assertIn('Z de Importaciones', latest_message.body,
                     "El mensaje debe mencionar el nuevo warehouse")

    def test_analytic_account_change_creates_chatter_message(self):
        """
        PRUEBA DE INTEGRACIÓN: Cambio de cuenta analítica debe crear mensaje en chatter
        """
        # Arrange: crear purchase request
        pr = self.env['purchase.request'].create({
            'name': 'TEST-ANALYTIC-001',
            'warehouse_id': self.warehouse_1.id,
            'account_analytic_id': self.analytic_1.id,
        })
        
        initial_message_count = len(pr.message_ids)
        
        # Act: cambiar cuenta analítica
        pr.with_user(self.test_user).write({
            'account_analytic_id': self.analytic_2.id
        })
        
        # Assert: debe haberse creado un mensaje
        new_message_count = len(pr.message_ids)
        self.assertGreater(new_message_count, initial_message_count,
                          "Debe crearse un mensaje en el chatter")
        
        # Verificar contenido
        latest_message = pr.message_ids[0]
        self.assertIn('Cuenta Analítica Modificada', latest_message.body,
                     "El mensaje debe mencionar el cambio de cuenta analítica")
        self.assertIn('ABC-2024', latest_message.body,
                     "El mensaje debe mencionar la cuenta anterior")
        self.assertIn('DEF-2025', latest_message.body,
                     "El mensaje debe mencionar la nueva cuenta")

    def test_multiple_changes_create_combined_message(self):
        """
        PRUEBA DE INTEGRACIÓN: Múltiples cambios simultáneos deben crear mensaje combinado
        """
        # Arrange: crear purchase request
        pr = self.env['purchase.request'].create({
            'name': 'TEST-MULTI-001',
            'warehouse_id': self.warehouse_1.id,
            'picking_type_id': self.picking_type_1.id,
            'account_analytic_id': self.analytic_1.id,
        })
        
        initial_message_count = len(pr.message_ids)
        
        # Act: cambiar ambos campos simultáneamente
        pr.with_user(self.test_user).write({
            'picking_type_id': self.picking_type_2.id,
            'account_analytic_id': self.analytic_2.id,
        })
        
        # Assert: debe haberse creado UN mensaje con ambos cambios
        new_message_count = len(pr.message_ids)
        self.assertEqual(new_message_count, initial_message_count + 1,
                        "Debe crearse exactamente un mensaje para ambos cambios")
        
        # Verificar que el mensaje contiene ambos cambios
        latest_message = pr.message_ids[0]
        self.assertIn('Tipo de Operación Modificado', latest_message.body,
                     "Debe incluir cambio de tipo de operación")
        self.assertIn('Cuenta Analítica Modificada', latest_message.body,
                     "Debe incluir cambio de cuenta analítica")

    def test_onchange_validation_prevents_invalid_picking_type(self):
        """
        PRUEBA DE INTEGRACIÓN: Validación onchange debe prevenir tipos inválidos
        """
        # Arrange: crear purchase request
        pr = self.env['purchase.request'].create({
            'name': 'TEST-VALIDATION-001',
            'warehouse_id': self.warehouse_1.id,
            'picking_type_id': self.picking_type_1.id,
        })
        
        # Act: intentar asignar picking_type incompatible
        pr.picking_type_id = self.picking_type_2.id  # Este pertenece a warehouse_2
        result = pr._onchange_picking_type_id()
        
        # Assert: debe retornar warning
        self.assertIsInstance(result, dict, "Debe retornar diccionario de warning")
        self.assertIn('warning', result, "Debe contener clave 'warning'")
        self.assertIn('Tipo de Operación Incompatible', result['warning']['title'],
                     "Debe mostrar mensaje de incompatibilidad")

    def test_create_rfq_ethics_with_protection(self):
        """
        PRUEBA DE INTEGRACIÓN: create_rfq_ethics debe funcionar con protección
        """
        # Arrange: crear PR completo con líneas
        product = self.env['product.product'].create({
            'name': 'Producto Test Integration',
            'type': 'product',
        })
        
        vendor = self.env['res.partner'].create({
            'name': 'Proveedor Integration',
            'is_company': True,
            'supplier_rank': 1,
        })
        
        pr = self.env['purchase.request'].create({
            'name': 'TEST-RFQ-001',
            'warehouse_id': self.warehouse_1.id,
            'picking_type_id': self.picking_type_1.id,
            'account_analytic_id': self.analytic_1.id,
        })
        
        self.env['purchase.request.line'].create({
            'request_id': pr.id,
            'product_id': product.id,
            'name': 'Línea Integration Test',
            'product_qty': 5.0,
            'product_uom': product.uom_po_id.id,
            'vendor_ids': [(6, 0, [vendor.id])],
        })
        
        # Act: ejecutar create_rfq_ethics
        pr.create_rfq_ethics()
        
        # Assert: debe crear PO con picking_type correcto
        created_pos = self.env['purchase.order'].search([('pr_ref_id', '=', pr.id)])
        self.assertTrue(created_pos, "Debe crear al menos una Purchase Order")
        
        for po in created_pos:
            self.assertEqual(po.picking_type_id, pr.picking_type_id,
                           "PO debe heredar el picking_type_id correcto")
            self.assertEqual(po.account_analytic_id, pr.account_analytic_id,
                           "PO debe heredar la cuenta analítica correcta")

    @patch('odoo.addons.jobcostphasecat.models.models_ethics_purchase_request._logger')
    def test_logging_integration(self, mock_logger):
        """
        PRUEBA DE INTEGRACIÓN: Verificar que logging funciona en flujo completo
        """
        # Arrange: crear PR
        pr = self.env['purchase.request'].create({
            'name': 'TEST-LOGGING-001',
            'warehouse_id': self.warehouse_1.id,
            'picking_type_id': self.picking_type_1.id,
        })
        
        # Act: cambiar picking_type_id
        pr.write({'picking_type_id': self.picking_type_2.id})
        
        # Assert: verificar que se llamó al logger
        mock_logger.info.assert_called()