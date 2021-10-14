# utf-8
# Alconsoft 2021 Alejandro Concepción
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from datetime import date, time
from odoo import api, fields, models, _, tools
##
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError, UserError, ValidationError, ValidationError, Warning, RedirectWarning
from odoo.tools.misc import formatLang, get_lang
#from openerp import exceptions
#import logging
##

# CREACION DEL MODELO DE LA VISTA: Vista SQL Cargador Salidas Almacen Softland
# PAQUETE DE INVENTARIO	DOCUMENTO DE INVENTARIO	LINEA	ARTICULO	BODEGA	CANTIDAD	Ajuste Configurable	Tipo	SUBTIPO	SubSubtipo	CENTRO DE COSTO	FASE	CUENTA CONTABLE	    OREDEN DE CAMBIO	NOTA
# ZU    	            CON-000	                1		X           0001	9           ~CC~            	C       D      	N			X               9       1-13-1301-001-001	1	                hola    

class JC_vsqlcss(models.Model):
    _name = 'project.vsqlcss'
    _auto = False

    name = fields.Char(string='Salida Inventario Bodega Fecha', readonly=True)
    id = fields.Integer(string='Linea', readonly=True)
    active = fields.Boolean('Activo', default=True, readonly=True)
    paquete_inventario = fields.Char(string='Paquete Inventario', readony=True)
    documento_inventario = fields.Char(string='Documento Inventario', readony=True)
    linea = fields.Integer(string='Linea', readonly=True)
    articulo = fields.Char(string='Articulo',readonly=True)
    bodega_id = fields.Many2one('stock_warehouse', readonly=True, string='Bodega')
    bodega = fields.Char(string='Bodega',readonly=True)
    cantidad = fields.Float(string='Cantidad', readonly=True)
    ajuste_configurable = fields.Char(string='Ajueste Configurable', readonly=True)
    tipo = fields.Char(string='Tipo', readonly=True)
    subtipo = fields.Char(string='SubTipo', readonly=True)
    subsubtipo = fields.Char(string='SubSubTipo', readonly=True)
    centro_costo_id = fields.Many2one('account_analytic_account', readonly=True, string='Centro Costo')
    centro_costo = fields.Char(string='Centro Costo',readonly=True)
    fase_id = fields.Many2one('project_task_phase', readonly=True, string='Fase')
    fase = fields.Char(string='Fase',readonly=True)
    cuenta_contable = fields.Char(string='Cuenta Contable', readonly=True)
    orden_cambio = fields.Char(string='Orden Cambio', readonly=True)
    notes = fields.Text(string='Notes', readonly=True)
    proyecto = fields.Char(string='Proyecto',readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """CREATE OR REPLACE VIEW project_vsqlcss AS (select row_number() OVER (PARTITION BY true) as id,
True as active,
sm.name, 
'ZU' as paquete_inventario,
'CON-000' as documento_inventario,
row_number() OVER (PARTITION BY true) as linea,
pp.default_code as articulo,
sl2."name" as bodega,
sm.product_qty as cantidad,
'~CC~' as ajuste_configurable,
'C' as tipo,
'D' as subtipo,
'N' as subsubtipo,
aaa.code as centro_costo,
ptp."name" as fase,
'1-13-1301-001-001' as cuenta_contable,
'1' as orden_cambio,
sm.note as notes,
1 as company_id
from public.stock_move sm  left join
public.product_product pp 
on sm.product_id = pp.id left join 
stock_location sl 
on sm.location_id = sl.id left join 
stock_location sl2
on sl.location_id = sl2.id left join
account_analytic_account aaa 
on sm.analytic_account_id = aaa.id left join 
project_task_phase ptp 
on sm.phase_id = ptp.id );
        """
        self.env.cr.execute(query)
