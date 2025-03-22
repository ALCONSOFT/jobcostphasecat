from odoo import models, fields, api

class PurchaseReportInherit(models.Model):
    _inherit = "purchase.report"

    # Campos nuevos
    analytic_account_id = fields.Many2one('account.analytic.account', string="Cuenta Analítica")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehículo")
    phase_id = fields.Many2one('project.task.phase', string="Fase")  

    def _select(self):
        select_str = super(PurchaseReportInherit, self)._select()
        select_str += """
            , l.account_analytic_id as analytic_account_id
            , l.vehicle_id as vehicle_id
            , l.phase_id as phase_id
        """
        return select_str

    def _from(self):
        from_str = super(PurchaseReportInherit, self)._from()
        from_str += """
            LEFT JOIN fleet_vehicle fv ON (l.vehicle_id = fv.id)
            LEFT JOIN project_task_phase pp ON (l.phase_id = pp.id)
        """
        return from_str

    def _group_by(self):
        group_by_str = super(PurchaseReportInherit, self)._group_by()
        group_by_str += """
            , l.account_analytic_id
            , l.vehicle_id
            , l.phase_id
        """
        return group_by_str