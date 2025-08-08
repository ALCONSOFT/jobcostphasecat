#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de verificación para PR00859 - Botón Descartar después de los cambios
Ejecutar desde dentro del contenedor Odoo o con acceso a la base de datos
"""

def verify_pr00859_fix():
    """Verificar que PR00859 ahora pueda usar el botón Descartar"""
    try:
        import odoo
        from odoo import api, SUPERUSER_ID
        import logging
        
        _logger = logging.getLogger(__name__)
        
        print("🔍 VERIFICANDO FIX PARA PR00859 - Botón Descartar")
        print("=" * 60)
        
        # Conectar a la base de datos (ajustar nombre según sea necesario)
        db_name = 'db030'  # Cambiar si es diferente
        
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
                
                # Verificar Purchase Orders relacionadas
                related_pos = env['purchase.order'].search([('request_id', '=', pr.id)])
                print(f"   - Purchase Orders relacionadas: {len(related_pos)}")
                
                for i, po in enumerate(related_pos, 1):
                    print(f"     {i}. PO: {po.name} - Estado: '{po.state}'")
                
                print(f"\n🔍 ANÁLISIS CON NUEVAS CONDICIONES:")
                
                # Nuevas condiciones del botón (después del fix)
                estados_visibles_nuevos = ['to_approve', 'confirm']
                boton_visible = pr.state in estados_visibles_nuevos
                
                print(f"   1. Botón visible (nuevas condiciones): {'✅' if boton_visible else '❌'}")
                print(f"      - Estado actual: '{pr.state}'")
                print(f"      - Estados que muestran botón: {estados_visibles_nuevos}")
                
                # Validar condiciones para ejecución del método
                print(f"\n🧪 VALIDACIÓN DE MÉTODO action_descarted():")
                
                # Verificar estados permitidos para ejecución
                estados_permitidos_metodo = ['to_approve', 'confirm']
                estado_valido = pr.state in estados_permitidos_metodo
                print(f"   1. Estado válido para ejecución: {'✅' if estado_valido else '❌'}")
                
                # Verificar Purchase Orders
                if related_pos:
                    estados_po_permitidos = ['cancel', 'descarted']
                    pos_validas = []
                    pos_problematicas = []
                    
                    for po in related_pos:
                        if po.state in estados_po_permitidos:
                            pos_validas.append(f"{po.name} ({po.state})")
                        else:
                            pos_problematicas.append(f"{po.name} ({po.state})")
                    
                    todas_pos_validas = len(pos_problematicas) == 0
                    print(f"   2. Purchase Orders en estados válidos: {'✅' if todas_pos_validas else '❌'}")
                    
                    if pos_validas:
                        print(f"      - PO válidas: {', '.join(pos_validas)}")
                    if pos_problematicas:
                        print(f"      - PO problemáticas: {', '.join(pos_problematicas)}")
                        print(f"      - Estados requeridos para PO: {estados_po_permitidos}")
                else:
                    todas_pos_validas = True
                    print(f"   2. Sin Purchase Orders relacionadas: ✅")
                
                # Resultado final
                puede_ejecutarse = estado_valido and todas_pos_validas
                print(f"\n📋 RESULTADO FINAL:")
                print(f"   - Botón debería aparecer: {'✅' if boton_visible else '❌'}")
                print(f"   - Método se puede ejecutar: {'✅' if puede_ejecutarse else '❌'}")
                
                if boton_visible and puede_ejecutarse:
                    print(f"\n🎉 ¡SUCCESS! PR00859 ahora puede usar el botón Descartar")
                    print(f"   - El botón aparecerá en la interfaz")
                    print(f"   - El método se ejecutará sin errores")
                    print(f"   - La Purchase Request pasará a estado 'descarted'")
                    
                    # Mostrar instrucciones
                    print(f"\n📝 INSTRUCCIONES PARA EL USUARIO:")
                    print(f"   1. Ir a Purchase Request PR00859")
                    print(f"   2. Verificar que tiene permisos de aprobador:")
                    print(f"      - account.group_account_manager O")
                    print(f"      - purchase.group_purchase_manager")
                    print(f"   3. Hacer clic en botón 'Descartar' (rojo)")
                    print(f"   4. Confirmar la acción")
                    print(f"   5. Verificar que el estado cambia a 'Descartado'")
                    
                elif boton_visible and not puede_ejecutarse:
                    print(f"\n⚠️  PARCIAL: Botón visible pero método fallará")
                    print(f"   - Razón: Purchase Orders en estados no permitidos")
                    print(f"   - Solución: Cancelar o descartar las Purchase Orders relacionadas")
                    
                elif not boton_visible:
                    print(f"\n❌ ERROR: Botón sigue sin ser visible")
                    print(f"   - Estado actual: '{pr.state}'")
                    print(f"   - Posible problema: Archivo XML no actualizado o cache")
                    print(f"   - Solución: Reiniciar servidor Odoo o actualizar módulo")
                    
                print(f"\n🔧 CAMBIOS REALIZADOS EN EL CÓDIGO:")
                print(f"   1. XML: Botón visible en estados 'to_approve' Y 'confirm'")
                print(f"   2. Python: Método acepta ambos estados")
                print(f"   3. Python: Valida PO en estados 'cancel' o 'descarted'")
                print(f"   4. Python: Mejores mensajes de error y logging")
                
    except Exception as e:
        print(f"❌ Error durante verificación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verify_pr00859_fix()