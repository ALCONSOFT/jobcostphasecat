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