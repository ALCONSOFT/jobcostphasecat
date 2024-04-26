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
