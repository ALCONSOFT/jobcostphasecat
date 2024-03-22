# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta

class EthicsPurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', index='btree_not_null')
    account_analytic_id = fields.Many2one('account.analytic.account', readonly=False, string='Cuenta Analítica')

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