from odoo import api, fields, models

class ValoresDefaults(models.Model):
    _name = 'valores.defaults'
    _description = 'Valores Defaults'

    user_id = fields.Many2one('res.users', string='Usuario', required=True)
    clave_valor = fields.Char(string='Clave Valor', required=True)
    nombre_clave = fields.Char(string='Nombre de la Clave', required=True)
    modelo_usado = fields.Char(string='Modelo Usado', required=True)

    @api.model
    def crear_registro(self, valores):
        # Crear un registro
        registro_creado = self.create(valores)
        return registro_creado

    def leer_registro(self):
        # Leer los campos del registro actual
        valores = self.read(['user_id', 'clave_valor', 'nombre_clave', 'modelo_usado'])
        return valores

    def escribir_registro(self, valores):
        # Escribir/Actualizar el registro actual
        self.write(valores)

    @api.model
    def buscar_y_devolver_valor_clave(self, user_id, nombre_clave, modelo_usado):
        """
        Busca el último registro basado en user_id, nombre_clave, y modelo_usado.
        Devuelve el valor de 'clave_valor' del registro más reciente si se encuentra alguno, de lo contrario None.
        """
        # Buscamos el registro más reciente que coincida con los criterios.
        # Ordenamos por 'write_date' para obtener el último modificado o por 'create_date' si 'write_date' no está disponible.
        registro = self.search([
            ('user_id', '=', user_id),
            ('nombre_clave', '=', nombre_clave),
            ('modelo_usado', '=', modelo_usado),
        ], order='write_date desc, create_date desc', limit=1)  # Ordenamos por 'write_date' y 'create_date' en orden descendente
        
        if registro:
            return registro.clave_valor
        else:
            return None
