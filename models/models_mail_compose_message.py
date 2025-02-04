from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo import Command

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _onchange_template_id(self, template_id, composition_mode, model, res_id):
        """
        Extiende el onchange de la plantilla para fusionar los adjuntos provenientes del contexto
        (default_attachment_ids) con los generados a partir de la plantilla.
        """
        # Recuperamos los adjuntos pasados en el contexto y nos aseguramos de que sean una lista de enteros.
        context_attachments = self.env.context.get('default_attachment_ids', [])
        if not isinstance(context_attachments, list):
            context_attachments = list(context_attachments)

        def flatten(lst):
            """ Función auxiliar para aplanar listas anidadas """
            flat = []
            for item in lst:
                if isinstance(item, list):
                    flat.extend(flatten(item))
                else:
                    flat.append(item)
            return flat

        context_attachments = flatten(context_attachments)

        if template_id and composition_mode == 'mass_mail':
            template = self.env['mail.template'].browse(template_id)
            values = {
                field: template[field]
                for field in ['subject', 'body_html', 'email_from', 'reply_to', 'mail_server_id']
                if template[field]
            }
            template_attachment_ids = template.attachment_ids.ids if template.attachment_ids else []
            merged_attachments = list(set(template_attachment_ids + context_attachments))
            # Se filtran los ceros (0) ya que no son IDs válidos
            merged_attachments = [x for x in merged_attachments if x]
            if merged_attachments:
                values['attachment_ids'] = [Command.set(merged_attachments)]
            if template.mail_server_id:
                values['mail_server_id'] = template.mail_server_id.id

        elif template_id:
            values = self.generate_email_for_composer(
                template_id, [res_id],
                ['subject', 'body_html', 'email_from', 'email_cc', 'email_to',
                 'partner_to', 'reply_to', 'attachment_ids', 'mail_server_id']
            )[res_id]
            # Procesa los adjuntos generados dinámicamente (campo 'attachments')
            new_attachment_ids = []
            Attachment = self.env['ir.attachment']
            for attach_fname, attach_datas in values.pop('attachments', []):
                data_attach = {
                    'name': attach_fname,
                    'datas': attach_datas,
                    'res_model': 'mail.compose.message',
                    'res_id': 0,
                    'type': 'binary',
                }
                new_attachment_ids.append(Attachment.create(data_attach).id)
            # Extrae los adjuntos que ya venían (pueden venir en forma de comando)
            existing_attachments = []
            raw_existing = values.get('attachment_ids', [])
            for cmd in raw_existing:
                if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == 6 and len(cmd) >= 3:
                    existing_attachments += cmd[2]
                elif isinstance(cmd, int):
                    existing_attachments.append(cmd)
            merged_attachments = list(set(existing_attachments + new_attachment_ids + context_attachments))
            merged_attachments = [x for x in merged_attachments if x]
            if merged_attachments:
                values['attachment_ids'] = [Command.set(merged_attachments)]

        else:
            default_values = self.with_context(
                default_composition_mode=composition_mode,
                default_model=model,
                default_res_id=res_id
            ).default_get([
                'composition_mode', 'model', 'res_id', 'parent_id',
                'subject', 'body', 'email_from', 'partner_ids', 'reply_to',
                'attachment_ids', 'mail_server_id'
            ])
            values = {
                key: default_values[key]
                for key in ['subject', 'body', 'email_from', 'partner_ids', 'reply_to', 'attachment_ids', 'mail_server_id']
                if key in default_values
            }
            raw_existing = values.get('attachment_ids', [])
            existing_attachments = []
            for cmd in raw_existing:
                if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == 6 and len(cmd) >= 3:
                    existing_attachments += cmd[2]
                elif isinstance(cmd, int):
                    existing_attachments.append(cmd)
            merged_attachments = list(set(existing_attachments + context_attachments))
            merged_attachments = [x for x in merged_attachments if x]
            if merged_attachments:
                values['attachment_ids'] = [Command.set(merged_attachments)]

        if values.get('body_html'):
            values['body'] = values.pop('body_html')

        # Convertimos los valores al formato de escritura; ahora, con los Command, el framework manejará
        # correctamente el campo many2many sin intentar acceder a atributos de un entero.
        values = self._convert_to_write(values)
        return {'value': values}

