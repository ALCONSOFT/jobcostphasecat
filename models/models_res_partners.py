from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    internal_supplier = fields.Boolean(string='Proveedor Interno', default=False)
    internal_transfer_warehouse_id = fields.Many2one(
        'stock.warehouse', 
        string='Almacén de Transferencia Interna', 
        help='Almacén desde el cual se realizarán las transferencias internas para este proveedor.'
    )
