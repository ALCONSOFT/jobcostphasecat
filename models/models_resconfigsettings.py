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

    # Control de Stock Negativo
    enable_negative_stock_control = fields.Boolean(
        string='Controlar Stock Negativo en Salidas',
        config_parameter='jobcostphasecat.enable_negative_stock_control',
        default=False,
        help='Si está habilitado, controla que solo almacenes y usuarios autorizados puedan hacer salidas con stock insuficiente'
    )

    allowed_negative_stock_warehouse_ids = fields.Many2many(
        'stock.warehouse',
        'config_warehouse_negative_stock_rel',
        'config_id', 'warehouse_id',
        string='Almacenes con Stock Negativo Permitido',
        help='Almacenes que PUEDEN tener stock negativo. Las salidas en estos almacenes NO serán bloqueadas por falta de stock.'
    )

    allowed_negative_stock_user_ids = fields.Many2many(
        'res.users',
        'config_user_negative_stock_rel',
        'config_id', 'user_id',
        string='Usuarios Autorizados para Salidas sin Stock',
        help='Usuarios que PUEDEN hacer salidas aunque no haya existencias. Estos usuarios NO recibirán error de validación.'
    )