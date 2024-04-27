# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import timedelta
import time
from odoo.exceptions import ValidationError
import pytz
import datetime
from zoneinfo import ZoneInfo

contexto_purchase_request = []

class EthicsPurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    def action_waiting_for_audit(self):
        for rec in self:
            rec.state = 'waiting_for_audit'
            self.message_post(
                body=_('SdC: ' + self.name + ' enviada a Auditoría.')
            )


    def _default_picking_type_id(self):
        return self.env['stock.picking.type'].search([('warehouse_id.company_id', '=', self.env.company.id), ('code', '=', 'incoming')], limit=1)

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehículo', index='btree_not_null', tracking=True)
    account_analytic_id = fields.Many2one('account.analytic.account', string='Cuenta Analítica', readonly=False, tracking=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Almacén', domain="[('company_id', '=', company_id)]", required=True, readonly=False)
    sequence_alter = fields.Char(string='Secuencia Alterna', readonly=True, index=True, rerquired=True)
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type', required=True, default=_default_picking_type_id,
        domain="['|',('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]", tracking=True)
    # Extendiendo el campo 'state' para agregar el nuevo estado
    state = fields.Selection(selection_add=[('waiting_for_audit', 'Esperando Auditoría'),
                                                ('waiting_for_buyer', "Esperando Comprador")
        ], ondelete={'waiting_for_approver': 'cascade'})
    pr_lines = fields.One2many('purchase.request.line', 'pr_id', tracking=True)

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):

        valores_defaults_vehicle = {
            'user_id': self.env.user.id,
            'clave_valor': self.vehicle_id.id,
            'nombre_clave': 'vehicle_id',
            'modelo_usado': self._name
        }
        print('valores_defaults_vehicle', valores_defaults_vehicle)
        # Verifica si algún valor en el diccionario es False
        tiene_false = any(valor is False for valor in valores_defaults_vehicle.values())

        if tiene_false:
            print("Hay al menos un valor False en el diccionario.")
            print("No se registrara nada")
        else:
            print("No hay valores False en el diccionario.")        
            nuevo_registro = self.env['valores.defaults'].crear_registro(valores_defaults_vehicle)
        return False
    
    @api.onchange('account_analytic_id')
    def _onchange_account_analytic_id(self):

        valores_defaults_account_a = {
            'user_id': self.env.user.id,
            'clave_valor': self.account_analytic_id.id,
            'nombre_clave': 'account_analytic_id',
            'modelo_usado': self._name
        }
        print('valores_defaults_account_a', valores_defaults_account_a)
        # Verifica si algún valor en el diccionario es False
        tiene_false = any(valor is False for valor in valores_defaults_account_a.values())

        if tiene_false:
            print("Hay al menos un valor False en el diccionario.")
            print("No se registrara nada")
        else:
            print("No hay valores False en el diccionario.")        
            nuevo_registro = self.env['valores.defaults'].crear_registro(valores_defaults_account_a)
        return False

    def reject_audit_pr(self):
        view = self.env.ref('ethics_purchase_request.view_add_pr_cancel_reason_form')
        return {
            'name': ('Add Reason'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'add.pr.reason',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'target':'new'
        }
        
    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        self.warehouse_id = self.picking_type_id.warehouse_id

    def action_confirm_ethics(self):
            if any(line.product_qty == 0 for line in self.pr_lines):
                raise UserError(_("Can you please set product qty."))
            if all(line.vendor_ids for line in self.pr_lines):
                self.message_post(
                    body=_('SdC: ' + self.name + ' fué APROBADA POR GERENCIA.')
                )
                self.create_rfq_ethics()
            else:
                view = self.env.ref('ethics_purchase_request.view_back_purchase_request_form')
                wiz_lines = [(0, 0,
                            {'product_id': line.product_id.id,
                            'name': line.product_id.name,
                            'account_analytic_id': line.account_analytic_id.id,
                            'product_qty': line.product_qty,
                            'product_uom': line.product_uom.id,
                            'vehicle_id': line.vehicle_id,})
                            for line in self.pr_lines.filtered(lambda l: not l.vendor_ids and l.product_qty >= 1)]

                return {'name': _('Create Back Purchase Request'),
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'views': [(view.id, 'form')],
                        'view_id': view.id,
                        'res_model': 'back.purchase.request',
                        'target': 'new',
                        'context': {
                            'default_pr_id': self.id,
                            'default_employee_id': self.employee_id.id,
                            'default_department_id': self.department_id.id,
                            'default_request_responsible': self.request_responsible.id,
                            'default_request_date': self.request_date,
                            'default_company_id': self.company_id.id,
                            'default_source_document': self.name,
                            'default_vehicle_id': self.vehicle_id,
                            'default_warehouse_id': self.warehouse_id,
                            'default_back_purchase_request_ids': wiz_lines,
                            }
                        }

    def create_rfq_ethics(self):
        purchase_dict = {}
        purchase_orders = []
        for line in self.pr_lines.filtered(lambda l:l.vendor_ids):
            print("----------------line.vendor_ids----------",line.vendor_ids)
            for vendor in line.vendor_ids:
                print("=======IF==not vendor===purchase_dict====")
                if vendor not in purchase_dict:
                    print("=======IF not=====purchase_dict====",vendor,purchase_dict)
                    purchase_dict.update({vendor: []})
                if purchase_dict:
                    print("=======IF=====purchase_dict====",purchase_dict)
                    purchase_dict[vendor].append((0, 0, {'product_id': line.product_id.id,
                                                         'name': line.product_id.name, 
                                                         'product_qty': line.product_qty, 
                                                         'product_uom': line.product_uom.id, 
                                                         'price_unit': 0.0, 
                                                         'display_type': False, 
                                                         'vehicle_id': line.vehicle_id.id,
                                                         'account_analytic_id': line.account_analytic_id.id,
                                                         'date_planned': time.strftime('%Y-%m-%d')}))
        for vendor,lines in purchase_dict.items():
            purchase_id = self.env['purchase.order'].create({
                'partner_id': vendor.id,
                'pr_ref_id': self.id,
                'vehicle_id': self.vehicle_id.id,
                'account_analytic_id': self.account_analytic_id.id,
                'picking_type_id': self.picking_type_id.id,
                'order_line': lines,
                })
            purchase_orders.append(purchase_id.id)
        self.update({'purchase_ids': [(6, 0, purchase_orders)]})
        self.state = 'confirm'
        return True

    @api.onchange('warehouse_id', 'picking_type_id')
    def _onchange_warehouse(self):
        if self.warehouse_id:
            self.sequence_alter = self._get_sequence(self.warehouse_id.id)
        return 

    @api.model
    def create(self, vals):
        if vals.get('warehouse_id'):
            #vals['warehouse_id'] = self.warehouse_id.id
            vals['sequence_alter'] = self._get_sequence(vals['warehouse_id'])
        return super(EthicsPurchaseRequest, self).create(vals)

    def write(self, vals):
        if 'warehouse_id' in vals:
            vals['sequence_alter'] = self._get_sequence(vals['warehouse_id'])
        return super(EthicsPurchaseRequest, self).write(vals)

    def _get_sequence(self, warehouse_id):
        # Método para obtener la secuencia basada en el almacén
        warehouse = self.env['stock.warehouse'].browse(warehouse_id)
        cr = self.env.cr
        if warehouse.code:
            # Si el almacén tiene código
            cadena_sql = """SELECT MAX(sequence_alter) FROM public.purchase_request
                            WHERE substring(sequence_alter from 1 for %(len)s) = %(code)s;"""
            cr.execute(cadena_sql, {'len': len(warehouse.code), 'code': warehouse.code})
            result = cr.fetchone()
            import re
            if result and result[0] is not None:
                # Buscar la porción numérica después del código
                match = re.search(f'{re.escape(warehouse.code)}(\\d+)', result[0])
                if match:
                    numeric_part = match.group(1)  # Extrae la porción numérica
                # Incrementar la secuencia o realizar el ajuste necesario aquí
                # Por ejemplo, si la secuencia es un número, podrías intentar extraer la parte numérica y incrementarla
                # Asegúrate de ajustar esta parte según cómo necesitas que funcione la secuencia.
                next_sequence = str(int(numeric_part) + 1).zfill(5)
                sequence = f"{warehouse.code}{next_sequence}"
            else:
                # Definir una secuencia inicial o manejar el caso de no resultado
                sequence = f"{warehouse.code}00001"  # Asumiendo que quieres empezar desde aquí
        else:
            # No tiene código el almacén
            sequence = None
        return sequence
    
    def action_submit_for_verifier_jc(self):
        super(EthicsPurchaseRequest, self).action_submit_for_verifier()
        self.message_post(
            body=_('SdC: ' + self.name + ' enviada a Verificación.')
        )
    
    def reject_verifier_pr_jc(self):
        super(EthicsPurchaseRequest, self).reject_verifier_pr()
        self.message_post(
            body=_('SdC: ' + self.name + ' RECHAZADA en la Verificación. - Para mayor información consulte la notas internas o contacte con su Verificad@r')
        )

    # Accion: Enviar por Auditoria;  ENviar a Compras
    def action_submit_for_audit(self):
        self.state = 'waiting_for_buyer'        
        self.message_post(
            body=_('SdC: ' + self.name + ' se envió a Compras')
        )



class EthicsPuchasRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    vehicle_id = fields.Many2one('fleet.vehicle',
                                string='Vehículo',
                                index='btree_not_null',
                                 default=lambda self: self._default_vehicle_id(), tracking=True)
    account_analytic_id = fields.Many2one('account.analytic.account',
                                            readonly=False,
                                            string='Cuenta Analítica',
                                            default=lambda self: self._default_aaid(), tracking=True)
    product_qty = fields.Float('Quantity', default=1, tracking=True)
    product_uom = fields.Many2one('uom.uom', related='product_id.uom_po_id', tracking=True,
        help="This comes from the product form.")
    vendor_ids = fields.Many2many('res.partner', tracking=True)    

    def _default_vehicle_id(self):
        user_id = self.env.user.id
        nombre_clave = 'vehicle_id'
        modelo_usado = 'purchase.request'

        # Llamada a la función
        valor_clave = self.env['valores.defaults'].buscar_y_devolver_valor_clave(user_id, nombre_clave, modelo_usado)
        if valor_clave:
            print("Valor de clave encontrado:", valor_clave)
        else:
            print("No se encontró un registro con los criterios especificados.")
            valor_clave = 0
        return int(valor_clave)
    
    def _default_aaid(self):
        user_id = self.env.user.id
        nombre_clave = 'account_analytic_id'
        modelo_usado = 'purchase.request'

        # Llamada a la función
        valor_clave = self.env['valores.defaults'].buscar_y_devolver_valor_clave(user_id, nombre_clave, modelo_usado)
        if valor_clave:
            print("Valor de clave encontrado:", valor_clave)
        else:
            print("No se encontró un registro con los criterios especificados.")
            valor_clave = 0
        return int(valor_clave)

class BackEthicsPurchaseRequest(models.TransientModel):
    _inherit = 'back.purchase.request'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehículo', index='btree_not_null')

class BackEthicsPurchaseRequestLine(models.TransientModel):
    _inherit = 'back.purchase.request.line'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehículo', index='btree_not_null')

class PurchaseOrders(models.Model):
    _inherit = 'purchase.order'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', index='btree_not_null')
    account_analytic_id = fields.Many2one('account.analytic.account', readonly=False, string='Cuenta Analítica')
    # Extendiendo el campo 'state' para agregar el nuevos estados
    state = fields.Selection(selection_add=[('waiting_for_price_revision', 'Esperando Revisión Precios'),
                                            ('waiting_for_price_approval','Esperando Aprobación Precios'),
                                            ('waiting_for_approval','Esperando Aprobación'),
                                            ('to approve','Por Aprobar @ Compras')
        ], ondelete={'waiting_for_approval': 'cascade'})

    # Boton Enviar P.O. por email
    def action_rfq_send_jc(self):
        for rec in self:
            rec.state = 'done'
        super(PurchaseOrders, self).action_rfq_send()

    # Botones en waiting_for_price_revision
    def action_waiting_for_price_revision(self):
        for rec in self:
            rec.state = 'waiting_for_price_revision'
    
    def reject_waiting_for_price_revision(self):
        for rec in self:
            rec.state = 'sent'

    # Botones en waiting_for_price_approval
    def action_waiting_for_price_approval(self):
        for reg in self.order_line:
            if reg.price_total == 0:
                raise ValidationError("El valor del precio unitario no puede ser 0.")
                return
        for rec in self:
            rec.state = 'waiting_for_price_approval'
    
    def reject_waiting_for_price_approval(self):
        for rec in self:
            rec.state = 'waiting_for_price_revision'
    
    # Botones en waiting_for_approval
    def action_waiting_for_approval(self):
        for rec in self:
            rec.state = 'waiting_for_approval'
    # Boton en envio a Aprobacion SdP por Compras
    def action_send_to_approve_purchase(self):
        for rec in self:
            rec.state = 'to approve'
    # Botón en envio a 
    
    # Boton Rechazar Aprobación de SdP = Rechazar Pedido
    def reject_waiting_for_approval(self):
        # Acciones personalizadas antes de llamar al método de la clase base
        for record in self:
            record.state = 'waiting_for_price_approval'
        # Llamada al método reject_purchase de la clase base usando super()
        super(PurchaseOrders, self).reject_purchase()
    
    def action_buttom_approve_jc(self):
        for record in self:
            #record.state = 'to approve'
            print('Estado actual: ', record.state)
        # Llamada al método reject_purchase de la clase base usando super()
        super(PurchaseOrders, self).action_button_approve()

    """# Botón Rechazar Pedido - Cual funiona bien?????????
    def reject_puchase(self):
        super(PurchaseOrders, self).reject_purchase()
        for rec in self:
            rec.state = 'waiting_for_price_approval'
    """
    
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', index='btree_not_null')
    account_analytic_id = fields.Many2one('account.analytic.account', readonly=False, string='Cuenta Analítica')
