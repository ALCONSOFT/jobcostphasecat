# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.addons.mail.models.mail_template import MailTemplate
import logging
from odoo import tools
from datetime import timedelta
import time
from odoo.exceptions import ValidationError, UserError
import pytz
import datetime
from zoneinfo import ZoneInfo
contexto_purchase_request = []
_logger = logging.getLogger(__name__)
contexto_purchase_request = []

class EthicsPurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    def unlink(self):
        for record in self:
            if record.state != 'cancel':
                    raise UserError("No puedes eliminar este registro. Debes cancelarlo primero.*")
            else:
                raise   UserError("No puedes eliminar este registro. Consulte con su administrador.")
        return super(EthicsPurchaseRequest, self).unlink()

    def action_waiting_for_audit(self):
        for rec in self:
            rec.state = 'waiting_for_audit'
            self.message_post(
                body=_('SdC: ' + self.name + ' enviada a Auditoría.')
            )

    vehicle_id = fields.Many2one('fleet.vehicle.data', string='Vehículo', tracking=True)
    # index='btree_not_null', 
    def action_open_vehicle_selection(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Vehicle',
            'res_model': 'fleet.vehicle.data',
            'view_mode': 'tree',
            'target': 'new',
        }

    warehouse_id = fields.Many2one('stock.warehouse', string='Almacén',
        domain="[('company_id', '=', company_id)]", required=True, readonly=False)    
    sequence_alter = fields.Char(string='Secuencia Alterna', readonly=True, index=True, rerquired=True)
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', tracking=True)
    #def _default_picking_type_id(self):
        #return self.env['stock.picking.type'].search([('warehouse_id.company_id', '=', self.env.company.id), ('code', '=', 'incoming')], limit=1)
    def _default_picking_type_id(self):
        """Busca el tipo de operación predeterminado basado en el almacén del usuario
        y se asegura de que sea consistente con la cuenta analítica del almacén."""
        # Buscar el almacén predeterminado asignado al usuario actual
        user_warehouse = self.env.user.property_warehouse_id  # Asume un campo personalizado en res.users
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

        return picking_type

    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type', required=True, default=_default_picking_type_id,
        domain="['|',('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]", tracking=True)

    def _default_account_analytic_id(self):
        picking_type = self._default_picking_type_id()
        """Obtiene la cuenta analítica predeterminada basada en el almacén relacionado con el tipo de operación."""
        if picking_type:
            account_analytic_id = picking_type.warehouse_id.account_analytic_id
            return account_analytic_id.id if account_analytic_id else False
        return False

    account_analytic_id = fields.Many2one('account.analytic.account',
        string='Cuenta Analítica',
        readonly=False,
        default =_default_account_analytic_id,
        tracking=True)

    # Extendiendo el campo 'state' para agregar los nuevos estados
    state = fields.Selection(selection_add=[
        ('waiting_for_audit', 'Esperando Auditoría'),
        ('waiting_for_buyer', "Esperando Comprador"),
        ('descarted', 'Descartado')
    ], ondelete={'waiting_for_approver': 'cascade'})
    pr_lines = fields.One2many('purchase.request.line', 'pr_id', tracking=True)

    approved_by_id = fields.Many2one(
        'res.users',
        string="Aprobado por",
        readonly=True,
        tracking=True  # Esto hace que se registre en el historial de cambios
    )

    def action_last_7_days_requests(self):
        today = fields.Date.context_today(self)
        date_from = today - timedelta(days=6)

        action = {
            'type': 'ir.actions.act_window',
            'name': 'Last 7 Days Requests',
            'view_mode': 'tree,form',
            'res_model': 'purchase.request',
            'domain': [('request_date', '>=', date_from), ('request_date', '<=', today)],
            'context': {'default_request_date': today},
        }
        return action

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        # Verifica si vehicle_id existe y es válido antes de proceder
        if not self.vehicle_id or not hasattr(self.vehicle_id, 'id'):
            print("Vehicle ID no es válido o no existe.")
            return False

        # Si vehicle_id es válido, procede con la creación del diccionario
        valores_defaults_vehicle = {
            'user_id': self.env.user.id,
            'clave_valor': self.vehicle_id.id,
            'nombre_clave': 'vehicle_id',
            'modelo_usado': self._name
        }
        print('valores_defaults_vehicle', valores_defaults_vehicle)

        # Verifica si algún valor en el diccionario es False
        tiene_false = any(valor is False for valor in valores_defaults_vehicle.values())

        if tiene_false:
            print("Hay al menos un valor False en el diccionario.")
            print("No se registrará nada")
        else:
            print("No hay valores False en el diccionario.")
            nuevo_registro = self.env['valores.defaults'].crear_registro(valores_defaults_vehicle)

        return False

    @api.onchange('account_analytic_id')
    def _onchange_account_analytic_id(self):

        valores_defaults_account_a = {
            'user_id': self.env.user.id,
            'clave_valor': self.account_analytic_id.id,
            'nombre_clave': 'account_analytic_id',
            'modelo_usado': self._name
        }
        print('valores_defaults_account_a', valores_defaults_account_a)
        # Verifica si algún valor en el diccionario es False
        tiene_false = any(valor is False for valor in valores_defaults_account_a.values())

        if tiene_false:
            print("Hay al menos un valor False en el diccionario.")
            print("No se registrara nada")
        else:
            print("No hay valores False en el diccionario.")        
            nuevo_registro = self.env['valores.defaults'].crear_registro(valores_defaults_account_a)
        return False

    def reject_audit_pr(self):
        view = self.env.ref('ethics_purchase_request.view_add_pr_cancel_reason_form')
        return {
            'name': ('Add Reason'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'add.pr.reason',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'target':'new'
        }
        
    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        self.warehouse_id = self.picking_type_id.warehouse_id

    def action_confirm_ethics(self):
        """
        1️⃣ Antes de comenzar, agrega todos los vendors de las líneas de producto a las líneas de sección y notas.
        2️⃣ Verifica que todas las líneas tengan una cantidad válida (> 0).
        3️⃣ Si todas las líneas de productos tienen vendors, aprueba la SdC.
        4️⃣ Si faltan vendors, abre un asistente para corregirlo.
        """
        # MEJORADO: Validar Purchase Orders existentes considerando su estado
        existing_po = self.env['purchase.order'].search([('pr_ref_id', '=', self.id)])
        if existing_po:
            # Filtrar solo Purchase Orders que NO están canceladas ni descartadas
            active_po = existing_po.filtered(lambda po: po.state not in ['cancel', 'descarted'])
            
            if active_po:
                # Si hay Purchase Orders activas, bloquear re-aprobación
                po_details = []
                for po in active_po:
                    po_details.append(f"• {po.name} (Estado: {dict(po._fields['state'].selection).get(po.state, po.state)})")
                
                raise UserError(_(
                    "Ya existen Solicitudes de Pedido (SdP) ACTIVAS para esta Solicitud de Compra (SdC):\n\n"
                    "%s\n\n"
                    "Para re-aprobar esta SdC, primero debe cancelar o descartar todas las SdP relacionadas."
                ) % '\n'.join(po_details))
            else:
                # Solo hay Purchase Orders canceladas/descartadas - permitir re-aprobación
                self.message_post(
                    body=_(
                        "🔄 RE-APROBACIÓN DETECTADA: Se encontraron %d Purchase Orders canceladas/descartadas "
                        "relacionadas con esta SdC. Se procederá a crear nuevas Purchase Orders."
                    ) % len(existing_po)
                )
        # 🔹 1️⃣ AGREGAR LOS PROVEEDORES A LAS SECCIONES Y NOTAS
        for section_or_note in self.pr_lines.filtered(lambda l: l.display_type in ['line_section', 'line_note']):
            # Obtener todos los vendors de las líneas de productos
            all_vendors = self.pr_lines.filtered(lambda l: not l.display_type).mapped('vendor_ids')

            # Asignar los vendors únicos a la línea de sección o nota
            section_or_note.vendor_ids = [(6, 0, all_vendors.ids)]

        # 🔹 2️⃣ VERIFICAR QUE TODAS LAS LÍNEAS TENGAN CANTIDAD > 0
        if any(line.product_qty == 0 for line in self.pr_lines):
            raise UserError(_("Can you please set product qty."))

        # 🔹 3️⃣ VERIFICAR SI TODAS LAS LÍNEAS TIENEN PROVEEDOR
        if all(line.vendor_ids for line in self.pr_lines if not line.display_type):
            self.message_post(
                body=_('SdC: ' + self.name + ' fue APROBADA POR GERENCIA. ' + self.env.user.name + ' la ha aprobado.')
            )
            self.create_rfq_ethics()

        else:
            # 🔹 4️⃣ ABRIR ASISTENTE PARA CORREGIR LÍNEAS SIN PROVEEDOR
            view = self.env.ref('ethics_purchase_request.view_back_purchase_request_form')
            wiz_lines = [(0, 0,
                        {'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'account_analytic_id': line.account_analytic_id.id,
                        'product_qty': line.product_qty,
                        'product_uom': line.product_uom.id,
                        'vehicle_id': line.vehicle_id,
                        })
                        for line in self.pr_lines.filtered(lambda l: not l.vendor_ids and l.product_qty >= 1)]

            return {
                'name': _('Create Back Purchase Request'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'res_model': 'back.purchase.request',
                'target': 'new',
                'context': {
                    'default_pr_id': self.id,
                    'default_employee_id': self.employee_id.id,
                    'default_department_id': self.department_id.id,
                    'default_request_responsible': self.request_responsible.id,
                    'default_request_date': self.request_date,
                    'default_company_id': self.company_id.id,
                    'default_source_document': self.name,
                    'default_vehicle_id': self.vehicle_id,
                    'default_payment_term_id': self.payment_term_id,
                    'default_warehouse_id': self.warehouse_id,
                    'default_back_purchase_request_ids': wiz_lines,
                }
            }
    def create_rfq_ethics(self):
        # NUEVO: Validar productos sin proveedor ANTES de continuar
        lines_without_vendor = self.pr_lines.filtered(lambda l: not l.vendor_ids and l.product_id)
        if lines_without_vendor:
            # Construir mensaje de advertencia detallado
            missing_products = []
            for line in lines_without_vendor:
                missing_products.append(f"• {line.product_id.name} (Cant: {line.product_qty} {line.product_uom.name})")
            
            # Lanzar error con lista de productos
            raise ValidationError(_(
                "⚠️ ADVERTENCIA: Existen productos sin proveedor asignado:\n\n"
                "%s\n\n"
                "Por favor, asigne proveedores a estos productos antes de aprobar la solicitud.\n"
                "Puede hacerlo desde el botón 'Editar' en cada línea de producto."
            ) % '\n'.join(missing_products))
        
        # PROTECCIÓN: Validar y preservar picking_type_id antes de crear órdenes de compra
        if not self._validate_picking_type():
            # Si el picking_type no es válido, intentar recuperar el correcto
            if self.warehouse_id:
                suggested_picking_type = self._get_picking_type_for_warehouse(self.warehouse_id)
                if suggested_picking_type:
                    _logger.warning(
                        "PR %s: Corrigiendo picking_type_id de %s a %s para warehouse %s",
                        self.name, 
                        self.picking_type_id.name if self.picking_type_id else 'None',
                        suggested_picking_type.name,
                        self.warehouse_id.name
                    )
                    self.picking_type_id = suggested_picking_type
                else:
                    raise ValidationError(_(
                        "No se puede crear órdenes de compra: No hay un tipo de operación "
                        "de recepción válido para el almacén '%s'. "
                        "Por favor configure correctamente los tipos de operación."
                    ) % self.warehouse_id.name)
            else:
                raise ValidationError(_(
                    "No se puede crear órdenes de compra: No hay almacén seleccionado "
                    "y no se puede determinar el tipo de operación de recepción."
                ))
        
        # Log información sobre el proceso
        _logger.info(
            "PR %s: Creando órdenes de compra con picking_type_id=%s para warehouse=%s",
            self.name,
            self.picking_type_id.name if self.picking_type_id else 'None',
            self.warehouse_id.name if self.warehouse_id else 'None'
        )
        
        purchase_dict = {}
        purchase_orders = []
        for line in self.pr_lines.filtered(lambda l:l.vendor_ids):
            print("----------------line.vendor_ids----------",line.vendor_ids)
            for vendor in line.vendor_ids:
                print("=======IF==not vendor===purchase_dict====")
                if vendor not in purchase_dict:
                    print("=======IF not=====purchase_dict====",vendor,purchase_dict)
                    purchase_dict.update({vendor: []})
                if purchase_dict:
                    print("=======IF=====purchase_dict====",purchase_dict)
                    purchase_dict[vendor].append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.name if line.display_type else line.product_id.name, 
                        'product_qty': line.product_qty, 
                        'product_uom': line.product_uom.id, 
                        'price_unit': 0.0, 
                        'display_type': line.display_type or False, 
                        'vehicle_id': line.vehicle_id.id if line.vehicle_id else False,
                        'account_analytic_id': line.account_analytic_id.id if line.account_analytic_id else False,
                        'analytic_distribution': {str(line.account_analytic_id.id): 100.0} if line.account_analytic_id else {},
                        'phase_id': line.phase_id.id if line.phase_id else False,
                        'date_planned': fields.Date.today(),
                        'sequence': line.sequence,
                    }))
        for vendor,lines in purchase_dict.items():
            purchase_id = self.env['purchase.order'].create({
                'partner_id': vendor.id,
                'pr_ref_id': self.id,
                'vehicle_id': self.vehicle_id.id,
                'payment_term_id': self.payment_term_id.id,
                'account_analytic_id': self.account_analytic_id.id,
                'picking_type_id': self.picking_type_id.id,
                'order_line': lines,
                })
            purchase_orders.append(purchase_id.id)
        self.update({'purchase_ids': [(6, 0, purchase_orders)]})
        self.state = 'confirm'
        return True

    @api.onchange('warehouse_id')
    def _onchange_warehouse(self):
        if self.warehouse_id:
            self.sequence_alter = self._get_sequence(self.warehouse_id.id)
            # Cambia Cuenta Analitica
            self.account_analytic_id = self.warehouse_id.account_analytic_id
            # Cambiar picking_type_id - Recepcion
            # Buscar el almacén seleccionado actual
            _warehouse = self.warehouse_id
            if not _warehouse:
                # Si no hay almacén predeterminado para el usuario, usa el primero disponible
                _warehouse = self.env['stock.warehouse'].search(
                    [('company_id', '=', self.env.company.id)], 
                    limit=1
                )
            # Buscar el tipo de operación 'incoming' relacionado con el almacén
            # Solo actualizar picking_type_id si no está establecido o si es diferente almacén
            if not self.picking_type_id or (self.picking_type_id.warehouse_id != _warehouse):
                suggested_picking_type = self._get_picking_type_for_warehouse(_warehouse)
                if suggested_picking_type:
                    self.picking_type_id = suggested_picking_type

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        """
        Validar que el picking_type_id sea compatible con el warehouse_id seleccionado.
        Evitar sobreescrituras no deseadas durante flujos de aprobación.
        """
        if self.picking_type_id and self.warehouse_id:
            if not self._validate_picking_type():
                return {
                    'warning': {
                        'title': _('Tipo de Operación Incompatible'),
                        'message': _(
                            'El tipo de operación "%s" no pertenece al almacén "%s". '
                            'Por favor seleccione un tipo de operación válido.'
                        ) % (self.picking_type_id.name, self.warehouse_id.name)
                    }
                }

    def _validate_picking_type(self):
        """
        Validar que el picking_type_id pertenezca al warehouse_id actual
        y sea del tipo 'incoming' (recepción).
        
        Returns:
            bool: True si es válido, False en caso contrario
        """
        if not self.picking_type_id or not self.warehouse_id:
            return True
            
        # Verificar que el picking_type pertenezca al warehouse actual
        if self.picking_type_id.warehouse_id != self.warehouse_id:
            _logger.warning(
                "PR %s: picking_type_id %s no pertenece al warehouse %s", 
                self.name, self.picking_type_id.name, self.warehouse_id.name
            )
            return False
            
        # Verificar que sea de tipo 'incoming' 
        if self.picking_type_id.code != 'incoming':
            _logger.warning(
                "PR %s: picking_type_id %s no es de tipo 'incoming'", 
                self.name, self.picking_type_id.name
            )
            return False
            
        return True

    def _get_picking_type_for_warehouse(self, warehouse):
        """
        Obtener el picking_type_id apropiado para un almacén dado.
        Implementa lógica de fallback robusta.
        
        Args:
            warehouse (stock.warehouse): El almacén para el cual obtener el tipo de operación
            
        Returns:
            stock.picking.type: El tipo de operación de recepción o None si no se encuentra
        """
        if not warehouse:
            return None
            
        # Buscar primero el tipo de operación 'incoming' específico del almacén
        picking_type = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', warehouse.id),
            ('code', '=', 'incoming')
        ], limit=1)
        
        if picking_type:
            _logger.info(
                "PR: Encontrado picking_type %s para warehouse %s", 
                picking_type.name, warehouse.name
            )
            return picking_type
            
        # Fallback: Si no se encuentra, intentar con el tipo por defecto de la compañía
        _logger.warning(
            "PR: No se encontró picking_type 'incoming' para warehouse %s, "
            "buscando alternativas", warehouse.name
        )
        
        # Buscar cualquier tipo de recepción en la misma compañía
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id.company_id', '=', warehouse.company_id.id)
        ], limit=1)
        
        if picking_type:
            _logger.warning(
                "PR: Usando picking_type %s como fallback para warehouse %s", 
                picking_type.name, warehouse.name
            )
            return picking_type
            
        _logger.error(
            "PR: No se pudo encontrar ningún picking_type 'incoming' para warehouse %s", 
            warehouse.name
        )
        return None

    @api.model
    def create(self, vals):
        if vals.get('warehouse_id'):
            #vals['warehouse_id'] = self.warehouse_id.id
            vals['sequence_alter'] = self._get_sequence(vals['warehouse_id'])
        return super(EthicsPurchaseRequest, self).create(vals)

    def write(self, vals):
        # TRACK CHANGES: Capturar valores anteriores para registrar cambios en chatter
        changes_to_track = {}
        
        # Capturar cambios de picking_type_id (Tipo de Operación)
        if 'picking_type_id' in vals:
            for record in self:
                old_picking_type = record.picking_type_id
                new_picking_type = self.env['stock.picking.type'].browse(vals['picking_type_id']) if vals['picking_type_id'] else False
                
                if old_picking_type != new_picking_type:
                    changes_to_track.setdefault(record.id, {})['picking_type_id'] = {
                        'old': old_picking_type.name if old_picking_type else _('Sin asignar'),
                        'new': new_picking_type.name if new_picking_type else _('Sin asignar'),
                        'old_warehouse': old_picking_type.warehouse_id.name if old_picking_type and old_picking_type.warehouse_id else _('N/A'),
                        'new_warehouse': new_picking_type.warehouse_id.name if new_picking_type and new_picking_type.warehouse_id else _('N/A')
                    }
        
        # Capturar cambios de account_analytic_id (Cuenta Analítica)
        if 'account_analytic_id' in vals:
            for record in self:
                old_analytic = record.account_analytic_id
                new_analytic = self.env['account.analytic.account'].browse(vals['account_analytic_id']) if vals['account_analytic_id'] else False
                
                if old_analytic != new_analytic:
                    changes_to_track.setdefault(record.id, {})['account_analytic_id'] = {
                        'old': old_analytic.name if old_analytic else _('Sin asignar'),
                        'new': new_analytic.name if new_analytic else _('Sin asignar')
                    }
        
        if 'warehouse_id' in vals:
            vals['sequence_alter'] = self._get_sequence(vals['warehouse_id'])
        
        # Ejecutar write original
        result = super(EthicsPurchaseRequest, self).write(vals)
        
        # CHATTER LOGGING: Registrar cambios en la bitácora después del write exitoso
        for record_id, changes in changes_to_track.items():
            record = self.browse(record_id)
            messages = []
            
            # Mensaje para cambio de Tipo de Operación
            if 'picking_type_id' in changes:
                change = changes['picking_type_id']
                message = _(
                    "<strong>🔄 Tipo de Operación Modificado:</strong><br/>"
                    "• <strong>Anterior:</strong> %s (Almacén: %s)<br/>"
                    "• <strong>Nuevo:</strong> %s (Almacén: %s)<br/>"
                    "• <strong>Usuario:</strong> %s<br/>"
                    "• <strong>Motivo:</strong> Actualización manual del tipo de operación"
                ) % (
                    change['old'], change['old_warehouse'],
                    change['new'], change['new_warehouse'],
                    self.env.user.name
                )
                messages.append(message)
            
            # Mensaje para cambio de Cuenta Analítica  
            if 'account_analytic_id' in changes:
                change = changes['account_analytic_id']
                message = _(
                    "<strong>📊 Cuenta Analítica Modificada:</strong><br/>"
                    "• <strong>Anterior:</strong> %s<br/>"
                    "• <strong>Nueva:</strong> %s<br/>"
                    "• <strong>Usuario:</strong> %s<br/>"
                    "• <strong>Motivo:</strong> Actualización manual de la cuenta analítica"
                ) % (
                    change['old'], change['new'],
                    self.env.user.name
                )
                messages.append(message)
            
            # Publicar mensajes en el chatter
            if messages:
                combined_message = '<br/><br/>'.join(messages)
                record.message_post(
                    body=combined_message,
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
                
                # Log adicional para debugging
                _logger.info(
                    "PR %s: Cambios registrados en chatter por usuario %s: %s",
                    record.name, self.env.user.name, list(changes.keys())
                )
        
        return result

    def _get_sequence(self, warehouse_id):
        # Método para obtener la secuencia basada en el almacén
        warehouse = self.env['stock.warehouse'].browse(warehouse_id)
        cr = self.env.cr
        if warehouse.code:
            # Si el almacén tiene código
            cadena_sql = """SELECT MAX(sequence_alter) FROM public.purchase_request
                            WHERE LENGTH(substring(sequence_alter from 1 for %(len)s)) = 1
                            AND substring(sequence_alter from 1 for %(len)s) = %(code)s;"""
            cr.execute(cadena_sql, {'len': len(warehouse.code), 'code': warehouse.code})
            result = cr.fetchone()
            import re
            if result and result[0] is not None:
                # Buscar la porción numérica después del código
                match = re.search(f'{re.escape(warehouse.code)}(\\d+)', result[0])
                if match:
                    numeric_part = match.group(1)  # Extrae la porción numérica
                # Incrementar la secuencia o realizar el ajuste necesario aquí
                # Por ejemplo, si la secuencia es un número, podrías intentar extraer la parte numérica y incrementarla
                # Asegúrate de ajustar esta parte según cómo necesitas que funcione la secuencia.
                next_sequence = str(int(numeric_part) + 1).zfill(5)
                sequence = f"{warehouse.code}{next_sequence}"
            else:
                # Definir una secuencia inicial o manejar el caso de no resultado
                sequence = f"{warehouse.code}00001"  # Asumiendo que quieres empezar desde aquí
        else:
            # No tiene código el almacén
            sequence = None
        return sequence
    
    def action_submit_for_verifier_jc(self):
        super(EthicsPurchaseRequest, self).action_submit_for_verifier()
        self.message_post(
            body=_('SdC: ' + self.name + ' enviada a Verificación.')
        )
    
    def reject_verifier_pr_jc(self):
        super(EthicsPurchaseRequest, self).reject_verifier_pr()
        self.message_post(
            body=_('SdC: ' + self.name + ' RECHAZADA en la Verificación. - Para mayor información consulte la notas internas o contacte con su Verificad@r')
        )

    # Accion: Enviar por Auditoria;  ENviar a Compras
    def action_submit_for_audit(self):
        self.state = 'waiting_for_buyer'        
        self.message_post(
            body=_('SdC: ' + self.name + ' se envió a Compras')
        )

    # Agregando campo de usuario actual para filtar los almacenes por usuario
    # 2025.04.05
    current_user_id = fields.Many2one('res.users', string='Usuario actual', compute='_compute_current_user', store=False)

    @api.depends()
    def _compute_current_user(self):
        for record in self:
            record.current_user_id = self.env.user
    # Agregando campo de almacenes no permitidos para filtar los almacenes por usuario
    # 2025.04.05
    unauthorized_warehouses = fields.Many2many('stock.warehouse', string='Almacenes no permitidos', compute='_compute_unauthorized_warehouses', store=False)

    @api.depends()
    def _compute_current_user(self):
        for record in self:
            record.current_user_id = self.env.user

    @api.depends()
    def _compute_unauthorized_warehouses(self):
        for record in self:
            record.unauthorized_warehouses = self.env.user.warehouse_ids
    
    @api.depends('warehouse_id', 'current_user_id.warehouse_ids')
    def _compute_mostrar_a_usuario(self):
        for record in self:
            if record.current_user_id and record.warehouse_id:
                record.mostrar_a_usuario = record.warehouse_id not in record.current_user_id.warehouse_ids
            else:
                record.mostrar_a_usuario = False

    mostrar_a_usuario = fields.Boolean(
        string='Mostrar a usuario', 
        compute='_compute_mostrar_a_usuario', 
        store=False
    )

    def action_descarted(self):
        """Método para marcar la solicitud como descartada.
        Disponible en estados 'draft' (Borrador), 'waiting_for_approver' (Pendiente) y 'confirm' (Aprobado).
        Solo para usuarios con permiso específico de Descartador de SdC.
        Valida que las Purchase Orders relacionadas estén canceladas o descartadas."""

        # Verificar que el usuario tenga permisos de Descartador
        if not self.env.user.has_group('jobcostphasecat.group_request_discarder'):
            raise UserError(_("Solo los usuarios con permiso 'Descartador de SdC' pueden descartar solicitudes. Contacte con Auditoría, Compras o Contabilidad."))

        # Verificar que el estado sea válido para descarte
        if self.state not in ['draft', 'waiting_for_approver', 'confirm']:
            raise UserError(_("Solo se pueden descartar solicitudes en estado 'Borrador', 'Pendiente de Aprobación' o 'Aprobado'."))

        # TEMPORAL: Comentado porque el campo 'request_id' no existe en purchase.order
        # TODO: Encontrar la relación correcta entre purchase.request y purchase.order
        # Por ahora, permitir descartar sin validar Purchase Orders relacionadas

        # related_pos = self.env['purchase.order'].search([
        #     ('request_id', '=', self.id)
        # ])
        #
        # # Si hay Purchase Orders relacionadas, validar que estén en estados permitidos
        # if related_pos:
        #     estados_permitidos = ['cancel', 'descarted']  # Cancelado o Descartado
        #     for po in related_pos:
        #         if po.state not in estados_permitidos:
        #             raise UserError(_(
        #                 "No se puede descartar esta solicitud. "
        #                 "La Purchase Order %s está en estado '%s'. "
        #                 "Todas las Purchase Orders relacionadas deben estar Canceladas o Descartadas."
        #             ) % (po.name, po.state))

        # Guardar estado anterior antes de cambiar (con soporte para draft)
        estados_nombres = {
            'draft': 'Borrador',
            'waiting_for_approver': 'Pendiente de Aprobación',
            'confirm': 'Aprobado'
        }
        estado_anterior = estados_nombres.get(self.state, self.state)

        # Cambiar estado a descartado
        self.state = 'descarted'

        # Registrar actividad en el chatter con información del estado anterior
        self.message_post(
            body=_('🗑️ SdC: %s ha sido DESCARTADA por %s (Estado anterior: %s)') % (
                self.name,
                self.env.user.name,
                estado_anterior
            )
        )

        # Log para auditoria
        _logger.info(f"Purchase Request {self.name} discarded by user {self.env.user.login} from state {self.state}")

    def action_submit_for_approver(self):
        """
        Sobreescribir método para enviar SdC a aprobación con validación de proveedores.
        Validación solicitada: No permitir avanzar si existen productos sin proveedor.
        Estado: waiting_for_buyer -> waiting_for_approver
        """
        # VALIDACIÓN: Verificar que todos los productos tienen al menos un proveedor
        lines_without_vendor = self.pr_lines.filtered(lambda l: not l.vendor_ids and l.product_id)
        if lines_without_vendor:
            # Construir mensaje de advertencia detallado
            missing_products = []
            for line in lines_without_vendor:
                missing_products.append(f"• {line.product_id.name} (Cant: {line.product_qty} {line.product_uom.name})")
            
            # Lanzar error con lista de productos
            raise ValidationError(_(
                "⚠️ ADVERTENCIA: No se puede enviar a aprobación.\n\n"
                "Existen productos sin proveedor asignado:\n\n"
                "%s\n\n"
                "Por favor, asigne proveedores a estos productos antes de continuar con la aprobación."
            ) % '\n'.join(missing_products))
        
        # Si pasa la validación, continuar con el flujo normal
        self.state = 'waiting_for_approver'
        
        # Mensaje informativo en chatter
        self.message_post(
            body=_('✅ SdC enviada a aprobación. Todos los productos tienen proveedores asignados.')
        )
        
        _logger.info(f"Purchase Request {self.name} sent to approver by {self.env.user.login} - All products have vendors")

class EthicsPuchasRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    vehicle_id = fields.Many2one('fleet.vehicle.data',
                                string='Vehículo',
                                index='btree_not_null',
                                domain=[],
                                tracking=True)

    account_analytic_id = fields.Many2one('account.analytic.account',
                                            readonly=False,
                                            string='Cuenta Analítica',
                                            default=lambda self: self._default_aaid(), tracking=True)
    product_qty = fields.Float('Quantity', default=1, tracking=True)
    product_uom = fields.Many2one('uom.uom', related='product_id.uom_po_id', tracking=True,
        help="This comes from the product form.")
    vendor_ids = fields.Many2many('res.partner', tracking=True)
    # 2025.01.29: Agregando campo de Fase
    phase_id = fields.Many2one("project.phaseproject",
                               string="Fase",
                               tracking=True,
                               domain="[('account_analytic_id', '=', account_analytic_id)]")

    # 2025.02.17: Agregando funcionalidad de Secciones y Notas a la SdC
    name = fields.Text(string='Descripción', required=True, store=True, readonly=False, tracking=True, default="New Product")

    def _default_vehicle_id(self):
        user_id = self.env.user.id
        nombre_clave = 'vehicle_id'
        modelo_usado = 'purchase.request'

        # Llamada a la función
        valor_clave = self.env['valores.defaults'].buscar_y_devolver_valor_clave(user_id, nombre_clave, modelo_usado)
        if valor_clave:
            print("Valor de clave encontrado:", valor_clave)
        else:
            print("No se encontró un registro con los criterios especificados.")
            valor_clave = 0
        return int(valor_clave)
    
    def _default_aaid(self):
        # First check if there's a parent record with an analytic account
        if self.pr_id and self.pr_id.account_analytic_id:
            return self.pr_id.account_analytic_id.id
        
        # If no parent account, try to get the default from previous values
        user_id = self.env.user.id
        nombre_clave = 'account_analytic_id'
        modelo_usado = 'purchase.request'

        # Llamada a la función
        valor_clave = self.env['valores.defaults'].buscar_y_devolver_valor_clave(user_id, nombre_clave, modelo_usado)
        if valor_clave:
            print("Valor de clave encontrado:", valor_clave)
            return int(valor_clave)
        
        # If no values found, return false
        return False
    
    # 2025,02,14: Agregando funcionalidad de Secciones y Notas a la SdC
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

    sequence = fields.Integer(string='Sequence', default=10)
    price_unit = fields.Float('Price Unit', digits='Product Price', tracking=True)
    price_subtotal = fields.Float('Subtotal', store=True, tracking=True)
    state = fields.Selection(
        related='pr_id.state',
        string='Estado',
        store=True,
        readonly=True
    )

    _sql_constraints = [
        ('accountable_required_fields',
            "CHECK(display_type IS NOT NULL OR (name IS NOT NULL))",
            "Missing required fields on accountable service order line."),
        ('non_accountable_null_fields',
            "CHECK(display_type IS NULL OR (name IS NOT NULL))",
            "Forbidden values on non-accountable service order line"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            display_type = values.get('display_type')
            
            if display_type in ['line_section', 'line_note']:
                # ✅ Si es sección o nota, asegurarse de que tenga un nombre
                if 'name' not in values or not values['name']:
                    values['name'] = "New Section" if display_type == 'line_section' else "New Note"
            # ❌ No sobrescribir `name` con False innecesariamente
            return super().create(vals_list)

    def write(self, values):
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(_("You cannot change the type of a service order line. Instead you should delete the current line and create a new line of the proper type."))
        return super().write(values)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id and not self.display_type:
            self.name = self.product_id.get_product_multiline_description_sale()

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.name = f"{self.product_id.name} ({self.partner_id.name})" if self.product_id and self.partner_id else self.name

    # 2025.04.28: Agregando campo de Fase requerida
    require_phase_id = fields.Boolean(
        string="¿Obligar fase?",
        compute="_compute_require_phase_id",
        store=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Validar después de creación
        if self.env['ir.config_parameter'].sudo()\
               .get_param('jobcostphasecat.require_phase_id','False').lower() == 'true':
            for rec in records:
                if not rec.phase_id:
                    raise UserError(_("Debe seleccionar la Fase antes de guardar."))
        return records

    def write(self, vals):
        res = super().write(vals)
        # Validar después de escritura
        if self.env['ir.config_parameter'].sudo()\
               .get_param('jobcostphasecat.require_phase_id','False').lower() == 'true':
            for rec in self:
                if not rec.phase_id:
                    raise UserError(_("Debe seleccionar la Fase antes de guardar."))
        return res
    # 2025.04.28

class BackEthicsPurchaseRequest(models.TransientModel):
    _inherit = 'back.purchase.request'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehículo', index='btree_not_null')

class BackEthicsPurchaseRequestLine(models.TransientModel):
    _inherit = 'back.purchase.request.line'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehículo', index='btree_not_null')

class PurchaseOrders(models.Model):
    _inherit = 'purchase.order'

    #vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', index='btree_not_null')
    vehicle_id = fields.Many2one('fleet.vehicle.data', string='Vehículo', tracking=True)
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', tracking=True)
    account_analytic_id = fields.Many2one('account.analytic.account', readonly=False, string='Cuenta Analítica')
    # Extendiendo el campo 'state' para agregar el nuevos estados
    state = fields.Selection(selection_add=[('waiting_for_price_revision', 'Esperando Revisión Precios'),
                                            ('waiting_for_price_approval','Esperando Aprobación Precios'),
                                            ('waiting_for_approval','Esperando Aprobación'),
                                            ('to approve','Por Aprobar @ Compras'),
                                            ('descarted','Descartado'),
                                            ('internal_transfer', 'Transferencia Interna')
        ], ondelete={'waiting_for_approval': 'cascade'})
    send_all_attachments = fields.Boolean(string='Enviar todos los adjuntos', default=False)

    # Boton Enviar P.O. por email
    def action_rfq_send_jc(self):
        super(PurchaseOrders, self).action_rfq_send()
        for rec in self:
            # 2025.01.27: Cambiar estado a 'done' antes de enviar el correo
            rec.state = 'done'
    ###############################################################################################
    def action_rfq_send(self):
        if self.send_all_attachments:
            '''
            This function opens a window to compose an email, with the edi purchase template message loaded by default
            '''
            self.ensure_one()
            ir_model_data = self.env['ir.model.data']
            try:
                if self.env.context.get('send_rfq', False):
                    template_id = ir_model_data._xmlid_lookup('purchase.email_template_edi_purchase')[2]
                else:
                    template_id = ir_model_data._xmlid_lookup('purchase.email_template_edi_purchase_done')[2]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
            except ValueError:
                compose_form_id = False
            
            # Retrieve all attachments related to the RFQ
            attachment_ids = self.env['ir.attachment'].search([
                ('res_model', '=', 'purchase.order'),
                ('res_id', '=', self.id)
            ]).ids
            
            _logger.info("Attachments found: %s", attachment_ids)  # Depuración
            
            ctx = dict(self.env.context or {})
            ctx.update({
                'default_model': 'purchase.order',
                'active_model': 'purchase.order',
                'active_id': self.ids[0],
                'default_res_id': self.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
                'default_attachment_ids': [(6, 0, attachment_ids)],  # Cambio aquí
            })

            # In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
            # object. Therefore, we pass the model description in the context, in the language in which
            # the template is rendered.
            lang = self.env.context.get('lang')
            if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
                template = self.env['mail.template'].browse(ctx['default_template_id'])
                if template and template.lang:
                    lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

            self = self.with_context(lang=lang)
            if self.state in ['draft', 'sent']:
                ctx['model_description'] = _('Request for Quotation')
                # Change the state of the purchase order to 'sent'
                if self.state == 'draft':
                    self.state = 'sent'
            else:
                ctx['model_description'] = _('Purchase Order')

            xmail = {
                'name': _('Compose Email for Purchase Order 02'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'view_id': compose_form_id if compose_form_id else False,
                'views': [(compose_form_id, 'form')] if compose_form_id else [],
                'target': 'new',
                'context': ctx,
                'attached_to_email': True,
                'attachment_ids': attachment_ids,
            }
            return xmail
        else:
            return super(PurchaseOrders, self).action_rfq_send()        
    # Botones en waiting_for_price_revision
    def action_waiting_for_price_revision(self):
        for rec in self:
            rec.state = 'waiting_for_price_revision'
    def action_waiting_for_price_revision_back(self):
        for rec in self:
            rec.state = 'draft'
    
    def reject_waiting_for_price_revision(self):
        for rec in self:
            rec.state = 'sent'

    # Botones en waiting_for_price_approval
    def action_waiting_for_price_approval(self):
        for reg in self.order_line:
            if reg.display_type:   # Ignorar líneas de título
                continue
            if reg.price_total == 0:
                raise ValidationError("El valor del precio unitario no puede ser 0.")
                return
        for rec in self:
            rec.state = 'waiting_for_price_approval'
    
    def reject_waiting_for_price_approval(self):
        for rec in self:
            rec.state = 'waiting_for_price_revision'
    
    # Botones en waiting_for_approval
    def action_waiting_for_approval(self):
        for rec in self:
            rec.state = 'waiting_for_approval'
    # Boton en envio a Aprobacion SdP por Compras
    def action_send_to_approve_purchase(self):
        for rec in self:
            rec.state = 'to approve'
    # Botón en envio a 
    
    # Boton Rechazar Aprobación de SdP = Rechazar Pedido
    def reject_waiting_for_approval(self):
        # Acciones personalizadas antes de llamar al método de la clase base
        for record in self:
            record.state = 'waiting_for_price_approval'
        # Llamada al método reject_purchase de la clase base usando super()
        super(PurchaseOrders, self).reject_purchase()
    
    def action_buttom_approve_jc(self):
        for record in self:
            #record.state = 'to approve'
            print('Estado actual: ', record.state)
        # Llamada al método reject_purchase de la clase base usando super()
        super(PurchaseOrders, self).action_button_approve()
    def button_approve(self):
        super(PurchaseOrders, self).button_approve()
        for rec in self:
            rec.state = 'purchase'
    
    def action_back(self):
        for rec in self:
            if rec.state != 'done':
                if rec.state == 'waiting_for_price_revision':
                    rec.state = 'draft' 
                if rec.state == 'waiting_for_price_approval':
                    rec.state = 'waiting_for_price_revision'
                if rec.state == 'waiting_for_approval':
                    rec.state = 'waiting_for_price_approval'
                if rec.state == 'to approve':
                    rec.state = 'waiting_for_approval'
                if rec.state == 'purchase':
                    rec.state = 'to approve'
                if rec.state == 'descarted':
                    if self.env.user.has_group('purchase.group_purchase_manager'):
                        rec.state = 'waiting_for_approval'
                    else:
                        raise ValidationError("Solo los administradores de compras pueden cambiar el estado de 'Descartado'.")
                    rec.state = 'waiting_for_approval'
                if rec.state == 'sent':
                    rec.state = 'draft'
            else:
                raise ValidationError("No se puede regresar un pedido ya confirmado.")


    # Botón Descartar Pedido (para Purchase Orders)
    def action_discard(self):
        for rec in self:
            rec.state = 'descarted'

    """# Botón Rechazar Pedido - Cual funiona bien?????????
    def reject_puchase(self):
        super(PurchaseOrders, self).reject_purchase()
        for rec in self:
            rec.state = 'waiting_for_price_approval'
    """
    
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    vehicle_id = fields.Many2one('fleet.vehicle.data', string='Vehículo', tracking=True)
    account_analytic_id = fields.Many2one('account.analytic.account', readonly=False, string='Cuenta Analítica')
    phase_id = fields.Many2one("project.phaseproject",
                               string="Fase",
                               tracking=True,
                               domain="[('account_analytic_id', '=', account_analytic_id)]")

class FleetVehicleData(models.Model):
    _name = 'fleet.vehicle.data'
    _description = 'Fleet Vehicle Data'
    _auto = False

    id = fields.Integer(string='Linea', readonly=True)
    vehicle_id = fields.Integer(string='Vehicle ID', readonly=True)
    name = fields.Char(string='Vehicle Name', readonly=True)
    license_plate = fields.Char(string='License Plate', readonly=True)

    @api.model
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW fleet_vehicle_data AS
            SELECT id AS id, id AS vehicle_id, name, license_plate
            FROM fleet_vehicle
        """
        try:
            self.env.cr.execute(query)
        except Exception as e:
            _logger.error('Error creating view fleet_vehicle_data: %s', e)