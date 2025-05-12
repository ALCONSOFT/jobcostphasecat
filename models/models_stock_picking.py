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

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        from datetime import datetime
        # Verificar si en configuracion de compras se permite duplicar transferencias en esytado solo plantillas
        allow_transfer_duplication = self.env['ir.config_parameter'].sudo().get_param('jobcostphasecat.allow_transfer_duplication', default=False)
        if not allow_transfer_duplication:
            # Si el campo allow_transfer_duplication es falso, se coopia normalmente
            pass
        else:
            # Si el campo allow_transfer_duplication es verdadero, se permite la duplicación de transferencias
            # en estado plantilla
            default = dict(default or {})

            # 1) Detectar devolución: si se cambió el picking_type al tipo de devolución
            return_type = self.picking_type_id.return_picking_type_id.id
            new_type = default.get('picking_type_id')
            is_return = new_type == return_type or default.get('move_type') == 'return'

            if is_return:
                # --- Lógica de devolución ---
                # (aquí podrías aplicar reglas especiales para devoluciones)
                return super().copy(default=default)

            if self.picking_type_id.code == 'outgoing':
                # Verifica si el estado no es 'plantilla'
                if self.state != 'plantilla':
                    from odoo.exceptions import ValidationError, UserError
                    raise UserError(_('Sólo se permite duplicar transferencias de Salidas desde estado Plantilla!.'))
                else:
                    # Define los valores predeterminados para los campos al duplicar
                    print("{ - - - - - - - Estoy en copy [Duplicando] - - - - - - - }")
                    default = dict(default or {})
                    default.update({
                        'export': False,  # Reinicia el campo booleano 'export'
                        'export_datetime': False,  # Reinicia el campo datetime 'export_datetime'
                        'export_user_id': False,  # Reinicia el campo Many2one 'export_user_id'
                        'export_url': False,  # Reinicia el campo Char o Text 'export_url'
                        'close': False,  # Reinicia el campo booleano 'close'
                        'close_datetime': False,  # Reinicia el campo datetime 'close_datetime'
                        'full_analytic_account_id': False,
                        'origin': False
                    })
                    # Llama al método copy original de la clase padre
                    res = super(JC_StockPicking, self).copy(default=default)
                    # Inicializa el campo analytic_account_id en todos los registros relacionados de stock.move
                    for move in res.move_ids_without_package:
                        move.account_analytic_id = False
                    # Copia el valor de full_analytic_account_id en cada una de las líneas del modelo stock.move
                    self.ver_detalles()
                    # Activa la bitácora inicial porque el flujo de copiar un registro de transferencia es diferente
                    valor_default = True
                    self._escribir_bitacora_inicia(self.env.user.name, valor_default, datetime.now())
            else:
                # Si el tipo de picking no es 'outgoing', llama al método copy original de la clase padre
                res = super(JC_StockPicking, self).copy(default=default)
                # Inicializa el campo analytic_account_id en todos los registros relacionados de stock.move
                for move in res.move_ids_without_package:
                    move.account_analytic_id = False
                # Copia el valor de full_analytic_account_id en cada una de las líneas del modelo stock.move
                self.ver_detalles()
                # Activa la bitácora inicial porque el flujo de copiar un registro de transferencia es diferente
                valor_default = True
                self._escribir_bitacora_inicia(self.env.user.name, valor_default, datetime.now())
            return res

            # Si el tipo de picking no es 'outgoing', llama al método copy original de la clase padre
        return super(JC_StockPicking, self).copy(default=default)
        # En este código, al duplicar el registro, los campos especificados se inicializan a un valor predeterminado
        # (en la mayoría de los casos, simplemente se reinician). Asumí algunos tipos de datos para los campos en base a sus nombres,
        # así que ajusta según sea necesario.
        # PENDIENTE: campo suma de verificación: esto es para saber si la fila o el registro del encabezado de
        # la transferencia ha cambiado y por lo tanto se debe actualizar
        ############################################################################################################

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