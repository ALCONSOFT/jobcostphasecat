# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta
import time

class EthicsPurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', index='btree_not_null')
    account_analytic_id = fields.Many2one('account.analytic.account', readonly=False, string='Cuenta Analítica')

    def action_confirm_ethics(self):
            if any(line.product_qty == 0 for line in self.pr_lines):
                raise UserError(_("Can you please set product qty."))
            if all(line.vendor_ids for line in self.pr_lines):
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
                'order_line': lines,
                })
            purchase_orders.append(purchase_id.id)
        self.update({'purchase_ids': [(6, 0, purchase_orders)]})
        self.state = 'confirm'
        return True


class EthicsPuchasRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', index='btree_not_null')
    account_analytic_id = fields.Many2one('account.analytic.account', readonly=False, string='Cuenta Analítica')

class PurchaseOrders(models.Model):
    _inherit = 'purchase.order'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', index='btree_not_null')
    account_analytic_id = fields.Many2one('account.analytic.account', readonly=False, string='Cuenta Analítica')    

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', index='btree_not_null')
    account_analytic_id = fields.Many2one('account.analytic.account', readonly=False, string='Cuenta Analítica')

