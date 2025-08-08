# -*- coding: utf-8 -*-
"""
Test específico para investigar PR00859 - Botón Descartar no visible
Autor: Claude Code
Fecha: 2025-01-28
"""

import logging
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TestPR00859Debug(TransactionCase):
    
    def setUp(self):
        super().setUp()
        # Buscar la PR00859
        self.pr00859 = self.env['purchase.request'].search([('name', '=', 'PR00859')], limit=1)
        
    def test_pr00859_investigation(self):
        """Investigar el estado actual de PR00859 y por qué no aparece el botón Descartar"""
        
        if not self.pr00859:
            _logger.error("❌ PR00859 no encontrada en la base de datos")
            self.skipTest("PR00859 no encontrada")
            
        _logger.info(f"🔍 INVESTIGANDO PR00859:")
        _logger.info(f"   - ID: {self.pr00859.id}")
        _logger.info(f"   - Nombre: {self.pr00859.name}")
        _logger.info(f"   - Estado actual: '{self.pr00859.state}'")
        _logger.info(f"   - Employee: {self.pr00859.employee_id.name if self.pr00859.employee_id else 'No asignado'}")
        
        # Verificar Purchase Orders relacionadas
        related_pos = self.env['purchase.order'].search([('request_id', '=', self.pr00859.id)])
        _logger.info(f"   - Purchase Orders relacionadas: {len(related_pos)}")
        
        for i, po in enumerate(related_pos, 1):
            _logger.info(f"     {i}. PO: {po.name} - Estado: '{po.state}'")
            
        # Verificar condiciones del botón
        _logger.info(f"\n🔍 CONDICIONES DEL BOTÓN DESCARTAR:")
        
        # Condición 1: Estado debe ser 'to_approve'
        estado_correcto = self.pr00859.state == 'to_approve'
        _logger.info(f"   1. Estado == 'to_approve': {'✅' if estado_correcto else '❌'} (actual: '{self.pr00859.state}')")
        
        # Condición 2: Usuario debe tener permisos
        user = self.env.user
        tiene_permisos_account = user.has_group('account.group_account_manager')
        tiene_permisos_purchase = user.has_group('purchase.group_purchase_manager')
        tiene_permisos = tiene_permisos_account or tiene_permisos_purchase
        
        _logger.info(f"   2. Permisos del usuario '{user.name}':")
        _logger.info(f"      - account.group_account_manager: {'✅' if tiene_permisos_account else '❌'}")
        _logger.info(f"      - purchase.group_purchase_manager: {'✅' if tiene_permisos_purchase else '❌'}")
        _logger.info(f"      - Tiene permisos suficientes: {'✅' if tiene_permisos else '❌'}")
        
        # Condición 3: Purchase Orders no deben estar en estado bloqueado
        po_bloqueadas = []
        for po in related_pos:
            if po.state in ['locked', 'purchase']:
                po_bloqueadas.append(f"{po.name} ({po.state})")
                
        sin_po_bloqueadas = len(po_bloqueadas) == 0
        _logger.info(f"   3. Sin PO bloqueadas: {'✅' if sin_po_bloqueadas else '❌'}")
        if po_bloqueadas:
            _logger.info(f"      - PO bloqueadas: {', '.join(po_bloqueadas)}")
            
        # Resumen
        puede_descartar = estado_correcto and tiene_permisos and sin_po_bloqueadas
        _logger.info(f"\n📋 RESUMEN:")
        _logger.info(f"   - Puede ver botón Descartar: {'✅' if puede_descartar else '❌'}")
        
        if not puede_descartar:
            _logger.info(f"   - Razones por las que NO aparece:")
            if not estado_correcto:
                _logger.info(f"     ❌ Estado incorrecto: '{self.pr00859.state}' != 'to_approve'")
            if not tiene_permisos:
                _logger.info(f"     ❌ Sin permisos suficientes")
            if not sin_po_bloqueadas:
                _logger.info(f"     ❌ Hay Purchase Orders bloqueadas")
                
        # Verificar si puede ejecutar el método (simulación)
        if self.pr00859.state == 'to_approve':
            try:
                # Crear usuario con permisos para probar
                admin_user = self.env.ref('base.user_admin')
                pr_as_admin = self.pr00859.with_user(admin_user)
                
                _logger.info(f"\n🧪 PRUEBA DE SIMULACIÓN:")
                _logger.info(f"   - Probando método action_descarted() como admin...")
                
                # Solo validar, no ejecutar realmente
                related_pos_check = self.env['purchase.order'].search([('request_id', '=', self.pr00859.id)])
                bloqueadas_check = []
                for po in related_pos_check:
                    if po.state in ['locked', 'purchase']:
                        bloqueadas_check.append(po.name)
                        
                if bloqueadas_check:
                    _logger.info(f"   - ❌ Fallaría por PO bloqueadas: {', '.join(bloqueadas_check)}")
                else:
                    _logger.info(f"   - ✅ Podría ejecutarse correctamente")
                    
            except Exception as e:
                _logger.error(f"   - ❌ Error en simulación: {e}")
        
        # Assertions para el test
        self.assertTrue(self.pr00859, "PR00859 debe existir")
        
    def test_correct_states_mapping(self):
        """Verificar mapeo correcto de estados"""
        _logger.info(f"\n📋 MAPEO DE ESTADOS EN PURCHASE REQUEST:")
        
        # Estados posibles según el modelo
        estados_modelo = [
            'draft', 'waiting_for_verifier', 'waiting_for_audit', 
            'waiting_for_buyer', 'waiting_for_approver', 'to_approve', 
            'confirm', 'descarted', 'cancel'
        ]
        
        for estado in estados_modelo:
            _logger.info(f"   - '{estado}'")
            
        _logger.info(f"\n💡 IMPORTANTE:")
        _logger.info(f"   - El botón Descartar requiere estado: 'to_approve'")
        _logger.info(f"   - Si ves 'Confirmed' en la UI, verifica que sea 'to_approve' en BD")
        _logger.info(f"   - Estados similares: 'confirm' ≠ 'to_approve'")