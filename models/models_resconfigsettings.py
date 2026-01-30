from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_qty_change = fields.Boolean(
        string='Permitir Modificar Cantidades en SdP',
        config_parameter='jobcostphasecat.allow_qty_change',
        default=False,
        help='Si está habilitado, permite modificar cantidades en las Solicitudes de Presupuesto'
    )

    require_phase_id = fields.Boolean(
        string='Requerir Phase ID en Solicitudes de Compra',
        config_parameter='jobcostphasecat.require_phase_id',
        default=False,
        help='Si está habilitado, se requiere capturar el Phase ID en las Solicitudes de Compra'
    )
    
    require_phase_id_out_transfer = fields.Boolean(
        string='Requerir Phase ID en Transferencias de Salidas de Inventario',
        config_parameter='jobcostphasecat.require_phase_id_out_transfer',
        default=False,
        help='Si está habilitado, se requiere capturar el Phase ID en las Transferencias de Salidas de Inventario'
    )

    allow_transfer_duplication = fields.Boolean(
        string='Permitir Duplicado de Transferencias solo Plantilla',
        config_parameter='jobcostphasecat.allow_transfer_duplication',
        default=False,
        help='Si está habilitado, permite duplicar transferencias estado plantilla en el sistema'
    )

    # 2026-01-30: Restricción de cambio de tipo de operación
    restrict_picking_type_change = fields.Boolean(
        string='Restringir Cambio de Tipo de Operación',
        config_parameter='jobcostphasecat.restrict_picking_type_change',
        default=False,
        help='Si está habilitado, solo usuarios con el permiso "Cambiar Tipo de Operación en Compras" '
             'pueden modificar el campo Tipo de Operación (Entregar a) en las órdenes de compra.'
    )

    # Usuarios autorizados para cambiar tipo de operación (vinculado al grupo)
    picking_type_change_user_ids = fields.Many2many(
        'res.users',
        string='Usuarios Autorizados',
        compute='_compute_picking_type_change_users',
        inverse='_inverse_picking_type_change_users',
        help='Usuarios que pueden cambiar el Tipo de Operación en órdenes de compra.'
    )

    @api.depends('restrict_picking_type_change')
    def _compute_picking_type_change_users(self):
        group = self.env.ref('jobcostphasecat.group_change_picking_type', raise_if_not_found=False)
        for record in self:
            if group:
                record.picking_type_change_user_ids = group.users
            else:
                record.picking_type_change_user_ids = False

    def _inverse_picking_type_change_users(self):
        group = self.env.ref('jobcostphasecat.group_change_picking_type', raise_if_not_found=False)
        if group:
            group.users = [(6, 0, self.picking_type_change_user_ids.ids)]

    # Control de Stock Negativo
    enable_negative_stock_control = fields.Boolean(
        string='Controlar Stock Negativo en Salidas',
        config_parameter='jobcostphasecat.enable_negative_stock_control',
        default=False,
        help='Si está habilitado, controla que solo almacenes y usuarios autorizados puedan hacer salidas con stock insuficiente'
    )

    allowed_negative_stock_warehouse_ids = fields.Many2many(
        'stock.warehouse',
        string='Almacenes con Stock Negativo Permitido',
        help='Almacenes que PUEDEN tener stock negativo. Las salidas en estos almacenes NO serán bloqueadas por falta de stock.'
    )

    allowed_negative_stock_user_ids = fields.Many2many(
        'res.users',
        string='Usuarios Autorizados para Salidas sin Stock',
        help='Usuarios que PUEDEN hacer salidas aunque no haya existencias. Estos usuarios NO recibirán error de validación.'
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()

        # Recuperar IDs de almacenes permitidos
        warehouse_ids_str = ICPSudo.get_param('jobcostphasecat.allowed_negative_stock_warehouse_ids', '')
        if warehouse_ids_str:
            warehouse_ids = [int(x) for x in warehouse_ids_str.split(',') if x.strip().isdigit()]
            res['allowed_negative_stock_warehouse_ids'] = [(6, 0, warehouse_ids)]

        # Recuperar IDs de usuarios permitidos
        user_ids_str = ICPSudo.get_param('jobcostphasecat.allowed_negative_stock_user_ids', '')
        if user_ids_str:
            user_ids = [int(x) for x in user_ids_str.split(',') if x.strip().isdigit()]
            res['allowed_negative_stock_user_ids'] = [(6, 0, user_ids)]

        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()

        # Guardar IDs de almacenes permitidos
        warehouse_ids = ','.join(str(x) for x in self.allowed_negative_stock_warehouse_ids.ids)
        ICPSudo.set_param('jobcostphasecat.allowed_negative_stock_warehouse_ids', warehouse_ids)

        # Guardar IDs de usuarios permitidos
        user_ids = ','.join(str(x) for x in self.allowed_negative_stock_user_ids.ids)
        ICPSudo.set_param('jobcostphasecat.allowed_negative_stock_user_ids', user_ids)