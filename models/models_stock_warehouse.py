# -*- coding: utf-8 -*-
from odoo import fields, models, api

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    account_analytic_id = fields.Many2one(
        'account.analytic.account', 
        string='Analytic Account',
        help="This is the default analytic account for this warehouse."
    )

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """You can extend the onchange to automatically set an analytic account, if necessary."""
        super()._onchange_company_id()
        if self.company_id:
            # Example: Automatically link a default analytic account based on the company
            default_account = self.env['account.analytic.account'].search([
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            self.account_analytic_id = default_account

    # def write(self, vals):
    #     """Optional: Validate or trigger specific actions when account_analytic_id changes."""
    #     res = super().write(vals)
    #     if 'account_analytic_id' in vals:
    #         # Add any custom behavior when the analytic account changes
    #         for warehouse in self:
    #             # Example: Log a message or trigger an update elsewhere
    #             self.env['mail.message'].create({
    #                 'body': f"Analytic account for warehouse {warehouse.name} updated.",
    #                 'model': self._name,
    #                 'res_id': warehouse.id,
    #             })
    #     return res
