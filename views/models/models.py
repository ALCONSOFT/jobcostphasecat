# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta

class JC_Category(models.Model):
    _name = 'project.category'
    _description = 'Categorias de Job Cost'
    name = fields.Char('Nombre Categoria', required=True)
    active = fields.Boolean('Activo', default=True)
    code_category = fields.Char('Referencia', required=True)
    cost_type = fields.Many2one('project.costtype', string = 'Tipo de Costos', tracking=True)

class JC_Cost_Type(models.Model):
    _name = "project.costtype"
    _description = 'Tipos de Costos de Job Cost'
    name = fields.Char('Nombre Tipo Costo')
    active = fields.Boolean('Activo', default=True)
    code_cost_type = fields.Char('Código Tipo Costo', required=True)


#    _inherit = 'project.project'
