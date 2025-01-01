from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    total_price_total = fields.Monetary(compute='_compute_total_price_total', string='Total Price Total')

    @api.depends('order_line.price_total')
    def _compute_total_price_total(self):
        for order in self:
            order.total_price_total = sum(line.price_total for line in order.order_line)

    total_price_subtotal = fields.Monetary(compute='_compute_total_price_subtotal', string='Total Price SubTotal')

    @api.depends('order_line.price_subtotal')
    def _compute_total_price_subtotal(self):
        for order in self:
            order.total_price_subtotal = sum(line.price_subtotal for line in order.order_line)

    allow_qty_change = fields.Boolean(
        string='Permitir cambio de cantidades',
        compute='_compute_allow_qty_change',
        store=False
    )

    @api.depends('company_id')
    def _compute_allow_qty_change(self):
        param = self.env['ir.config_parameter'].sudo().get_param('jobcostphasecat.allow_qty_change', 'False')
        for record in self:
            record.allow_qty_change = param.lower() == 'true'

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    allow_qty_change_line = fields.Boolean(
        related='order_id.allow_qty_change',
        store=False
    )
    notes = fields.Text(string='Notes')

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        if not self.allow_qty_change_line:
            self.product_qty = self._origin.product_qty
            return {
                'warning': {
                    'title': 'Cantidad no permitida',
                    'message': 'No está permitido cambiar la cantidad de este producto.',
                }
            }
