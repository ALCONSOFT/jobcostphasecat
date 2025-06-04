
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    part_number = fields.Char(
        string='Número de Parte / Código de Fabricante',
        help='Código o número de parte asignado por el fabricante',
        related='product_tmpl_id.part_number',
        store=True
    )

    @api.constrains('part_number')
    def _check_part_number_unique(self):
        for record in self:
            if record.part_number:
                duplicate = self.search([
                    ('part_number', '=', record.part_number),
                    ('id', '!=', record.id)
                ])
                if duplicate:
                    raise ValidationError(_('El número de parte %s ya existe en otro producto') % record.part_number)


class ProductTemplate(models.Model):
    _inherit = ['product.template', 'mail.thread']
    _name = 'product.template'  # Asegura que el _name no cambie

    # Campo para número de parte/código de fabricante
    part_number = fields.Char(
        string='Número de Parte / Código de Fabricante',
        help='Código o número de parte asignado por el fabricante',
        tracking=True,
        index=True  # Para búsquedas rápidas
    )

    _sql_constraints = [
        ('part_number_unique', 'unique(part_number)', 'El número de parte/código de fabricante debe ser único')
    ]
    

    # Campos con tracking para la bitácora
    standard_price = fields.Float(tracking=True)
    list_price = fields.Float(tracking=True)
    description = fields.Text(tracking=True)

    def _register_hook(self):
        super()._register_hook()
        allowed_types = (fields.Char, fields.Float, fields.Integer, fields.Text, 
                         fields.Selection, fields.Many2one, fields.Date, fields.Datetime, fields.Boolean)

        for field_name, field in self._fields.items():
            # Verificar si el campo es de un tipo permitido y si tiene el atributo 'tracking'
            if isinstance(field, allowed_types) and hasattr(field, 'tracking'):
                field.tracking = True
    
    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        for field in vals.keys():
            self.message_post(body=f"Cambio en {field}: {vals[field]}")
        return res

