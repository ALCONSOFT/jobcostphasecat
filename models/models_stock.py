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

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    category_id = fields.Many2one(
        "project.category", string="Category", tracking=True)

class JC_StockMove(models.Model):
    _inherit = "stock.move"

    @api.depends('account_analytic_id')
    def _bldf(self):
        print('Entrando a _bldf')
        domain=""" [] """
        for record in self:
            if not record.account_analytic_id:
                domain=""" [] """
                print('dominio: sin filtro')
            else:
                domain=""" [("account_analytic_id", "=", %d )]
                    """ % (record.account_analytic_id)
                print('dominio: con filtro:', domain)
            return domain

    account_analytic_id = fields.Many2one(
        'account.analytic.account',
        readonly=False, string='Cuenta Analítica')
    # Alconor: 23-dic-2024
    vehicle_id = fields.Many2one(
        'fleet.vehicle', 
        string='Vehículo',
        tracking=True,
        help="Vehículo asignado para esta transferencia"
    )
    # -------------------------
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
    # Alconor: 25-dic-2024
    # Update field definition
    analytic_account_line_id = fields.Many2one(
        'account.analytic.line',
        string='Línea Analítica',
        required=True,  # Make field required
        copy=False,
        index='btree_not_null',
        domain="[('account_id', '!=', False)]",  # Only valid analytic lines
        help='Línea analítica asociada al movimiento de stock'
    )
    # Add validation constraint
    @api.constrains('analytic_account_line_id')
    def _check_analytic_account_line(self):
        for record in self:
            if not record.analytic_account_line_id:
                raise ValidationError(_('Debe especificar una línea analítica para este movimiento.'))
    # Add onchange for default value
    @api.onchange('picking_id')
    def _onchange_picking_analytic(self):
        if self.picking_id and self.picking_id.full_analytic_account_id:
            analytic_line = self.env['account.analytic.line'].search(
                [('account_id', '=', self.picking_id.full_analytic_account_id.id)],
                limit=1
            )
            if analytic_line:
                self.analytic_account_line_id = analytic_line.id    
    # -------------------------
    # ALCONOR: Valida que las fases seleccionadas sean las correspondientes a la cuenta analitica seleccioanda. 
    @api.onchange('phase_id')
    def onchange_phase_id(self):
        print("----> Entrando a Cambio de Fase---------------------------------")
        for record in self:
            if not self.phase_id:
                return
            else:
                ca_filtro = self.account_analytic_id
                if self.description_picking == False:
                    self.description_picking = self.phase_id.name
                else:
                    self.description_picking += " " + self.phase_id.name
                print('Filtro: ', ca_filtro)
                #msg_1 = 'Linea: %d - La Cuenta Analitica seleccioanda: %s no corresponde a la Cuanta Analitica de la Fase seleecionada: %s' % (record, ca_selecc, ca_filtro)
                #raise exceptions.Warning(msg_1)

    @api.onchange('analytic_distribution', 'account_analytic_id')
    def onchange_aaid(self):
        print("-----> Entrando a: cambio de Analytic Distribution -------------------") 
        for record in self:
            if not self.account_analytic_id:
                # Alconor: 22-mar-2022
                self.account_analytic_id = self.env['stock.picking'].browse(self.picking_id.full_analytic_account_id).id
                # Alconor: 24-dic-2024
                # Retornar un diccionario con el ID de la cuenta analítica y el 100% de distribución
                self.analytic_distribution = {str(self.account_analytic_id.id): 100.0}
                # -------------------------
                # self: hace referenca al modelo actual en el que se esta apuntando.
                # env: hace referencia al Enviroment o Entorno; por el cual se puede localizar cualquier otro modelo
                # modelo: clases de python que en odoo se usan para acceeder a los registros de bases de datos o funciones
                # browse: visor o examinador que permite hacer referencia campo o field del modelo que se requiere
                #         dentro del browse siempre el parametro sera un id, que es la fila del registro en cuestión.
                # 22-mar-2022
                return
            else:
                ln_aaid = self.account_analytic_id
                # Alconor: 25-dic-2024
                self.analytic_distribution = {str(self.account_analytic_id.id): 100.0}
                # -------------------------
                #self.analytic_distribution = {}
                print('El indice de las aaid es: %', ln_aaid)
                # Llamar a la función _bldf
                domini = self._bldf()
                self.phase_id = fields.Many2one("project.phaseproject",
                               string="Fase",
                               tracking=True,
                               domain= domini
                               )

                return

    def action_show_details(self):
        # Method disabled/not implemented
        raise UserError(_("This action is not available."))
    # 2025.04.29
    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        # Leer parámetro
        require = self.env['ir.config_parameter'].sudo() \
            .get_param('jobcostphasecat.require_phase_id_out_transfer', 'False') \
            .lower() == 'true'
        if require:
            for move in moves:
                if move.picking_id.picking_type_id.code == 'outgoing' and not move.phase_id:
                    raise ValidationError(_("Debe seleccionar la Fase para los movimientos de salida."))
        return moves

    def write(self, vals):
        res = super().write(vals)
        # Leer parámetro
        require = self.env['ir.config_parameter'].sudo() \
            .get_param('jobcostphasecat.require_phase_id_out_transfer', 'False') \
            .lower() == 'true'
        if require:
            for move in self:
                if move.picking_id.picking_type_id.code == 'outgoing' and not move.phase_id:
                    raise ValidationError(_("Debe seleccionar la Fase para los movimientos de salida."))
        return res
    
    # Alconor: 2025.04.29


class JC_StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    category_id = fields.Many2one(
        "project.category", string="Categoria", tracking=True)
    account_analytic_id = fields.Many2one(
        'account.analytic.account',
        readonly=True,
        string='Cuenta Analítica',
        compute='_compute_account_analytic_id',
        related='move_id.account_analytic_id',
        store=True)
    # Alconor: 2025.06.03
    # analytic_distribution = fields.Float(
    #         string="Distribución Analítica",
    #         related="analytic_distribution",
    #         store=True,
    #         readonly=True
    #     )    

    @api.depends('move_id.account_analytic_id')
    def _compute_account_analytic_id(self):
        for line in self:
            if not line.account_analytic_id and line.move_id.account_analytic_id:
                line.account_analytic_id = line.move_id.account_analytic_id
    # Alconor: 23-dic-2024
    vehicle_id = fields.Many2one(
        'fleet.vehicle', 
        string='Vehículo',
        tracking=True,
        help="Vehículo asignado para esta transferencia"
    )
    # -------------------------
    phase_id = fields.Many2one("project.phaseproject",
                               string="Fase",
                               tracking=True
                               )

