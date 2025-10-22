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

    # Alconor: 10-oct-2025: Control de Stock Negativo Configurable
    def action_assign(self):
        """
        Override del método action_assign (Comprobar Disponibilidad) para controlar stock negativo.

        Este método se ejecuta ANTES de reservar stock, mostrando al usuario
        si hay problemas de disponibilidad ANTES de ingresar cantidades.

        Permite configurar:
        - Control habilitado/deshabilitado
        - Almacenes que PUEDEN tener stock negativo
        - Usuarios que PUEDEN hacer salidas sin restricción

        Solo valida en transferencias de SALIDA (outgoing).
        """
        # 1. Verificar si el control está habilitado
        control_enabled = self.env['ir.config_parameter'].sudo().get_param(
            'jobcostphasecat.enable_negative_stock_control',
            'False'
        ).lower() == 'true'

        # Si control deshabilitado → comportamiento Odoo estándar
        if not control_enabled:
            return super(ZZ_StockPicking, self).action_assign()

        # 2. Solo validar en transferencias de SALIDA
        if self.picking_type_id.code != 'outgoing':
            return super(ZZ_StockPicking, self).action_assign()

        # 3. Obtener configuración de almacenes y usuarios permitidos
        allowed_warehouse_ids = self.env['ir.config_parameter'].sudo().get_param(
            'jobcostphasecat.allowed_negative_stock_warehouse_ids',
            '[]'
        )
        allowed_user_ids = self.env['ir.config_parameter'].sudo().get_param(
            'jobcostphasecat.allowed_negative_stock_user_ids',
            '[]'
        )

        # Convertir strings a listas de IDs
        import ast
        try:
            allowed_warehouse_ids = ast.literal_eval(allowed_warehouse_ids) if allowed_warehouse_ids else []
            allowed_user_ids = ast.literal_eval(allowed_user_ids) if allowed_user_ids else []
        except:
            allowed_warehouse_ids = []
            allowed_user_ids = []

        # 4. Verificar EXCEPCIONES (almacén o usuario permitido)
        warehouse = self.picking_type_id.warehouse_id
        current_user = self.env.user

        # EXCEPCIÓN 1: El almacén está en la lista de permitidos
        if warehouse.id in allowed_warehouse_ids:
            return super(ZZ_StockPicking, self).action_assign()

        # EXCEPCIÓN 2: El usuario está en la lista de autorizados
        if current_user.id in allowed_user_ids:
            return super(ZZ_StockPicking, self).action_assign()

        # 5. VALIDAR STOCK - Solo si NO se cumplió ninguna excepción
        import logging
        _logger = logging.getLogger(__name__)

        for move in self.move_ids:
            if move.state in ('done', 'cancel'):
                continue

            # Validar la cantidad solicitada (product_uom_qty), no la hecha
            cantidad_solicitada = move.product_uom_qty
            if cantidad_solicitada <= 0:
                continue

            # Obtener información completa de stock
            # Buscamos todos los quants para este producto/ubicación
            quants = self.env['stock.quant'].search([
                ('product_id', '=', move.product_id.id),
                ('location_id', '=', move.location_id.id)
            ])

            # Calcular stock total físico en almacén
            stock_total = sum(quants.mapped('quantity'))

            # Calcular stock reservado SOLO de OTRAS transferencias (no la actual)
            # Buscamos move.lines con reservas excluyendo la transferencia actual
            otras_reservas = self.env['stock.move.line'].search([
                ('product_id', '=', move.product_id.id),
                ('location_id', '=', move.location_id.id),
                ('reserved_qty', '>', 0),
                ('state', 'not in', ['done', 'cancel']),
                ('picking_id', '!=', self.id)  # EXCLUIR la transferencia actual
            ])
            stock_reservado = sum(otras_reservas.mapped('reserved_qty'))  # Solo reservas de OTRAS transferencias

            # Stock disponible = Total - Reservas de OTRAS transferencias
            stock_disponible = stock_total - stock_reservado

            _logger.info("=== VALIDACION STOCK NEGATIVO (Comprobar Disponibilidad) ===")
            _logger.info("Producto: %s", move.product_id.display_name)
            _logger.info("Stock Total: %s", stock_total)
            _logger.info("Stock Reservado: %s", stock_reservado)
            _logger.info("Stock Disponible: %s", stock_disponible)
            _logger.info("Cantidad Solicitada: %s", cantidad_solicitada)
            _logger.info("Usuario: %s", self.env.user.name)
            _logger.info("Almacén: %s", warehouse.name if warehouse else 'N/A')

            # VALIDAR: Si intenta reservar más del stock DISPONIBLE → ERROR
            if cantidad_solicitada > stock_disponible:
                # Buscar información detallada de las reservas (ya calculadas en "otras_reservas")
                reservas_info = ""
                if stock_reservado > 0 and otras_reservas:
                    reservas_info = "\n\n" + "="*50 + "\n"
                    reservas_info += "DETALLE DE STOCK RESERVADO:\n"
                    reservas_info += "="*50 + "\n"

                    for line in otras_reservas:
                        picking_name = line.picking_id.name if line.picking_id else 'N/A'
                        picking_origin = line.picking_id.origin if line.picking_id and line.picking_id.origin else ''
                        state_name = dict(line.picking_id._fields['state'].selection).get(line.picking_id.state, line.picking_id.state)

                        reservas_info += "\n• Transferencia: %s" % picking_name
                        if picking_origin:
                            reservas_info += " (Origen: %s)" % picking_origin
                        reservas_info += "\n  Cantidad Reservada: %.2f %s" % (line.reserved_qty, move.product_uom.name)
                        reservas_info += "\n  Estado: %s" % state_name

                    reservas_info += "\n\n" + "-"*50
                    reservas_info += "\nPARA LIBERAR RESERVAS:"
                    reservas_info += "\n" + "-"*50
                    reservas_info += "\n1. Ir a la transferencia que tiene el stock reservado"
                    reservas_info += "\n2. Hacer clic en el boton 'Deshacer Reserva'"
                    reservas_info += "\n3. O cancelar la transferencia si ya no es necesaria"
                    reservas_info += "\n4. Luego podras comprobar disponibilidad nuevamente"

                error_msg = _(
                    'STOCK INSUFICIENTE\n\n'
                    'Producto: %s\n'
                    'Ubicación: %s\n\n'
                    'Stock Total:      %10.2f %s\n'
                    'Stock Reservado: -%10.2f %s\n'
                    '────────────────────────────────\n'
                    'Stock Disponible: %10.2f %s\n\n'
                    'Solicitado:       %10.2f %s\n'
                    'Faltante:         %10.2f %s'
                    '%s\n\n'
                    'NOTA: Solo almacenes y usuarios autorizados pueden hacer salidas con stock insuficiente.\n'
                    'Contacta al administrador si necesitas autorización.'
                ) % (
                    move.product_id.display_name,
                    move.location_id.complete_name,
                    stock_total,
                    move.product_uom.name,
                    stock_reservado,
                    move.product_uom.name,
                    stock_disponible,
                    move.product_uom.name,
                    cantidad_solicitada,
                    move.product_uom.name,
                    cantidad_solicitada - stock_disponible,
                    move.product_uom.name,
                    reservas_info,
                )
                _logger.error("=== BLOQUEANDO COMPROBAR DISPONIBILIDAD POR STOCK INSUFICIENTE ===")
                _logger.error("Disponible: %s | Solicitado: %s", stock_disponible, cantidad_solicitada)
                if otras_reservas:
                    _logger.error("Reservas de OTRAS transferencias: %d", len(otras_reservas))
                    for line in otras_reservas:
                        _logger.error("  - %s: %.2f unidades", line.picking_id.name, line.reserved_qty)
                raise UserError(error_msg)

        # 6. Si todo está OK, continuar con la reserva de stock normal
        return super(ZZ_StockPicking, self).action_assign()

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