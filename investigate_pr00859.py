#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para investigar PR00859 - Por qué no aparece el botón Descartar
Ejecutar desde dentro del contenedor Odoo
"""

def investigate_pr00859():
    """Investigar PR00859"""
    try:
        import odoo
        from odoo import api, SUPERUSER_ID
        import logging
        
        _logger = logging.getLogger(__name__)
        
        print("🔍 INVESTIGANDO PR00859 - Botón Descartar no visible")
        print("=" * 60)
        
        # Conectar a la base de datos
        db_name = 'db030'
        
        with api.Environment.manage():
            with odoo.registry(db_name).cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                
                # Buscar PR00859
                pr = env['purchase.request'].search([('name', '=', 'PR00859')], limit=1)
                
                if not pr:
                    print("❌ PR00859 no encontrada en la base de datos")
                    return
                    
                print(f"✅ PR00859 encontrada!")
                print(f"   - ID: {pr.id}")
                print(f"   - Nombre: {pr.name}")
                print(f"   - Estado actual: '{pr.state}'")
                print(f"   - Employee: {pr.employee_id.name if pr.employee_id else 'No asignado'}")
                
                # Verificar Purchase Orders relacionadas
                related_pos = env['purchase.order'].search([('request_id', '=', pr.id)])
                print(f"   - Purchase Orders relacionadas: {len(related_pos)}")
                
                for i, po in enumerate(related_pos, 1):
                    print(f"     {i}. PO: {po.name} - Estado: '{po.state}'")
                    
                print(f"\n🔍 ANÁLISIS DE CONDICIONES DEL BOTÓN DESCARTAR:")
                
                # Condición 1: Estado debe ser 'to_approve'
                estado_correcto = pr.state == 'to_approve'
                print(f"   1. Estado == 'to_approve': {'✅' if estado_correcto else '❌'}")
                print(f"      - Estado actual: '{pr.state}'")
                print(f"      - Requerido: 'to_approve'")
                
                # Condición 2: Verificar si hay PO bloqueadas
                po_bloqueadas = []
                for po in related_pos:
                    if po.state in ['locked', 'purchase']:
                        po_bloqueadas.append(f"{po.name} ({po.state})")
                        
                sin_po_bloqueadas = len(po_bloqueadas) == 0
                print(f"   2. Sin PO bloqueadas: {'✅' if sin_po_bloqueadas else '❌'}")
                if po_bloqueadas:
                    print(f"      - PO bloqueadas: {', '.join(po_bloqueadas)}")
                else:
                    print(f"      - Todas las PO están en estados permitidos")
                    
                # Resumen
                puede_mostrar_boton = estado_correcto
                print(f"\n📋 DIAGNÓSTICO:")
                print(f"   - Puede mostrar botón: {'✅' if puede_mostrar_boton else '❌'}")
                
                if not puede_mostrar_boton:
                    print(f"   - ❌ PROBLEMA IDENTIFICADO:")
                    if not estado_correcto:
                        print(f"      Estado incorrecto: '{pr.state}' != 'to_approve'")
                        
                        # Sugerir estados posibles
                        print(f"\n💡 POSIBLES SOLUCIONES:")
                        print(f"   1. Verificar en la UI que el estado mostrado sea realmente 'to_approve'")
                        print(f"   2. Los estados en Odoo pueden ser:")
                        estados = ['draft', 'waiting_for_verifier', 'waiting_for_audit', 
                                 'waiting_for_buyer', 'waiting_for_approver', 'to_approve', 
                                 'confirm', 'descarted', 'cancel']
                        for estado in estados:
                            print(f"      - '{estado}'" + (" ← REQUERIDO PARA BOTÓN" if estado == 'to_approve' else ''))
                            
                        print(f"\n   3. Si la UI muestra 'Confirmed', puede ser estado 'confirm' (≠ 'to_approve')")
                        
                else:
                    print(f"   - ✅ Todas las condiciones están correctas")
                    print(f"   - El botón debería aparecer para usuarios con permisos:")
                    print(f"     • account.group_account_manager")
                    print(f"     • purchase.group_purchase_manager")
                    
                # Verificar método puede ejecutarse
                if estado_correcto and sin_po_bloqueadas:
                    print(f"\n🧪 SIMULACIÓN DE EJECUCIÓN:")
                    try:
                        # Solo verificar validaciones, no ejecutar
                        if pr.state != 'to_approve':
                            print(f"   - ❌ Fallaría: Estado incorrecto")
                        elif po_bloqueadas:
                            print(f"   - ❌ Fallaría: PO bloqueadas")
                        else:
                            print(f"   - ✅ Se ejecutaría correctamente")
                    except Exception as e:
                        print(f"   - ❌ Error en simulación: {e}")
                        
    except Exception as e:
        print(f"❌ Error durante investigación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    investigate_pr00859()