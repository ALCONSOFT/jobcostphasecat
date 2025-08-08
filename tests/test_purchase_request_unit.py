# -*- coding: utf-8 -*-

"""
PRUEBAS UNITARIAS para Purchase Request
Prueban métodos individuales de forma aislada
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from unittest.mock import patch


class TestPurchaseRequestUnit(TransactionCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Crear datos de prueba
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Almacén Test',
            'code': 'TEST',
        })
        
        cls.picking_type = cls.env['stock.picking.type'].create({
            'name': 'Recepciones Test',
            'code': 'incoming',
            'warehouse_id': cls.warehouse.id,
            'sequence_code': 'IN',
        })
        
        cls.analytic_account = cls.env['account.analytic.account'].create({
            'name': 'Proyecto Test',
        })
        
        cls.purchase_request = cls.env['purchase.request'].create({
            'name': 'TEST-001',
            'warehouse_id': cls.warehouse.id,
            'picking_type_id': cls.picking_type.id,
            'account_analytic_id': cls.analytic_account.id,
        })

    def test_validate_picking_type_valid(self):
        """
        PRUEBA UNITARIA: _validate_picking_type() con datos válidos
        """
        # Arrange: datos válidos ya están en self.purchase_request
        
        # Act: ejecutar validación
        result = self.purchase_request._validate_picking_type()
        
        # Assert: debe retornar True
        self.assertTrue(result, "Validación debe ser exitosa con datos válidos")

    def test_validate_picking_type_invalid_warehouse(self):
        """
        PRUEBA UNITARIA: _validate_picking_type() con warehouse incorrecto
        """
        # Arrange: crear warehouse diferente
        other_warehouse = self.env['stock.warehouse'].create({
            'name': 'Otro Almacén',
            'code': 'OTHER',
        })
        
        # Modificar picking_type para que apunte a otro warehouse
        self.purchase_request.picking_type_id.warehouse_id = other_warehouse.id
        
        # Act: ejecutar validación
        result = self.purchase_request._validate_picking_type()
        
        # Assert: debe retornar False
        self.assertFalse(result, "Validación debe fallar con warehouse incorrecto")

    def test_validate_picking_type_wrong_code(self):
        """
        PRUEBA UNITARIA: _validate_picking_type() con código incorrecto
        """
        # Arrange: cambiar código a outgoing
        self.purchase_request.picking_type_id.code = 'outgoing'
        
        # Act: ejecutar validación
        result = self.purchase_request._validate_picking_type()
        
        # Assert: debe retornar False
        self.assertFalse(result, "Validación debe fallar con código incorrecto")

    def test_get_picking_type_for_warehouse_success(self):
        """
        PRUEBA UNITARIA: _get_picking_type_for_warehouse() encuentra tipo correcto
        """
        # Act: buscar picking type para warehouse
        result = self.purchase_request._get_picking_type_for_warehouse(self.warehouse)
        
        # Assert: debe encontrar el picking type correcto
        self.assertEqual(result, self.picking_type, 
                        "Debe encontrar el picking type correcto para el warehouse")

    def test_get_picking_type_for_warehouse_none(self):
        """
        PRUEBA UNITARIA: _get_picking_type_for_warehouse() con warehouse None
        """
        # Act: buscar picking type para None
        result = self.purchase_request._get_picking_type_for_warehouse(None)
        
        # Assert: debe retornar None
        self.assertIsNone(result, "Debe retornar None cuando warehouse es None")

    def test_create_rfq_ethics_validation_success(self):
        """
        PRUEBA UNITARIA: create_rfq_ethics() pasa validación correctamente
        """
        # Arrange: agregar línea de producto para que create_rfq_ethics funcione
        product = self.env['product.product'].create({
            'name': 'Producto Test',
            'type': 'product',
        })
        
        vendor = self.env['res.partner'].create({
            'name': 'Proveedor Test',
            'is_company': True,
            'supplier_rank': 1,
        })
        
        self.env['purchase.request.line'].create({
            'request_id': self.purchase_request.id,
            'product_id': product.id,
            'name': 'Línea Test',
            'product_qty': 1.0,
            'product_uom': product.uom_po_id.id,
            'vendor_ids': [(6, 0, [vendor.id])],
        })
        
        # Act & Assert: no debe lanzar excepción
        try:
            self.purchase_request.create_rfq_ethics()
            success = True
        except (ValidationError, UserError):
            success = False
        
        self.assertTrue(success, "create_rfq_ethics debe ejecutarse sin errores con datos válidos")

    @patch('odoo.addons.jobcostphasecat.models.models_ethics_purchase_request._logger')
    def test_logging_in_validate_picking_type(self, mock_logger):
        """
        PRUEBA UNITARIA: Verificar que el logging funciona correctamente
        """
        # Arrange: configurar datos inválidos
        self.purchase_request.picking_type_id.code = 'outgoing'
        
        # Act: ejecutar validación
        self.purchase_request._validate_picking_type()
        
        # Assert: verificar que se llamó al logger
        mock_logger.warning.assert_called()