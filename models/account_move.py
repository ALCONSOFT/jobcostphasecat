from odoo import models, fields

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    phase_id = fields.Many2one(
        "project.phaseproject",
        string="Fase",
        tracking=True
    )
