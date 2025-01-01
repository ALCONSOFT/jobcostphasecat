from odoo import models, api

class PurchaseRequestReport(models.AbstractModel):
    _name = 'report.jobcostphasecat.report_purchase_request_document'
    _description = 'Purchase Request Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['purchase.request'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'purchase.request',
            'docs': docs,
        }
