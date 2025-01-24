from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.tools import float_is_zero
from itertools import groupby

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

    # Accion de crear factura desde purchase en jobcostphasecat: Se agrega la condición para que no se cree la factura si la línea está oculta
    # 2025.01.23
    def action_create_invoice(self):
        """Create the invoice associated to the PO.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        sequence = 10
        for order in self:
            if order.invoice_status != 'to invoice':
                continue

            order = order.with_company(order.company_id)
            pending_section = None
            # Invoice values.
            invoice_vals = order._prepare_invoice()
            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                #Alconor: Se agrega la condición para que no se cree la factura si la línea está oculta
                if line.hide:
                    continue
                # 2025.01.23
                if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    if pending_section:
                        line_vals = pending_section._prepare_account_move_line()
                        line_vals.update({'sequence': sequence})
                        invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                        sequence += 1
                        pending_section = None
                    line_vals = line._prepare_account_move_line()
                    line_vals.update({'sequence': sequence})
                    invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                    sequence += 1
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

        # 2) group by (company_id, partner_id, currency_id) for batch creation
        new_invoice_vals_list = []
        for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
            origins = set()
            payment_refs = set()
            refs = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
                payment_refs.add(invoice_vals['payment_reference'])
                refs.add(invoice_vals['ref'])
            ref_invoice_vals.update({
                'ref': ', '.join(refs)[:2000],
                'invoice_origin': ', '.join(origins),
                'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()

        return self.action_view_invoice(moves)
    #######################################################################################################################
    # Accion de crear picking desde purchase en jobcostphasecat: Se agrega la condición para que no se cree el picking si la línea está oculta
    # 2025.01.23
    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self.filtered(lambda po: po.state in ('purchase', 'done')):
            if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
                order = order.with_company(order.company_id)
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                if not pickings:
                    res = order._prepare_picking()
                    picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                    pickings = picking
                else:
                    picking = pickings[0]
                moves = order.order_line.filtered(lambda line: not line.hide)._create_stock_moves(picking)
                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()
                # Get following pickings (created by push rules) to confirm them as well.
                forward_pickings = self.env['stock.picking']._get_impacted_pickings(moves)
                (pickings | forward_pickings).action_confirm()
                picking.message_post_with_view('mail.message_origin_link',
                    values={'self': picking, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return True
    #######################################################################################################################


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

    @api.onchange('account_analytic_id')
    def _onchange_account_analytic_id(self):
        if self.analytic_distribution:
            self.analytic_distribution = {str(self.account_analytic_id.id): 100.0}