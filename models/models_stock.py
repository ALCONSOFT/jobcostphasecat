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
from openerp import exceptions
#import logging
##

# CREACION DEL MODELO DE LA VISTA: FASES POR PROYECTO - PHASE PROJECT
class JC_PhaseProject(models.Model):
    _name = 'project.phaseproject'
    _auto = False

    name = fields.Char(string='Phase Name', readonly=True)
    account_analytic_id = fields.Many2one(
        'account_analytic_account', readonly=True, string='Cuenta Analítica')
    notes = fields.Text(string='Notes', readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """CREATE OR REPLACE VIEW project_phaseproject AS (
           select min(ptp.id) as id, aaa.id as account_analytic_id, ptp."name" , ptp.notes ,ptp.company_id 
from project_task_phase ptp inner join project_project pp 
on ptp .project_id = pp.id 
inner join account_analytic_account aaa 
on pp.analytic_account_id = aaa.id
group by aaa.id, ptp."name", ptp.notes, ptp.company_id);
        """
        self.env.cr.execute(query)


class JC_StockMove(models.Model):
    _inherit = "stock.move"

    @api.depends('analytic_account_id')
    def _bldf(self):
        print('Entrando a _bldf')
        domain=""" [] """
        for record in self:
            if not record.analytic_account_id:
                domain=""" [] """
                print('dominio: sin filtro')
            else:
                domain=""" [("account_analytic_id", "=", %d )]
                    """ % (record.analytic_account_id)
                print('dominio: con filtro:', domain)
            return domain

    category_id = fields.Many2one(
        "project.category", string="Categoria", tracking=True)
    phase_id = fields.Many2one("project.phaseproject",
                               string="Fase",
                               tracking=True,
                               domain="[('account_analytic_id', '=', analytic_account_id)]"
                               # Alconor: 2021-09-29: aclaración importante del uso de parametro: domain
                               # 'account_analytic_id': es el campo del modelo actual
                               #  analytic_account_id : es el campo relacionado many2one del modelo o vista relacionado.
                               # Siempre en domain el primer parametro hace referencia al modelo actual
                               # Siempre en domain el segundo parametro hace referencia al operador
                               # Siem  pre en domain el tercer paramtro hace referencia una constante o un valor del modelo de la tabla relacionada.
                               )
    
#     # ALCONOR: Filtrar la vista: "Fases de Proyecto" por "Cuenta Analítica"; seleccionada en la línea: [project.phaseproject por analytic_account_id]
#     @api.onchange('analytic_account_id')
#     def onchange_analytic_account_id(self):
#         if not self.analytic_account_id:
#             return
#         tools.drop_view_if_exists(self.env.cr, 'project.phaseproject')
#         self.env.cr.execute("""CREATE OR REPLACE VIEW project_phaseproject AS (
#            select min(ptp.id) as id, aaa.id as account_analytic_id, ptp."name" , ptp.notes ,ptp.company_id 
# from project_task_phase ptp inner join project_project pp 
# on ptp .project_id = pp.id 
# inner join account_analytic_account aaa 
# on pp.analytic_account_id = aaa.id
# where aaa.id = %d
# group by aaa.id, ptp."name", ptp.notes, ptp.company_id);
#         """ % (self.analytic_account_id)
#         )

    # ALCONOR: Valida que las fases seleccionadas sean las correspondientes a la cuenta analitica seleccioanda. 
    @api.onchange('phase_id')
    def onchange_phase_id(self):
        for record in self:
            if not self.phase_id:
                return
            else:
                ca_filtro = self.analytic_account_id
                print('Filtro: ', ca_filtro)
                #msg_1 = 'Linea: %d - La Cuenta Analitica seleccioanda: %s no corresponde a la Cuanta Analitica de la Fase seleecionada: %s' % (record, ca_selecc, ca_filtro)
                #raise exceptions.Warning(msg_1)

    @api.onchange('analytic_account_id')
    def onchange_aaid(self):
        print('Entrando a funcion: onchange_aaid')
        for record in self:
            if not self.analytic_account_id:
                return
            else:
                ln_aaid = self.analytic_account_id
                print('El indice de las aaid es: %', ln_aaid)
                # Llamar a la función _bldf
                domini = self._bldf()
                self.phase_id = fields.Many2one("project.phaseproject",
                               string="Fase",
                               tracking=True,
                               domain= domini
                               )

                return


class JC_StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    category_id = fields.Many2one(
        "project.category", string="Categoria", tracking=True)
    phase_id = fields.Many2one("project.phaseproject",
                               string="Fase",
                               tracking=True
                               )

#   RESTRICCION POR METODO: !!!!! NO FUNCIONA ¡¡¡¡¡¡
#    @api.constrains('phase_id')
#    def _check_phase_id_aaa(self):
#        for record in self:
#            if record.phase_id.account_analytic_id == record.analytic_account_id:
#                raise models.ValidationError(
#                    'La Cuenta Analítica debe ser la misma Cuenta Analítica de la Fase!')
