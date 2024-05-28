from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    anglo_saxon_accounting = fields.Boolean(string='Anglo Saxon Accounting', default=True)
