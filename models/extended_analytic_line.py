from odoo import api, fields, models

class ExtendedAccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    vehicle_id = fields.Many2one(
        'fleet.vehicle', 
        string='Vehículo-1ext',
        compute='_compute_vehicle_id',
        store=True
    )
    phase_id = fields.Many2one("project.phaseproject",
                               string="Fase",
                               tracking=True,
                               domain="[('account_analytic_id', '=', account_analytic_id)]")


    @api.depends('account_id')
    def _compute_vehicle_id(self):
        for line in self:
            #stock_move = self.env['stock.move'].search([('analytic_account_line_id', '=', line.id)], limit=1)
            #line.vehicle_id = stock_move.vehicle_id if stock_move else False
            line.vehicle_id = line.move_line_id.move_id.stock_move_id.vehicle_id if line.move_line_id.move_id.stock_move_id.vehicle_id else False
            print(
                'line.vehicle_id:', line.vehicle_id,
            )
