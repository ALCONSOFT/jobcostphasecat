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
class JC_StockPicking(models.Model):
    _inherit = "stock.picking"

    full_analytic_account_id = fields.Many2one(
        string="Al Lote Completo", comodel_name="account.analytic.account", help="Se refiere a si todos los productos corresponden al mismo lote!"
    )
    actividades_id = fields.Many2one("account.analytic.line", string="Tareas", tracking=True)
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

    # Alconor: 23-mar-2022; crear una función que sustituya todos los lotes del detalle: (stock.move) por el lote del encabezado
    #          (stock.picking) full_account_analytic_id usando el decorador onchange [en cambio de:]
    # @api.onchange('full_analytic_account_id')
    # def _onchange_fanalytic(self):
    #     print('------------------------------ANALIZANDO-------------------------------------')
    #     print(self.id)
    #     modelo_detalle = self.env['stock.move'].search([('picking_id', '=', self.ids)])
    #     # Consultar si se ha asignado el lote en el modelo
    #     self.ids
    #     # Solo se puede usar este control si ya se guardo la transferencia nueva!
    #     # si origin es un entero enteonces se puede hacer el cambio de lote o proyecto!
    #     if not self.full_analytic_account_id:
    #         return
    #     else:
    #         # validar si ya es un documento guardado? y en modo Borrador
    #         if (not self.id.origin):
    #             return {'warning': {
    #                 'title': "Intenta cambiar el lote; pero no ha guardado aún!.",
    #                 'message': "Intenta cambiar el lote; pero no ha guardado aún!.  " +
    #                 "Si es una tranferencia nueva debe guardar primero y dejar en modo Borrador. "
    #                 "Para poder realizar cambio del lote o proyecto!!!",
    #             }
    #         }

    #             #res = { "type": "ir.actions.client", "tag": "reload" }
    #     alerta = {'warning': {
    #             'title': "Ha cambiado el Lote para todas las lineas del Documento.",
    #              'message': "Ha cambiado el Lote para todas las lineas del Documento.  " +
    #              "Haga click en botón: Refrescar Detalles ó "
    #              "Por favor guarde el Documento para ver los cambios y vuelva a Editar si desea realizar otros cambios!!!",
    #         }
    #     }
    #     #self.ver_detalles
    #     return alerta

        # 24-mar-2022; Como refrescar la vista formularios desde el modelo?
    # 23-mar-2022
    def ver_detalles(self):
        # Iniciar ciclo para cambiar lote linea por linea del Detalle
        modelo_detalle = self.env['stock.move'].search([('picking_id', '=', self.ids)])
        for record in modelo_detalle:
            print(record.analytic_account_id) 
            record.analytic_account_id = self.full_analytic_account_id
            print('Linea: ***************')
            print(record.analytic_account_id)

        #message = _('refrescando detalles  !!!')
        #raise UserError(message.lstrip())



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