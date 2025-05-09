from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from itertools import groupby

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    total_price_total = fields.Monetary(compute='_compute_total_price_total', string='Total Price Total')

    def unlink(self):
        for record in self:
            if record.state != 'cancel':
                    raise UserError("No puedes eliminar este registro. Debes cancelarlo primero.**")
            else:
                raise   UserError("No puedes eliminar este registro. Consulte con su administrador.")
        return super(EthicsPurchaseRequest, self).unlink()
    
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
                        #line_vals.update({'sequence': sequence}) 2025.01.27
                        line_vals.update({'sequence': sequence, 'phase_id': line.phase_id.id})
                        invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                        sequence += 1
                        pending_section = None
                    line_vals = line._prepare_account_move_line()
                    #line_vals.update({'sequence': sequence}) 2025.01.27    Se agrega la fase a la factura
                    line_vals.update({'sequence': sequence,
                        'phase_id': line.phase_id.id,
                        'vehicle_id': line.vehicle_id.id})
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
    # Crear transferencia Interna desde purchase en jobcostphasecat:
    #   Se crea la accion de crear transferncia Itnerna desde la SdP
 
    internal_transfer = fields.Boolean(string='Transferencia Interna', default=False)

    @api.onchange('internal_transfer')
    def _onchange_internal_transfer(self):
        if self.internal_transfer:
            self.state = 'internal_transfer'
    
    def action_create_internal_transfer(self):
        if self.internal_transfer != True:
            raise UserError(_('La SdP debe estar marcada "Transferencia Interna" para crear una transferencia interna.'))
            
        StockPicking = self.env['stock.picking']
        for order in self:
            if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
                if not order.partner_id.internal_supplier:
                    raise UserError(_('The supplier must be marked as an internal supplier to create an internal transfer.'))
                order = order.with_company(order.company_id)
                picking_type = self.env.ref('stock.picking_type_internal')
                picking_vals = {
                    'picking_type_id': picking_type.id,
                    #'location_id': order.partner_id.property_stock_supplier.id,
                    'location_id': order.partner_id.internal_transfer_warehouse_id.lot_stock_id.id,
                    'location_dest_id': order.picking_type_id.default_location_dest_id.id,
                    'origin': order.name,
                    'company_id': order.company_id.id,
                    'move_type': 'direct',
                }
                picking = StockPicking.create(picking_vals)
                moves = order.order_line.filtered(lambda line: not line.hide)._create_stock_moves(picking)
                moves._action_confirm()
                picking.action_assign()
                picking.message_post_with_view('mail.message_origin_link',
                    values={'self': picking, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
        self.state = 'internal_transfer'
        return True
    #######################################################################################################################
    def action_create_double_internal_transfer(self):
        if not self.internal_transfer:
            raise UserError(_('La SdP debe estar marcada "Transferencia Interna" para crear una transferencia interna.'))

        StockPicking = self.env['stock.picking']
        StockLocation = self.env['stock.location']
        StockMove = self.env['stock.move']
        customers_location = StockLocation.search([('usage', '=', 'customer')], limit=1)

        if not customers_location:
            raise UserError(_('No se encontró una ubicación de cliente (Customers).'))

        for order in self:
            if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
                if not order.partner_id.internal_supplier:
                    raise UserError(_('El proveedor debe estar marcado como proveedor interno para crear una transferencia interna.'))

                order = order.with_company(order.company_id)
                # --- Salida ---
                picking_vals_out = {
                    'picking_type_id': order.partner_id.internal_transfer_warehouse_id.out_type_id.id,
                    'location_id': order.partner_id.internal_transfer_warehouse_id.lot_stock_id.id,
                    'location_dest_id': customers_location.id,
                    'origin': order.name,
                    'company_id': order.company_id.id,
                    'move_type': 'direct',
                    'partner_id': order.partner_id.id,
                }
                picking_out = StockPicking.create(picking_vals_out)
                moves_out = order.order_line.filtered(lambda l: not l.hide)._create_stock_moves(picking_out)

                # — Asignar cuenta analítica y distribución a cada movimiento de salida —
                for line in order.order_line.filtered(lambda l: not l.hide):
                    moves_line = moves_out.filtered(lambda m: m.product_id == line.product_id)
                    moves_line.write({
                        'account_analytic_id': line.account_analytic_id.id,
                        'analytic_distribution': line.analytic_distribution,
                    })

                moves_out._action_confirm()
                picking_out.action_assign()

                # — Transferencia de entrada (de Customers al almacén destino) —
                picking_vals_in = {
                    'picking_type_id': order.picking_type_id.id,
                    'location_id': customers_location.id,
                    'location_dest_id': order.picking_type_id.default_location_dest_id.id,
                    'origin': order.name,
                    'company_id': order.company_id.id,
                    'move_type': 'direct',
                    'partner_id': order.partner_id.id,
                }
                picking_in = StockPicking.create(picking_vals_in)

                # Crear movimientos de stock manualmente y asignar analítica
                for move_out in moves_out:
                    move_vals = {
                        'name': move_out.name,
                        'product_id': move_out.product_id.id,
                        'product_uom_qty': move_out.product_uom_qty,
                        'product_uom': move_out.product_uom.id,
                        'picking_id': picking_in.id,
                        'location_id': move_out.location_id.id,
                        'location_dest_id': move_out.location_dest_id.id,
                        'company_id': order.company_id.id,
                    }
                    new_move = StockMove.create(move_vals)
                    new_move.write({
                        'account_analytic_id': line.account_analytic_id.id,
                        'analytic_distribution': move_out.analytic_distribution,
                    })

                picking_in.move_ids._action_confirm()
                picking_in.action_assign()

                # Mensajes de seguimiento
                picking_out.message_post_with_view(
                    'mail.message_origin_link',
                    values={'self': picking_out, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
                picking_in.message_post_with_view(
                    'mail.message_origin_link',
                    values={'self': picking_in, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)

        # Actualizar el estado de la orden
        self.state = 'internal_transfer'
        # Añadir al histórico
        for order in self:
            order.picking_ids |= picking_out
            order.picking_ids |= picking_in

        return True
    #######################################################################################################################
    # recalcular los estados de las SdP para que se muestre el estado correcto en la vistas: camp invoice_status
        # 2025.01.26
    @api.depends('state', 'order_line.qty_to_invoice', 'order_line.hide', 'invoice_ids', 'write_date')
    def _get_invoiced(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for order in self:
            if order.state not in ('purchase', 'done'):
                order.invoice_status = 'no'
                continue

            # Filtrar solo líneas que no sean de visualización ni estén ocultas
            valid_lines = order.order_line.filtered(lambda l: not l.display_type and not l.hide)
            if any(
                not float_is_zero(line.qty_to_invoice, precision_digits=precision)
                for line in valid_lines
            ):
                order.invoice_status = 'to invoice'
            elif valid_lines and all(
                float_is_zero(line.qty_to_invoice, precision_digits=precision)
                for line in valid_lines
            ) and order.invoice_ids:
                order.invoice_status = 'invoiced'
            else:
                order.invoice_status = 'no'
    #######################################################################################################################
    # Agregar campo de historial de compras a la orden de compra    
    # 2025.02.26: Campo one2many para mostrar el historial
    purchase_history_ids = fields.One2many(
        comodel_name='purchase.order.line',
        inverse_name='order_id',
        string='Historial de Compras',
        compute='_compute_purchase_history',
        store=False
    )
    
    @api.depends('order_line.product_id')  # o los campos que quieras detonar
    def _compute_purchase_history(self):
        for order in self:
            # Aquí decides la lógica de filtrado que quieras aplicar:
            # Por ejemplo, mostrar TODAS las líneas de orden de compra
            # pasadas que tengan los mismos productos del pedido actual
            # y/o mismo proveedor.
            
            # Si quieres filtrar por el partner (el proveedor actual):
            partner_id = order.partner_id.id
            
            # Obtener todos los product_ids de este pedido
            product_ids = order.order_line.mapped('product_id').ids
            
            # Buscar líneas de compra con esos productos y ese partner
            # y que NO sean la orden de compra actual (por si no quieres duplicar).
            lines = self.env['purchase.order.line'].search([
                ('product_id', 'in', product_ids),
                ('order_id.partner_id', '=', partner_id),
                ('order_id', '!=', order.id),
                # si quieres excluir borradores, recibidas, etc. 
                # puedes añadir condiciones sobre ('order_id.state', '=', 'purchase'), etc.
            ])
            
            order.purchase_history_ids = lines

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    allow_qty_change_line = fields.Boolean(
        related='order_id.allow_qty_change',
        store=False
    )
    notes = fields.Text(string='Notes')
    hide = fields.Boolean(string='Hide in Report', default=False)
    discount = fields.Float(string="Discount (%)", digits="Discount")
    phase_id = fields.Many2one("project.phaseproject",
                               string="Fase",
                               tracking=True,
                               domain="[('account_analytic_id', '=', account_analytic_id)]")
    

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
        else:
            # Solo los usuarios miembros del grupo de Compras pueden modificar la cantidad en la SdP
            if not self.env.user.has_group('purchase.group_purchase_manager'):
                return {
                    'warning': {
                        'title': 'No permitido',
                        'message': 'Solo el grupo de Administradores en Compras puede modificar la cantidad en la SdP.',
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

    x_is_incomplete = fields.Boolean(
        string="Diferencia Cantidades",
        compute="_compute_is_incomplete",
        store=True,  # Opcional si deseas que sea un campo almacenado
    )

    @api.depends('product_qty', 'qty_received')
    def _compute_is_incomplete(self):
        for line in self:
            line.x_is_incomplete = (line.product_qty != line.qty_received)

    # 2025.02.26: Agregar campo partner_id para historial de compras a la orden de compra
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Proveedor (related)',
        related='order_id.partner_id',
        store=False,  # o True si deseas guardarlo
        readonly=True
    )
    # 2025.02.26: Agregar campo order_id para historial de compras a la orden de compra
    line_history_ids = fields.One2many(
        comodel_name='purchase.order.line',
        inverse_name='id',       # Sin inverse real; será un compute
        string='Historial de esta línea',
        compute='_compute_line_history_ids',
        store=False,
    )

    @api.depends('product_id', 'order_id.partner_id')
    def _compute_line_history_ids(self):
        for line in self:
            # Definir qué se considera “historial”.
            # Por ejemplo, líneas de compra con el mismo product_id y partner
            # en órdenes confirmadas o realizadas, excluyendo la línea actual.
            domain = [
                ('product_id', '=', line.product_id.id),
                ('order_id.partner_id', '=', line.order_id.partner_id.id),
                ('order_id.state', 'in', ['purchase','done']),  # si deseas sólo confirmadas o terminadas
                ('id', '!=', line.id),  # excluir la línea actual
            ]
            line.line_history_ids = self.env['purchase.order.line'].search(domain)
    # 2025.02.26: Agregar acción para ver historial de compras en la orden de compra por linea
    def action_view_line_history(self):
        """
        Retorna una acción (ventana) que muestra las líneas de compra
        que tengan el mismo producto y el mismo proveedor, 
        excluyendo la línea actual.
        """
        self.ensure_one()  # aseguramos que haya exactamente una línea
        domain = [
            ('product_id', '=', self.product_id.id),
            #('order_id.partner_id', '=', self.order_id.partner_id.id),
            ('id', '!=', self.id),
            # Opcional: si quieres sólo ver OCs en estado confirmado o hecho:
            ('order_id.state', 'in', ['purchase', 'done', 'descarted']),
        ]
        return {
            'name': 'Historial de Compras',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order.line',
            'view_mode': 'tree,form',
            'domain': domain,
            # target = 'current' abre la vista en la misma pestaña
            # target = 'new' la abre como pop-up
            'target': 'current',
        }
    # 2025.02.26: Agregar campo pr_ref_ids para historial de compras a la orden de compra
    pr_ref_ids = fields.Many2one(
        related='order_id.pr_ref_id',
        string='PR References',
        store=False,
        readonly=True
    )

    @api.depends('order_id.order_line.pr_ref_ids')
    def _compute_pr_ref_ids(self):
        for line in self:
            # si pr_ref_ids es un Many2many, por ejemplo:
            line.pr_ref_ids = [(6, 0, [line.order_id.pr_ref_id.id])]