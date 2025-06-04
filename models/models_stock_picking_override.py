# -*- coding: utf-8 -*-
# Alconsoft 2025 - Override para método copy() de stock.picking
# Este archivo se carga al FINAL para tener prioridad sobre ac_sync_odoo_odoo
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPickingFinalOverride(models.Model):
    """
    Clase final que se carga después de ac_sync_odoo_odoo para 
    garantizar que nuestro método copy() tenga prioridad
    """
    _inherit = "stock.picking"
    _order = "id desc"  # Forzar orden de herencia

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """
        Método copy() con prioridad final sobre ac_sync_odoo_odoo
        """
        # Verificar si en configuracion de compras se permite duplicar transferencias en estado solo plantillas
        allow_transfer_duplication = self.env['ir.config_parameter'].sudo().get_param(
            'jobcostphasecat.allow_transfer_duplication', default=False)
        
        if not allow_transfer_duplication:
            # Si el campo allow_transfer_duplication es falso, se copia normalmente
            return super().copy(default=default)
        
        # Si el campo allow_transfer_duplication es verdadero, aplicar lógica personalizada
        default = dict(default or {})

        # 1) Detectar devolución
        return_type = self.picking_type_id.return_picking_type_id.id if self.picking_type_id.return_picking_type_id else False
        new_type = default.get('picking_type_id')
        is_return = new_type == return_type or default.get('move_type') == 'return'

        if is_return:
            # Lógica de devolución normal
            return super().copy(default=default)

        if self.picking_type_id.code == 'outgoing':
            # Verifica si el estado no es 'plantilla'
            if self.state != 'plantilla':
                raise UserError(_('Sólo se permite duplicar transferencias de Salidas desde estado Plantilla!.'))
            else:
                # Define los valores predeterminados para los campos al duplicar
                default.update({
                    'export': False,
                    'export_datetime': False,
                    'export_user_id': False,
                    'export_url': False,
                    'close': False,
                    'close_datetime': False,
                    'full_analytic_account_id': False,
                    'origin': False
                })
                
                # Llama al método copy original de la clase padre
                res = super().copy(default=default)
                
                # Inicializa el campo analytic_account_id en todos los registros relacionados de stock.move
                for move in res.move_ids_without_package:
                    move.account_analytic_id = False
                
                # Copia el valor de full_analytic_account_id en cada una de las líneas
                if hasattr(self, 'ver_detalles'):
                    self.ver_detalles()
                
                # Activa la bitácora inicial
                if hasattr(self, '_escribir_bitacora_inicia'):
                    self._escribir_bitacora_inicia(self.env.user.name, True, datetime.now())
                
                return res
        else:
            # Si el tipo de picking no es 'outgoing'
            res = super().copy(default=default)
            
            # Inicializa el campo analytic_account_id en todos los registros relacionados de stock.move
            for move in res.move_ids_without_package:
                move.account_analytic_id = False
            
            # Copia el valor de full_analytic_account_id en cada una de las líneas
            if hasattr(self, 'ver_detalles'):
                self.ver_detalles()
            
            # Activa la bitácora inicial
            if hasattr(self, '_escribir_bitacora_inicia'):
                self._escribir_bitacora_inicia(self.env.user.name, True, datetime.now())
            
            return res

        # Fallback normal
        return super().copy(default=default) 