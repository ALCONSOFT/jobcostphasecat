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
            order.total_price_subtotal = sum(line.price_subtotal for line in order.order_line if not line.hide)

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

    # Calculo de totales tomando en cuen.hideta los llas lineas ocultas hide

    @api.depends('order_line.price_total', 'order_line.hide')
    def _amount_all(self):
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            order_lines = order_lines.filtered(lambda line: not line.hide)
            if order.company_id.tax_calculation_rounding_method == 'round_globally':
                tax_results = self.env['account.tax']._compute_taxes([
                    line._convert_to_tax_base_line_dict()
                    for line in order_lines
                ])
                totals = tax_results['totals']
                amount_untaxed = totals.get(order.currency_id, {}).get('amount_untaxed', 0.0)
                amount_tax = totals.get(order.currency_id, {}).get('amount_tax', 0.0)
            else:
                amount_untaxed = sum(order_lines.mapped('price_subtotal'))
                amount_tax = sum(order_lines.mapped('price_tax'))

            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_tax
            order.amount_total = order.amount_untaxed + order.amount_tax
        print("Amount Untaxed:", amount_untaxed)
        print("Amount Tax:", amount_tax)
        print("Amount Total:", order.amount_total)
        self._compute_tax_totals()

    @api.depends_context('lang')
    @api.depends('order_line.taxes_id', 'order_line.price_subtotal', 'amount_total', 'amount_untaxed')
    def _compute_tax_totals(self):
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type and not x.hide)
            order.tax_totals = self.env['account.tax']._prepare_tax_totals(
                [x._convert_to_tax_base_line_dict() for x in order_lines],
                order.currency_id or order.company_id.currency_id,
            )
        print("Tax Totals:", order.tax_totals)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    allow_qty_change_line = fields.Boolean(
        related='order_id.allow_qty_change',
        store=False
    )
    notes = fields.Text(string='Notes')
    hide = fields.Boolean(string='Hide in Report', default=False)
    discount = fields.Float(string="Discount (%)", digits="Discount")

    _sql_constraints = [
        (
            "discount_limit",
            "CHECK (discount <= 100.0)",
            "Discount must be lower than 100%.",
        )
    ]

    price_unit_discounted = fields.Monetary(
        compute='_compute_price_unit_discounted', 
        string='Initial Discounted Price'
    )

    @api.depends('price_unit', 'discount')
    def _compute_price_unit_discounted(self):
        for line in self:
            line.price_unit_discounted = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

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
    @api.onchange('hide')
    def _onchange_hide(self):
        if self.order_id:
            self.order_id._amount_all()