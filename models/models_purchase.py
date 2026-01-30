from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from itertools import groupby

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # 2026-01-30: Validar que el tipo de operación sea recepción, no devolución
    @api.constrains('picking_type_id')
    def _check_picking_type_is_reception(self):
        """
        Asegurar que las órdenes de compra usen tipos de operación de Recepción,
        no de Devolución. Los tipos de recepción tienen return_picking_type_id definido.
        """
        for order in self:
            if order.picking_type_id and order.picking_type_id.code == 'incoming':
                # Si el tipo NO tiene return_picking_type_id, es una devolución
                if not order.picking_type_id.return_picking_type_id:
                    # Obtener el tipo de recepción correcto del almacén
                    warehouse = order.picking_type_id.warehouse_id
                    correct_type = warehouse.in_type_id if warehouse else False
                    raise UserError(_(
                        '¡TIPO DE OPERACIÓN INCORRECTO!\n\n'
                        'La orden de compra %(order)s tiene asignado el tipo "%(wrong_type)s" '
                        'que está destinado para DEVOLUCIONES de clientes, no para recepciones de compra.\n\n'
                        'Por favor seleccione el tipo de operación correcto: "%(correct_type)s"',
                        order=order.name,
                        wrong_type=order.picking_type_id.name,
                        correct_type=correct_type.name if correct_type else 'Recepciones del almacén'
                    ))

    # Agregando estado: "cerrado "al campo: invoice_status (estado de facturación)
    invoice_status = fields.Selection([
        ('no', 'Nothing to Bill'),
        ('to invoice', 'Waiting Bills'),
        ('invoiced', 'Fully Billed'),
        ('done', 'Cerrado'),
    ],
        string='Estado de Facturación',
        compute='_get_invoiced',
        store=True,
        readonly=False,
        tracking=True,
        copy=False, default='no')
    
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
    subtotal_without_discount = fields.Monetary(
        string='Subtotal sin descuento',
        store=True
        # tracking=True  # Removido: no trackear campos computados (evita spam)
    )

    @api.depends('company_id')
    def _compute_allow_qty_change(self):
        param = self.env['ir.config_parameter'].sudo().get_param('jobcostphasecat.allow_qty_change', 'False')
        for record in self:
            record.allow_qty_change = param.lower() == 'true'

    # Global Discount Fields
    global_discount_type = fields.Selection(
        [
            ('percentage', 'Porcentaje Global'),
            ('fixed', 'Fijo Global'),
            ('percentage_line', 'Porcentaje por Línea'),
            ('fixed_line', 'Fijo por Línea')
        ],
        string='Tipo Descuento Global',
        default='percentage',
        tracking=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'to approve': [('readonly', False)], 'purchase': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )
    global_discount_percentage = fields.Float(
        string='Descuento Global (%)',
        digits='Discount', # Standard Odoo precision for discounts
        default=0.0,
        tracking=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'to approve': [('readonly', False)], 'purchase': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )
    global_discount_fixed_amount = fields.Monetary(
        string='Descuento Global Fijo',
        default=0.0,
        tracking=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'to approve': [('readonly', False)], 'purchase': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )
    total_discount = fields.Monetary(
        string='Total Descuento',
        compute='_compute_total_discount',
        store=True
        # tracking=True  # Removido: no trackear campos computados (evita spam)
    )
    

    _sql_constraints = [
        ('global_discount_percentage_limit', 'CHECK(global_discount_percentage >= 0.0 AND global_discount_percentage <= 100.0)', 'Global discount percentage must be between 0 and 100%.'),
        ('global_discount_fixed_amount_positive', 'CHECK(global_discount_fixed_amount >= 0.0)', 'Global discount fixed amount must be positive.'),
    ]

    # Calculo de totales tomando en cuen.hideta los llas lineas ocultas hide

    @api.depends('order_line.price_total',
        'order_line.price_subtotal',
        'order_line.hide',
        'global_discount_type',
        'global_discount_percentage',
        'global_discount_fixed_amount')
    def _amount_all(self):
        # 2025.05.30: Se calcula el descuento global
        self._compute_global_discount()
        # 2025.06.06: Calcular Sub-Total sin descuento
        self.subtotal_without_discount = self._compute_subtotal_without_discount()
        # 2025.05.30: Se recalcula los totales de la orden de compra
        self.total_discount = self._compute_total_discount()
        # Se recalcula los totales de la orden de compra
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type and not x.hide)

            if not order_lines:
                # Deshabilitar tracking para evitar spam en bitácora (recálculo automático)
                order.with_context(tracking_disable=True).write({
                    'amount_untaxed': 0.0,
                    'amount_tax': 0.0,
                    'amount_total': 0.0
                })
            else:
                # FIX 2025-11-08: Evitar doble aplicación de descuento global
                # Para tipos 'percentage' y 'fixed', el descuento ya fue aplicado en las líneas
                # por _compute_global_discount(), por lo que NO debe aplicarse aquí nuevamente.
                # Solo se aplicaría un descuento adicional para tipos que no distribuyen a las líneas.

                effective_global_discount_rate = 0.0

                # NO aplicar descuento a nivel de orden para tipos 'percentage' y 'fixed'
                # porque ya está aplicado en las líneas por _compute_global_discount()
                # Los tipos 'percentage_line' y 'fixed_line' se manejan directamente en las líneas
                # por el usuario, sin distribución automática, así que tampoco necesitan descuento aquí.

                # En resumen: effective_global_discount_rate siempre será 0.0
                # El descuento real ya está reflejado en line.price_subtotal de cada línea

                new_tax_base_lines = []
                # en _amount_all, después de construir new_tax_base_lines
                if new_tax_base_lines:
                    # 🔸  Asegura que todos los taxes usados en las líneas existen y están flushados
                    self.env.cr.flush()

                    tax_results = self.env['account.tax']._compute_taxes(new_tax_base_lines)

                for line in order_lines:
                    line_dict = line._convert_to_tax_base_line_dict()
                    # FIX 2025-11-08: NO aplicar descuento global aquí
                    # El price_unit en line_dict ya refleja el descuento de línea
                    # que fue aplicado en _compute_global_discount() para tipos 'percentage' y 'fixed'
                    # Por lo tanto, NO multiplicamos por (1 - effective_global_discount_rate)
                    # line_dict['price_unit'] ya es el precio correcto con descuento incluido
                    new_tax_base_lines.append(line_dict)

                if not new_tax_base_lines: # Should not happen if order_lines was not empty, but as a safeguard
                    # Deshabilitar tracking para evitar spam en bitácora (recálculo automático)
                    order.with_context(tracking_disable=True).write({
                        'amount_untaxed': 0.0,
                        'amount_tax': 0.0,
                        'amount_total': 0.0
                    })
                else:
                    tax_results = self.env['account.tax']._compute_taxes(new_tax_base_lines)
                    totals = tax_results['totals']

                    # The amount_untaxed from tax_results is now the sum of line subtotals *after* global discount
                    amount_untaxed = totals.get(order.currency_id, {}).get('amount_untaxed', 0.0)
                    amount_tax = totals.get(order.currency_id, {}).get('amount_tax', 0.0)

                    # Deshabilitar tracking para evitar spam en bitácora (recálculo automático)
                    order.with_context(tracking_disable=True).write({
                        'amount_untaxed': amount_untaxed,
                        'amount_tax': amount_tax,
                        'amount_total': amount_untaxed + amount_tax
                    })
            
            # The print statements might be for debugging and can be kept or removed based on final requirements.
            # For now, I'll assume they should reflect the final computed values.
            print("Amount Untaxed:", order.amount_untaxed)
            print("Amount Tax:", order.amount_tax)
            print("Amount Total:", order.amount_total)
            self._compute_tax_totals()

    def _compute_global_discount(self):
        # 2025.05.30: Se agrega el calculo de los totales tomando en cuenta los descuentos globales
        # Distribuir el descuento global a cada linea segun el peso de la linea en el total de la factura
        for order in self:
            if not order.order_line:
                continue
                
            # Calcular el monto total de la factura sin descuento (subtotal base)
            subtotal = sum(line.product_qty * line.price_unit for line in order.order_line if not line.hide)
            
            if subtotal == 0:
                continue
                
            if order.global_discount_type == 'fixed':
                # Descuento global fijo: distribuir proporcionalmente según el peso de cada línea
                for line in order.order_line:
                    if line.hide:
                        continue
                        
                    line_subtotal = line.product_qty * line.price_unit
                    peso = line_subtotal / subtotal if subtotal > 0 else 0
                    descuento_linea_total = order.global_discount_fixed_amount * peso
                    
                    # El descuento fijo por unidad
                    line_discount_fixed_per_unit = descuento_linea_total / line.product_qty if line.product_qty > 0 else 0
                    
                    # Calcular el porcentaje equivalente
                    line_discount_percentage = (line_discount_fixed_per_unit / line.price_unit * 100) if line.price_unit > 0 else 0
                    
                    # Solo escribir el tipo y los valores base - el campo computado calculará discount_fixed_amount
                    # Deshabilitar tracking para evitar spam en bitácora (cambios automáticos)
                    line.with_context(tracking_disable=True).write({
                        'discount_type': 'fixed',
                        'discount': line_discount_percentage
                    })
                    
            elif order.global_discount_type == 'percentage':
                # Descuento global porcentual: aplicar el mismo porcentaje a todas las líneas
                for line in order.order_line:
                    if line.hide:
                        continue
                        
                    # Solo escribir el tipo y porcentaje - el campo computado calculará discount_fixed_amount
                    # Deshabilitar tracking para evitar spam en bitácora (cambios automáticos)
                    line.with_context(tracking_disable=True).write({
                        'discount_type': 'percentage',
                        'discount': order.global_discount_percentage
                    })
                    
            else:
                # Para 'percentage_line' o 'fixed_line': no aplicar descuento global automático
                pass
                
        # Fuerza el volcado de datos al cursor
        self.env.cr.flush()
    
    @api.constrains('global_discount_type', 'global_discount_fixed_amount', 'order_line', 'order_line.price_subtotal')
    def _check_global_discount_fixed_amount(self):
        for order in self:
            if order.global_discount_type == 'fixed' and order.global_discount_fixed_amount:
                # Calculate current total subtotal from lines (already net of line discounts)
                # Ensure to use the same filtering as in _amount_all for consistency
                order_lines = order.order_line.filtered(lambda x: not x.display_type and not x.hide)
                current_subtotal = sum(line.price_subtotal for line in order_lines)
                if order.global_discount_fixed_amount > current_subtotal:
                    raise UserError(_('Global fixed discount amount (%(amount).2f) cannot exceed the total untaxed amount before global discount (%(subtotal).2f).') % {
                        'amount': order.global_discount_fixed_amount,
                        'subtotal': current_subtotal
                    })

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
                if order.invoice_status == 'done':
                    order.invoice_status = 'done'
                else:
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

    total_discount_amount_lines = fields.Monetary(
        string='Total Descuento por Líneas',
        compute='_compute_total_discount_amount_lines',
        store=False,
        currency_field='currency_id'
    )

    @api.depends(
        'order_line.discount',
        'order_line.discount_type',
        'order_line.discount_fixed_amount',
        'order_line.price_unit',
        'order_line.product_qty',
        'global_discount_type'
    )
    def _compute_total_discount_amount_lines(self):
        for order in self:
            total = 0.0
            if order.global_discount_type == 'percentage_line':
                total = sum((line.price_unit * line.product_qty) * (line.discount / 100.0) for line in order.order_line if not line.hide)
            elif order.global_discount_type == 'fixed_line':
                total = sum(line.discount_fixed_amount * line.product_qty for line in order.order_line if not line.hide)
            order.total_discount_amount_lines = total
            # 2025.06.06: Calcular total de descuentos de la orden de compra
            order.total_discount = order.total_discount_amount_lines
    
    @api.onchange('global_discount_type', 'global_discount_percentage', 'global_discount_fixed_amount')
    def _onchange_global_discount_type(self):
        for order in self:
            # Primero limpiar descuentos existentes en las líneas
            for line in order.order_line:
                if order.global_discount_type == 'percentage':
                    line.discount_type = 'percentage'
                    # Los valores se calcularán en _compute_global_discount
                elif order.global_discount_type == 'fixed':
                    line.discount_type = 'fixed'
                    # Los valores se calcularán en _compute_global_discount
                elif order.global_discount_type == 'percentage_line':
                    line.discount_type = 'percentage'
                    # Opcional: establecer valor por defecto
                    line.discount = 0.0
                    line.discount_fixed_amount = 0.0
                    line.price_unit_discounted = 0.0
                    #if not line.discount:
                    #    line.discount = order.global_discount_percentage
                    # Recalcular el monto fijo basado en el porcentaje de la línea
                    # line.discount_fixed_amount = (line.discount / 100.0) * line.price_unit if line.price_unit > 0 else 0
                elif order.global_discount_type == 'fixed_line':
                    line.discount_type = 'fixed'
                    # line.discount_fixed_amount = 0.0
                    line.price_unit_discounted = 0.0
                    # Limpiar valores globales para este modo
                    line.discount = 0.0
                        
            # Aplicar la distribución del descuento global (solo para 'percentage' y 'fixed')
            if order.global_discount_type in ['percentage', 'fixed']:
                order._compute_global_discount()
                
        # 2025.05.31: Inicializar los descuentos globales
        for order in self:
            if order.global_discount_type == 'percentage':
                order.global_discount_fixed_amount = 0.0
            elif order.global_discount_type == 'fixed':
                order.global_discount_percentage = 0.0
            elif order.global_discount_type == 'percentage_line':
                order.global_discount_percentage = 0.0
                order.global_discount_fixed_amount = 0.0
            elif order.global_discount_type == 'fixed_line':
                order.global_discount_percentage = 0.0
                order.global_discount_fixed_amount = 0.0
    
        # Recalcular totales de la orden de compra
        self._amount_all()

    total_discount_percentage = fields.Float(
        string='Total Discount (%)',
        compute='_compute_total_discount_percentage',
        store=False
    )
    total_discount_fixed_amount = fields.Monetary(
        string='Total Discount Fixed',
        compute='_compute_total_discount_fixed_amount',
        store=False,
        currency_field='currency_id'
    )

    @api.depends('order_line.discount', 'order_line.discount_type')
    def _compute_total_discount_percentage(self):
        for order in self:
            # Suma solo los descuentos en porcentaje
            order.total_discount_percentage = sum(
                line.discount for line in order.order_line if line.discount_type == 'percentage'
            )

    @api.depends('order_line.discount_fixed_amount', 'order_line.discount_type')
    def _compute_total_discount_fixed_amount(self):
        for order in self:
            # Suma solo los descuentos fijos
            order.total_discount_fixed_amount = sum(
                line.discount_fixed_amount * line.product_qty for line in order.order_line if line.discount_type == 'fixed'
            )
    def _compute_subtotal_without_discount(self):
        for order in self:
            subtotal = 0.0
            for line in order.order_line:
                if not line.hide:
                    subtotal += line.price_unit * line.product_qty
            return subtotal
    def _compute_total_discount(self):
        for order in self:
            total_discount = 0.0
            if order.global_discount_type == 'percentage':
                total_discount = order.global_discount_percentage * order.subtotal_without_discount / 100.0
            elif order.global_discount_type == 'fixed':
                total_discount = order.global_discount_fixed_amount
            elif order.global_discount_type == 'percentage_line':
                #total_discount = order.global_discount_percentage * order.subtotal_without_discount / 100.0
                total_discount = order.total_discount_amount_lines
            elif order.global_discount_type == 'fixed_line':
                #total_discount = order.global_discount_fixed_amount
                total_discount = order.total_discount_amount_lines
            return total_discount

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    allow_qty_change_line = fields.Boolean(
        related='order_id.allow_qty_change',
        store=False
    )
    notes = fields.Text(string='Notes')
    hide = fields.Boolean(string='Hide in Report', default=False)

    line_number_display = fields.Char(
        string='#',
        compute='_compute_line_number_display',
        store=False
    )
    discount = fields.Float(string="Discount (%)", digits="Discount")
    phase_id = fields.Many2one("project.phaseproject",
                               string="Fase",
                               tracking=True,
                               domain="[('account_analytic_id', '=', account_analytic_id)]")
    discount_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount')],
        string='Tipo Descuento',
        default='percentage',
        tracking=True)
    discount_fixed_amount = fields.Monetary(
        string='Descuento Fijo',
        compute='_compute_discount_fixed_amount',
        inverse='_inverse_discount_fixed_amount',
        store=True,
        tracking=True)
    

    _sql_constraints = [
        (
            "discount_limit",
            "CHECK (discount <= 100.0)",
            "Discount must be lower than 100%.",
        ),
        (
            "discount_fixed_amount_limit",
            "CHECK (discount_fixed_amount >= 0.0)",
            "Discount amount must be positive.",
        )
    ]

    price_unit_discounted = fields.Monetary(
        compute='_compute_price_unit_discounted',
        string='Initial Discounted Price'
    )

    # Métodos computados
    @api.depends('order_id.order_line', 'sequence')
    def _compute_line_number_display(self):
        """Calcula el número de línea correlativo (1, 2, 3...) en vez de la secuencia
        Maneja correctamente líneas nuevas sin ID y recalcula al mover/agregar líneas"""

        # Procesar por orden para mayor eficiencia
        for order in self.mapped('order_id'):
            # Filtrar líneas válidas que tienen ID
            lines_with_id = order.order_line.filtered(
                lambda l: not l.display_type and l.id
            ).sorted('sequence')

            # Asignar números correlativos a líneas guardadas
            for idx, line in enumerate(lines_with_id, start=1):
                line.line_number_display = str(idx)

        # Manejar líneas nuevas sin ID (en creación)
        for line in self.filtered(lambda l: not l.id):
            if line.order_id:
                # Contar líneas existentes + 1
                existing_count = len(line.order_id.order_line.filtered(
                    lambda l: not l.display_type and l.id
                ))
                line.line_number_display = str(existing_count + 1)
            else:
                line.line_number_display = "•"  # Temporal hasta que se asigne a una orden

    def action_open_line_form(self):
        """Abrir formulario completo de la línea en popup"""
        self.ensure_one()
        # Obtener el número de línea correlativo calculado
        line_number = self.line_number_display or "0"
        return {
            'name': f'Línea #{line_number} - {self.product_id.name or "Nueva Línea"}',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order.line',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',  # Abrir en popup
            'context': self.env.context,
            'view_id': self.env.ref('jobcostphasecat.view_purchase_order_line_form_complete_popup').id,
        }

    @api.depends('price_unit', 'discount', 'discount_type', 'discount_fixed_amount')
    def _compute_price_unit_discounted(self):
        for line in self:
            if line.discount_type == 'percentage':
                line.price_unit_discounted = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            elif line.discount_type == 'fixed':
                # Ensure discounted price doesn't go below zero
                line.price_unit_discounted = max(0.0, line.price_unit - line.discount_fixed_amount)
            else:
                line.price_unit_discounted = line.price_unit

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount', 'discount_type', 'discount_fixed_amount')
    def _compute_amount(self):
        for line in self:
            price_reduce = 0.0
            if line.discount_type == 'percentage':
                price_reduce = line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)
            elif line.discount_type == 'fixed':
                price_reduce = line.price_unit - line.discount_fixed_amount
                if price_reduce < 0.0: # Ensure price_reduce doesn't go below zero
                    price_reduce = 0.0
            else: # Failsafe, though should not happen with a default value
                price_reduce = line.price_unit

            # Sanity check for fixed discount not exceeding total value before tax
            if line.discount_type == 'fixed' and line.discount_fixed_amount > (line.price_unit * line.product_qty) and line.product_qty > 0 :
                # This case should ideally be prevented by a constraint or onchange warning
                # For now, we ensure price_subtotal is not negative.
                # The price_reduce here is per unit, so the check should be against price_unit.
                # However, the fixed discount is often conceptualized against the line total.
                # Let's adjust price_reduce to be per unit for tax calculation.
                # If discount_fixed_amount is meant for the whole line, then price_reduce logic needs care.
                # Assuming discount_fixed_amount is a discount per unit for now as per typical POL structure.
                # If discount_fixed_amount is for the line total, then:
                # price_reduce_total_line = (line.price_unit * line.product_qty) - line.discount_fixed_amount
                # price_reduce_unit = price_reduce_total_line / line.product_qty if line.product_qty else 0
                # For now, sticking to discount_fixed_amount as a per-unit discount based on typical field placement.
                # Let's assume discount_fixed_amount is a discount per unit.
                # price_reduce was already calculated as line.price_unit - line.discount_fixed_amount
                # The check `if price_reduce < 0.0: price_reduce = 0.0` handles this at unit level.
                pass # The negative check for price_reduce already handles this at unit level.


            price_on_line = line.product_qty * price_reduce
            # 2025.05.30: Se recalcula los impuestos para evitar CacheMiss en company_id
            if line.taxes_id:
                # recarga los impuestos para evitar CacheMiss en company_id
                taxes_rs = self.env['account.tax'].browse(line.taxes_id.ids)
                # opcional: asegurar flush si acabas de crear impuestos en la misma transacción
                self.env.cr.flush()
                taxes_rs = taxes_rs.with_company(line.order_id.company_id)
                taxes = taxes_rs.compute_all(
                    price_reduce,
                    line.order_id.currency_id,
                    line.product_qty,
                    product=line.product_id,
                    partner=line.order_id.partner_id
                )

                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })
            else:
                line.update({
                    'price_tax': 0.0,
                    'price_total': price_on_line,
                    'price_subtotal': price_on_line,
                })
    @api.constrains('discount_type', 'discount_fixed_amount', 'price_unit', 'product_qty')
    def _check_discount_fixed_amount(self):
        for line in self:
            if line.discount_type == 'fixed' and line.product_qty > 0: # Avoid division by zero if product_qty is 0
                # The discount_fixed_amount is per unit in this implementation
                if line.discount_fixed_amount > line.price_unit:
                    raise models.ValidationError(_('Fixed discount amount cannot exceed the unit price.'))
            # If discount_fixed_amount was intended for the total line:
            # if line.discount_type == 'fixed' and line.discount_fixed_amount > (line.price_unit * line.product_qty):
            #     raise models.ValidationError(_('Fixed discount amount cannot exceed the total line amount (Price * Quantity).'))


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
            # Definir qué se considera "historial".
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
    # 2025.08.01: Modificado para permitir ordenamiento (store=True)
    pr_ref_ids = fields.Many2one(
        related='order_id.pr_ref_id',
        string='Referencia SdC',
        store=True,
        readonly=True
    )
    
    # 2025.08.01: Agregar campo relacionado para categoría del producto
    # 2025.08.01: Modificado store=True para permitir agrupación
    product_categ_id = fields.Many2one(
        related='product_id.categ_id',
        string='Categoría Producto',
        store=True,
        readonly=True
    )
    
    # 2025.08.01: Agregar campo relacionado para fecha de SdC
    pr_request_date = fields.Date(
        related='pr_ref_ids.request_date',
        string='Fecha SdC',
        store=True,
        readonly=True
    )
    
    # 2025.08.01: Campo calculado para días diferidos entre SdC y OC
    days_deferred = fields.Integer(
        string='Días Diferidos',
        compute='_compute_days_deferred',
        store=True,
        readonly=True,
        help='Días transcurridos entre la Fecha de SdC y la Fecha de Orden de Compra'
    )
    
    # 2025.08.01: Campo calculado para horas diferidos entre SdC y OC
    hours_deferred = fields.Float(
        string='Horas Diferidas',
        compute='_compute_days_deferred',
        store=True,
        readonly=True,
        digits=(16, 1),
        help='Horas transcurridas entre la Fecha de SdC y la Fecha de Orden de Compra'
    )
    
    # 2025.08.01: Campos calculados que excluyen líneas ocultas para totales correctos
    price_subtotal_visible = fields.Monetary(
        string='Subtotal (Visible)',
        compute='_compute_visible_totals',
        store=True,
        readonly=True,
        help='Subtotal excluyendo líneas ocultas'
    )
    
    price_total_visible = fields.Monetary(
        string='Total (Visible)',
        compute='_compute_visible_totals',
        store=True,
        readonly=True,
        help='Total excluyendo líneas ocultas'
    )
    
    price_tax_visible = fields.Monetary(
        string='Impuesto (Visible)',
        compute='_compute_visible_totals',
        store=True,
        readonly=True,
        help='Impuesto excluyendo líneas ocultas'
    )

    @api.depends('pr_request_date', 'date_order')
    def _compute_days_deferred(self):
        """Calcula los días y horas diferidos entre la fecha de SdC y la fecha de OC"""
        for line in self:
            if line.pr_request_date and line.date_order:
                # Convertir fechas a datetime para cálculo preciso
                request_datetime = fields.Datetime.from_string(str(line.pr_request_date) + ' 00:00:00')
                order_datetime = line.date_order
                
                # Calcular diferencia
                diff = order_datetime - request_datetime
                line.days_deferred = diff.days
                line.hours_deferred = diff.total_seconds() / 3600.0
            else:
                line.days_deferred = 0
                line.hours_deferred = 0.0

    @api.depends('hide', 'price_subtotal', 'price_total', 'price_tax')
    def _compute_visible_totals(self):
        """Calcula los totales excluyendo líneas ocultas"""
        for line in self:
            if line.hide:
                # Si la línea está oculta, los campos visibles son 0
                line.price_subtotal_visible = 0.0
                line.price_total_visible = 0.0
                line.price_tax_visible = 0.0
            else:
                # Si la línea es visible, usar los valores originales
                line.price_subtotal_visible = line.price_subtotal
                line.price_total_visible = line.price_total
                line.price_tax_visible = line.price_tax

    @api.depends('order_id.order_line.pr_ref_ids')
    def _compute_pr_ref_ids(self):
        for line in self:
            # si pr_ref_ids es un Many2many, por ejemplo:
            line.pr_ref_ids = [(6, 0, [line.order_id.pr_ref_id.id])]

    @api.onchange('discount_type', 'price_unit', 'discount', 'discount_fixed_amount', 'product_qty')
    def _onchange_discount_type(self):
        for line in self:
            if line.discount_type == 'fixed':
                # Al cambiar a descuento fijo, calcular el porcentaje equivalente
                if line.price_unit > 0 and line.discount_fixed_amount >= 0:
                    # El descuento fijo es por unidad
                    line.discount = (line.discount_fixed_amount / line.price_unit) * 100
                else:
                    line.discount = 0.0
            elif line.discount_type == 'percentage':
                # Al cambiar a descuento porcentual, calcular el monto fijo equivalente
                if line.price_unit > 0 and line.discount >= 0:
                    line.discount_fixed_amount = (line.discount / 100.0) * line.price_unit
                else:
                    line.discount_fixed_amount = 0.0
                    
        # Forzar recálculo de campos computados
        for line in self:
            line._compute_price_unit_discounted()
            line._compute_amount()
            
        # Si hay orden padre, recalcular totales
        if self.order_id:
            self.order_id._amount_all()
        
        # 2025.06.06: Calcular total de descuentos de la orden de compra
        self.order_id.total_discount = self.order_id._compute_total_discount()

    @api.depends('discount_type', 'discount', 'price_unit')
    def _compute_discount_fixed_amount(self):
        # 2025.05.31: Recalcular los descuentos fijos de las líneas de compra
        for line in self:
            if line.discount_type == 'percentage':
                # Calcular monto fijo basado en el porcentaje y precio unitario
                line.discount_fixed_amount = (line.discount / 100.0) * line.price_unit if line.price_unit > 0 and line.discount > 0 else 0.0
            elif line.discount_type == 'fixed':
                # Para tipo fijo, calcular también basado en el porcentaje (que fue calculado en _compute_global_discount)
                line.discount_fixed_amount = (line.discount / 100.0) * line.price_unit if line.price_unit > 0 and line.discount > 0 else 0.0
            else:
                line.discount_fixed_amount = 0.0

    def _inverse_discount_fixed_amount(self):
        for line in self:
            if line.discount_type == 'fixed' and line.price_unit > 0:
                # Cuando el usuario cambia el monto fijo manualmente, calcular el porcentaje equivalente
                line.discount = (line.discount_fixed_amount / line.price_unit) * 100 if line.discount_fixed_amount > 0 else 0.0
