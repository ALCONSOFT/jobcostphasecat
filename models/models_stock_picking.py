# utf-8
# Alconsoft 2021 Alejandro Concepción
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from datetime import date, time
from email.policy import default
#from tkinter import N
from odoo import api, fields, models, _, tools
##
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError, UserError, ValidationError, ValidationError, Warning, RedirectWarning
from odoo.tools.misc import formatLang, get_lang
#"Alconor: En construccion; 15-ene-2022"
class ZZ_StockPicking(models.Model):
    _inherit = "stock.picking"

    full_analytic_account_id = fields.Many2one(
        string="Al Lote Completo", comodel_name="account.analytic.account", help="Se refiere a si todos los productos corresponden al mismo lote!"
    )
    actividades_id = fields.Many2one("account.analytic.line", string="Tareas", tracking=True)
    # alconor: 23-dic-2024
    # vehicle_id = fields.Many2one(
    #     'fleet.vehicle', 
    #     string='Vehículo',
    #     tracking=True,
    #     help="Vehículo asignado para esta transferencia"
    # )

    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=True, default=lambda self: self.env.ref('stock.picking_type_out').id
    )
    location_id = fields.Many2one(
        'stock.location', 'Source Location',
        required=True, default=lambda self: self.env.ref('stock.stock_location_stock').id
    )
    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location',
        required=True, default=lambda self: self.env.ref('stock.stock_location_customers').id
    )

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        if self.picking_type_id:
            self.location_id = self.picking_type_id.default_location_src_id.id
            self.location_dest_id = self.picking_type_id.default_location_dest_id.id
            self.full_analytic_account_id = self.picking_type_id.warehouse_id.account_analytic_id.id

    # ------------------------------
    def action_confirm_jc(self):
        # Llamar al metodo: self.action_confirm() del modelo: stock.picking
        self.env['stock.picking'].action_confirm()
        print('Entrando a funcion: [action_confirm_jc]')
        # llamar fecha maxima de closed_date
        ld_fecha_maxima = self.env['stock.picking.closed'].browse(1).closed_date
        ld_fecha_prevista = self.scheduled_date
        if  ld_fecha_prevista < ld_fecha_maxima:
            message = _('Esta transferencia no se puede Realizar porque la fecha de cierre es: %s \nFecha prevista es: %s') % (ld_fecha_maxima.strftime("%d-%b-%Y (%H:%M:%S.%f)"), (ld_fecha_prevista.strftime("%d-%b-%Y (%H:%M:%S.%f)")))
            raise UserError(message.lstrip())
        else:
            return
    # Alconor: 30-mar-2022; validacion de control lote: full_analytic_account_id
    @api.constrains('full_analytic_accoount_id')
    def _check_fanalytic(self):
        if (not self.id.origin):
            return {'warning': {
                'title': "Intenta cambiar el lote; pero no ha guardado aún!.",
                'message': "Intenta cambiar el lote; pero no ha guardado aún!.  " +
                "Si es una tranferencia nueva debe guardar primero y dejar en modo Borrador. "
                "Para poder realizar cambio del lote o proyecto!!!",
            }
        }
        else:
            print('Validando en Full_analytic_accoount_id')
            return

 
    # 23-mar-2022
    def ver_detalles(self):
        # Iniciar ciclo para cambiar lote linea por linea del Detalle
        modelo_detalle = self.env['stock.move'].search([('picking_id', '=', self.ids)])
        for record in modelo_detalle:
            print(record.account_analytic_id) 
            record.account_analytic_id = self.full_analytic_account_id
            print('Linea: ***************')
            print(record.account_analytic_id)
            record.analytic_distribution = {str(self.full_analytic_account_id.id): 100.0}

        #message = _('refrescando detalles  !!!')
        #raise UserError(message.lstrip())
    ## Alconor: 2-may-2025: se movio del modulo: (ac_sync_odoo_odoo) a este modulo: jobcostphasecat
    # 2023-10-31,1,2,3.....
    @api.model
    def boton_convertir_a_plantilla(self, vals):
        from datetime import datetime
        # Solo las transferencias en estado = borrador [draft] se pueden convertir a plantilla
        registro_tranf = self.env['stock.picking'].browse(vals)
        if registro_tranf.state != 'draft':
            from odoo.exceptions import ValidationError, UserError
            raise UserError(_('Sólo se permite convertir las transferecnias en estado borrador a Plantilla!.'))
        else:
            registro_tranf.write({'state': 'plantilla'})
            self._escribir_bitacora_fin(self.env.user.name, False, datetime.now())
        return True
    # 2023-11-12: Fin

    # NOTA: El método copy() ahora está en models_stock_picking_override.py
    # para tener prioridad sobre ac_sync_odoo_odoo

class JC_closed_date_transference(models.Model):
    _name = 'stock.picking.closed'

    name = fields.Char('Fecha Cierre de Transacciones', default="Cerradas las transferencias al dia: ")
    closed_date = fields.Datetime(
        'Fecha Cerrada!', store=True,
        help="Fechas cerradas que no permiten validar transferencias!")

class JC_mensaje(models.Model):
    _name = 'stock.mensaje'

    name = fields.Char('Titulo', default='Alerta!!!')
    descripcion = fields.Char('Descripción', default='Cuidado!.  Haga click para continuar!')