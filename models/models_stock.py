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

# CREACION DEL MODELO DE LA VISTA: FASES POR PROYECTO - PHASE PROJECT
class JC_PhaseProject(models.Model):
    _name = 'project.phaseproject'
    _auto = False

    name = fields.Char(string='Phase Name', readonly=True)
    account_analytic_id = fields.Many2one(
        'account.analytic.account', readonly=True, string='Cuenta Analítica')
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

    def name_get(self): 
        result = [] 
        for fase in self:
            if fase.notes == False:
                lc_fase = "Sin Descripción"
            else:
                lc_fase = fase.notes
            name = '%s {%s}' % (fase.name, ''.join(lc_fase)) 
            result.append((fase.id, name))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        '''# Accediendo al diccionario en la tercera posición de la lista (índice 2)
        diccionario0 = args[0][0]
        diccionario1 = args[0][1]
        diccionario2 = args[0][2]
        # Obtener el primer elemento (clave y valor)
        clave, valor = next(iter(diccionario2.items()))
        nargs = [[diccionario0, diccionario1, clave]]
        '''
        args = [] if args is None else args.copy() 
        if not(name == '' and operator == 'ilike'): 
            args += ['|', '|', 
                ('name', operator, name), 
                ('notes', operator, name)
                  ] 
        return super()._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)

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

    account_analytic_id = fields.Many2one('account.analytic.account', readonly=True, string='Cuenta Analítica')

    category_id = fields.Many2one(
        "project.category", string="Categoria", tracking=True)
    phase_id = fields.Many2one("project.phaseproject",
                               string="Fase",
                               tracking=True,
                               domain="[('account_analytic_id', '=', account_analytic_id)]"
                               # Alconor: 2021-09-29: aclaración importante del uso de parametro: domain
                               # 'account_analytic_id': es el campo del modelo actual
                               #  analytic_account_id : es el campo relacionado many2one del modelo o vista relacionado.
                               # Siempre en domain el primer parametro hace referencia al modelo actual
                               # Siempre en domain el segundo parametro hace referencia al operador
                               # Siempre en domain el tercer parametro hace referencia una constante o un valor del modelo de la tabla relacionada.
                               )

    # ALCONOR: Valida que las fases seleccionadas sean las correspondientes a la cuenta analitica seleccioanda. 
    @api.onchange('phase_id')
    def onchange_phase_id(self):
        print("----> Entrando a Cambio de Fase---------------------------------")
        for record in self:
            if not self.phase_id:
                return
            else:
                ca_filtro = self.analytic_account_id
                if self.description_picking == False:
                    self.description_picking = self.phase_id.name
                else:
                    self.description_picking += self.phase_id.name
                print('Filtro: ', ca_filtro)
                #msg_1 = 'Linea: %d - La Cuenta Analitica seleccioanda: %s no corresponde a la Cuanta Analitica de la Fase seleecionada: %s' % (record, ca_selecc, ca_filtro)
                #raise exceptions.Warning(msg_1)

    #@api.onchange('analytic_account_id')
    @api.onchange('analytic_distribution')
    def onchange_aaid(self):
        print("-----> En cambio de Analytic Distribution -------------------") 
        for record in self:
            if not self.analytic_account_id:
                # Alconor: 22-mar-2022
                self.analytic_account_id = self.env['stock.picking'].browse(self.picking_id.full_analytic_account_id).id
                # self: hace referenca al modelo actual en el que se esta apuntando.
                # env: hace referencia al Enviroment o Entorno; por el cual se puede localizar cualquier otro modelo
                # modelo: clases de python que en odoo se usan para acceeder a los registros de bases de datos o funciones
                # browse: visor o examinador que permite hacer referencia campo o field del modelo que se requiere
                #         dentro del browse siempre el parametro sera un id, que es la fila del registro en cuestión.
                # 22-mar-2022
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

