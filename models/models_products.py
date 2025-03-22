from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = ['product.template', 'mail.thread']
    _name = 'product.template'  # Asegura que el _name no cambie

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
