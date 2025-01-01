from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_qty_change = fields.Boolean(
        string='Permitir Modificar Cantidades en SdP',
        config_parameter='jobcostphasecat.allow_qty_change',
        default=False,
        help='Si está habilitado, permite modificar cantidades en las Solicitudes de Presupuesto'
    )