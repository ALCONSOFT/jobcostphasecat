from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EthicsPurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    def _default_picking_type_id(self):
        """Busca el tipo de operación predeterminado basado en el almacén del usuario
        y se asegura de que sea consistente con la cuenta analítica del almacén."""
        # Buscar el almacén predeterminado asignado al usuario actual
        user_warehouse = self.env.user.default_warehouse_id  # Asume un campo personalizado en res.users
        if not user_warehouse:
            # Si no hay almacén predeterminado para el usuario, usa el primero disponible
            user_warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', self.env.company.id)], 
                limit=1
            )
        
        # Buscar el tipo de operación 'incoming' relacionado con el almacén
        picking_type = self.env['stock.picking.type'].search(
            [('warehouse_id', '=', user_warehouse.id), ('code', '=', 'incoming')], 
            limit=1
        )
        
        # Asegurar que la cuenta analítica del almacén sea consistente con el tipo de operación
        if picking_type and user_warehouse.account_analytic_id:
            if not self.account_analytic_id or self.account_analytic_id != user_warehouse.account_analytic_id:
                self.account_analytic_id = user_warehouse.account_analytic_id.id

        return picking_type
    
    
    def _default_warehouse_id(self):
        """Obtiene el primer almacén relacionado con la compañía del usuario actual."""
        return self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], 
            limit=1
        )

    def _default_account_analytic_id(self):
        """Obtiene la cuenta analítica predeterminada del almacén por defecto."""
        default_warehouse = self._default_warehouse_id()
        return default_warehouse.account_analytic_id.id if default_warehouse else False

    warehouse_id = fields.Many2one(
        'stock.warehouse', 
        string='Almacén', 
        domain="[('company_id', '=', company_id)]", 
        required=True, 
        readonly=False, 
        default=_default_warehouse_id
    )
    account_analytic_id = fields.Many2one(
        'account.analytic.account', 
        string='Cuenta Analítica', 
        readonly=False, 
        tracking=True,
        default=_default_account_analytic_id
    )

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        """Actualiza la cuenta analítica según el almacén seleccionado."""
        if self.warehouse_id:
            self.account_analytic_id = self.warehouse_id.account_analytic_id.id

    @api.model
    def create(self, vals):
        """Asegura que la cuenta analítica sea asignada basada en el almacén durante la creación."""
        if 'warehouse_id' in vals and not vals.get('account_analytic_id'):
            warehouse = self.env['stock.warehouse'].browse(vals['warehouse_id'])
            vals['account_analytic_id'] = warehouse.account_analytic_id.id if warehouse.account_analytic_id else False
        return super(EthicsPurchaseRequest, self).create(vals)

    def write(self, vals):
        """Actualiza la cuenta analítica si cambia el almacén."""
        if 'warehouse_id' in vals and not vals.get('account_analytic_id'):
            warehouse = self.env['stock.warehouse'].browse(vals['warehouse_id'])
            vals['account_analytic_id'] = warehouse.account_analytic_id.id if warehouse.account_analytic_id else False
        return super(EthicsPurchaseRequest, self).write(vals)
