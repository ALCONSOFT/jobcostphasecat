# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import contextlib
import hashlib
import io
import itertools
import logging
import mimetypes
import os
import re
import uuid

from collections import defaultdict
from PIL import Image

from odoo import api, fields, models, SUPERUSER_ID, tools, _
from odoo.exceptions import AccessError, ValidationError, UserError
from odoo.tools import config, human_size, ImageProcess, str2bool, consteq
from odoo.tools.mimetypes import guess_mimetype
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def check(self, mode, values=None):
        """ Modificación para permitir acceso a usuarios internos a adjuntos """
        if self.env.is_superuser():
            return True
        # Permitir acceso a usuarios internos a adjuntos        
        if self.env.user.has_group('jobcostphasecat.group_attachment_user'):
            return True

        # Mantener restricciones para usuarios externos
        if not self.env.is_admin() and not self.env.user._is_internal():
            raise AccessError(_("Disculpe! No tiene permiso para adjuntar a este documento.  Por favor solicite permisos al administrador. Usuario Adjuntador"))

        # Recopilar registros a verificar
        model_ids = defaultdict(set)
        if self:
            self.env['ir.attachment'].flush_model(['res_model', 'res_id', 'create_uid', 'public', 'res_field'])
            self._cr.execute(
                'SELECT res_model, res_id, create_uid, public, res_field FROM ir_attachment WHERE id IN %s',
                [tuple(self.ids)]
            )
            for res_model, res_id, create_uid, public, res_field in self._cr.fetchall():
                if public and mode == 'read':
                    continue
                if not self.env.is_system() and (res_field or (not res_id and create_uid != self.env.uid)):
                    raise AccessError(_("Disculpe! No tiene permiso para adjuntar a este documento.  Por favor solicite permisos al administrador. Usuario Adjuntador"))
                if not (res_model and res_id):
                    continue
                model_ids[res_model].add(res_id)

        if values and values.get('res_model') and values.get('res_id'):
            model_ids[values['res_model']].add(values['res_id'])

        # Verificar derechos de acceso en los modelos relacionados
        for res_model, res_ids in model_ids.items():
            if res_model not in self.env:
                continue
            records = self.env[res_model].browse(res_ids).exists()
            access_mode = 'write' if mode in ('create', 'unlink') else mode
            records.check_access_rights(access_mode)
            records.check_access_rule(access_mode)
