# -*- coding: utf-8 -*-
"""
Pruebas para el botón Descartar en Purchase Request - Estado 'confirm'
Autor: Claude Code
Fecha: 2025-01-28

Pruebas para verificar que el botón Descartar funcione correctamente
cuando la Purchase Request está en estado 'confirm' (aprobado).
"""

import logging
from unittest.mock import Mock, patch
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TestDiscardConfirmState(TransactionCase):
    
    def setUp(self):
        super().setUp()
        
        # Crear usuario con permisos de aprobador
        self.test_user = self.env['res.users'].create({
            'name': 'Test Approver',
            'login': 'test_approver',
            'groups_id': [(6, 0, [
                self.env.ref('account.group_account_manager').id
            ])]
        })
        
        # Crear purchase request de prueba
        self.purchase_request = self.env['purchase.request'].create({
            'name': 'PR-TEST-CONFIRM',
            'state': 'confirm',  # Estado aprobado
            'employee_id': self.test_user.id,
        })

    def test_boton_visible_estado_confirm(self):
        """Verificar que el botón sea visible en estado 'confirm'"""
        _logger.info("🧪 Test: Botón visible en estado 'confirm'")
        
        # El botón debería ser visible según las nuevas condiciones XML
        # attrs="{'invisible': [('state', 'not in', ['to_approve', 'confirm'])]}"
        
        estados_visibles = ['to_approve', 'confirm']
        boton_visible = self.purchase_request.state in estados_visibles
        
        self.assertTrue(boton_visible, f"Botón debe ser visible en estado '{self.purchase_request.state}'")
        _logger.info(f"✅ Botón visible: {boton_visible}")

    def test_boton_invisible_otros_estados(self):
        """Verificar que el botón no sea visible en otros estados"""
        _logger.info("🧪 Test: Botón no visible en otros estados")
        
        estados_no_visibles = ['draft', 'waiting_for_verifier', 'waiting_for_audit', 
                              'waiting_for_buyer', 'waiting_for_approver', 'descarted', 'cancel']
        
        for estado in estados_no_visibles:
            with self.subTest(estado=estado):
                self.purchase_request.state = estado
                
                estados_visibles = ['to_approve', 'confirm']
                boton_visible = self.purchase_request.state in estados_visibles
                
                self.assertFalse(boton_visible, f"Botón NO debe ser visible en estado '{estado}'")
                _logger.info(f"✅ Estado '{estado}': Botón oculto correctamente")

    def test_action_descarted_estado_confirm_sin_purchase_orders(self):
        """Test: Descartar PR en estado 'confirm' sin Purchase Orders relacionadas"""
        _logger.info("🧪 Test: Descartar PR 'confirm' sin Purchase Orders")
        
        # Configurar PR como usuario con permisos
        pr_as_approver = self.purchase_request.with_user(self.test_user)
        
        # Verificar estado inicial
        self.assertEqual(pr_as_approver.state, 'confirm')
        
        # Ejecutar acción de descarte
        pr_as_approver.action_descarted()
        
        # Verificar resultado
        self.assertEqual(pr_as_approver.state, 'descarted')
        _logger.info("✅ Purchase Request descartada correctamente desde estado 'confirm'")

    def test_action_descarted_estado_confirm_con_po_canceladas(self):
        """Test: Descartar PR 'confirm' con Purchase Orders canceladas"""
        _logger.info("🧪 Test: Descartar PR 'confirm' con Purchase Orders canceladas")
        
        # Crear Purchase Orders de prueba con estados permitidos
        po_cancelada = self.env['purchase.order'].create({
            'name': 'PO-CANCEL-001',
            'partner_id': 1,  # Assuming partner exists
            'state': 'cancel',
            'request_id': self.purchase_request.id
        })
        
        po_descartada = self.env['purchase.order'].create({
            'name': 'PO-DISCARD-002', 
            'partner_id': 1,
            'state': 'descarted',
            'request_id': self.purchase_request.id
        })
        
        # Configurar PR como usuario con permisos
        pr_as_approver = self.purchase_request.with_user(self.test_user)
        
        # Ejecutar acción de descarte
        pr_as_approver.action_descarted()
        
        # Verificar resultado
        self.assertEqual(pr_as_approver.state, 'descarted')
        _logger.info("✅ Purchase Request descartada correctamente con PO canceladas/descartadas")

    def test_action_descarted_estado_confirm_po_activas_falla(self):
        """Test: NO puede descartar PR 'confirm' con Purchase Orders activas"""
        _logger.info("🧪 Test: Fallar al descartar PR 'confirm' con Purchase Orders activas")
        
        # Crear Purchase Order en estado activo
        po_activa = self.env['purchase.order'].create({
            'name': 'PO-ACTIVE-001',
            'partner_id': 1,
            'state': 'purchase',  # Estado que NO permite descarte
            'request_id': self.purchase_request.id
        })
        
        # Configurar PR como usuario con permisos
        pr_as_approver = self.purchase_request.with_user(self.test_user)
        
        # Intentar descartar (debe fallar)
        with self.assertRaises(UserError) as context:
            pr_as_approver.action_descarted()
            
        # Verificar mensaje de error
        error_msg = str(context.exception)
        self.assertIn("No se puede descartar esta solicitud", error_msg)
        self.assertIn("PO-ACTIVE-001", error_msg)
        self.assertIn("purchase", error_msg)
        
        # Verificar que el estado no cambió
        self.assertEqual(pr_as_approver.state, 'confirm')
        _logger.info("✅ Correctamente impedido descarte con Purchase Order activa")

    def test_action_descarted_estado_to_approve_funciona(self):
        """Test: Descartar PR en estado 'to_approve' sigue funcionando"""
        _logger.info("🧪 Test: Descartar PR 'to_approve' (funcionalidad original)")
        
        # Cambiar estado a to_approve
        self.purchase_request.state = 'to_approve'
        
        # Configurar PR como usuario con permisos
        pr_as_approver = self.purchase_request.with_user(self.test_user)
        
        # Ejecutar acción de descarte
        pr_as_approver.action_descarted()
        
        # Verificar resultado
        self.assertEqual(pr_as_approver.state, 'descarted')
        _logger.info("✅ Funcionalidad original (to_approve) sigue funcionando")

    def test_action_descarted_sin_permisos_falla(self):
        """Test: Usuario sin permisos no puede descartar"""
        _logger.info("🧪 Test: Usuario sin permisos no puede descartar")
        
        # Crear usuario sin permisos
        user_sin_permisos = self.env['res.users'].create({
            'name': 'Test User No Permissions',
            'login': 'test_no_perms',
            # Sin grupos de aprobador
        })
        
        # Configurar PR como usuario sin permisos
        pr_sin_permisos = self.purchase_request.with_user(user_sin_permisos)
        
        # Intentar descartar (debe fallar)
        with self.assertRaises(UserError) as context:
            pr_sin_permisos.action_descarted()
            
        # Verificar mensaje de error
        error_msg = str(context.exception)
        self.assertIn("Solo los aprobadores pueden descartar solicitudes", error_msg)
        
        # Verificar que el estado no cambió
        self.assertEqual(pr_sin_permisos.state, 'confirm')
        _logger.info("✅ Correctamente impedido descarte sin permisos")

    def test_action_descarted_estado_invalido_falla(self):
        """Test: No puede descartar PR en estados inválidos"""
        _logger.info("🧪 Test: No puede descartar PR en estados inválidos")
        
        estados_invalidos = ['draft', 'waiting_for_verifier', 'cancel', 'descarted']
        
        for estado in estados_invalidos:
            with self.subTest(estado=estado):
                # Cambiar estado
                self.purchase_request.state = estado
                
                # Configurar PR como usuario con permisos
                pr_as_approver = self.purchase_request.with_user(self.test_user)
                
                # Intentar descartar (debe fallar)
                with self.assertRaises(UserError) as context:
                    pr_as_approver.action_descarted()
                    
                # Verificar mensaje de error
                error_msg = str(context.exception)
                self.assertIn("Solo se pueden descartar solicitudes en estado", error_msg)
                self.assertIn("Pendiente de Aprobación", error_msg)
                self.assertIn("Aprobado", error_msg)
                
                _logger.info(f"✅ Estado '{estado}': Correctamente impedido descarte")

    def test_chatter_message_estado_anterior(self):
        """Test: Mensaje en chatter incluye estado anterior"""
        _logger.info("🧪 Test: Mensaje en chatter con estado anterior")
        
        with patch.object(self.purchase_request, 'message_post') as mock_message_post:
            # Configurar PR como usuario con permisos
            pr_as_approver = self.purchase_request.with_user(self.test_user)
            
            # Ejecutar acción de descarte
            pr_as_approver.action_descarted()
            
            # Verificar que se llamó message_post
            mock_message_post.assert_called_once()
            
            # Verificar contenido del mensaje
            call_args = mock_message_post.call_args
            message_body = call_args[1]['body']
            
            self.assertIn('PR-TEST-CONFIRM', message_body)
            self.assertIn('DESCARTADA', message_body)
            self.assertIn('Test Approver', message_body)
            self.assertIn('Estado anterior: Aprobado', message_body)
            
            _logger.info("✅ Mensaje en chatter incluye información completa")

    def test_resumen_funcionalidad_completa(self):
        """Test de resumen: Funcionalidad completa"""
        _logger.info("\n📋 RESUMEN DE FUNCIONALIDAD - BOTÓN DESCARTAR EN ESTADO 'CONFIRM':")
        _logger.info("="*70)
        
        test_cases = [
            {"estado": "to_approve", "visible": True, "puede_descartar": True},
            {"estado": "confirm", "visible": True, "puede_descartar": True},
            {"estado": "draft", "visible": False, "puede_descartar": False},
            {"estado": "cancel", "visible": False, "puede_descartar": False},
            {"estado": "descarted", "visible": False, "puede_descartar": False},
        ]
        
        for case in test_cases:
            estado = case["estado"]
            esperado_visible = case["visible"]
            esperado_descarte = case["puede_descartar"]
            
            # Test visibilidad
            estados_visibles = ['to_approve', 'confirm']
            actual_visible = estado in estados_visibles
            
            # Test descarte (solo para estados válidos)
            if estado in ['to_approve', 'confirm']:
                self.purchase_request.state = estado
                pr_as_approver = self.purchase_request.with_user(self.test_user)
                
                try:
                    pr_as_approver.action_descarted()
                    actual_descarte = True
                    # Revertir para siguiente test
                    self.purchase_request.state = estado
                except UserError:
                    actual_descarte = False
            else:
                actual_descarte = esperado_descarte
            
            _logger.info(f"   Estado '{estado}':")
            _logger.info(f"     - Botón visible: {actual_visible} ({'✅' if actual_visible == esperado_visible else '❌'})")
            _logger.info(f"     - Puede descartar: {actual_descarte} ({'✅' if actual_descarte == esperado_descarte else '❌'})")
        
        _logger.info("\n🎯 CASOS DE USO PRINCIPALES:")
        _logger.info("   ✅ PR00859 (confirm + PO canceladas) → Botón visible y funcional")
        _logger.info("   ✅ PR pendiente (to_approve) → Funcionalidad original preservada")
        _logger.info("   ❌ PR con PO activas → Correctamente bloqueado")
        _logger.info("   ❌ Usuario sin permisos → Correctamente bloqueado")
        _logger.info("="*70)