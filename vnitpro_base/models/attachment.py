# -*- coding: utf-8 -*-
###############################################################################
#
#    Công ty giải pháp phần mềm VNITPro.
#    Copyright (C) 2018-TODAY VNITPro(<http://vnitpro.vn>).
#    Created by: tam.pt
###############################################################################

from odoo import models, api, fields, _
import logging

_logger = logging.getLogger(__name__)


class BaseAttachment(models.Model):
    _name = 'vnitpro.base.attachment'
    _rec_name = "file_name"

    file = fields.Binary('Choose File', attachment=True, required=True)
    file_name = fields.Char('File name', readonly=True)
    description = fields.Text('Description', size=900, track_visibility="onchange")
    user_id = fields.Many2one('res.users', 'Upload Users', default=lambda self: self.env.user, store=True,
                              readonly=True)
    date = fields.Date('Attached date', default=lambda self: fields.Date.today(), readonly=True)

    def download_file(self):
        self.env.cr.execute('select id from ir_attachment where res_model = \'%s\' and res_id = %s'
                            % (self._name, self.id))
        return {
            "url": "/web/content/%s?download=true" % self.env.cr.fetchone()[0],
            "type": "ir.actions.act_url"
        }

    @api.model
    def create(self, vals):
        record = super(BaseAttachment, self).create(vals)
        if "file_name" in vals:
            self.env.cr.execute('update ir_attachment set datas_fname = \'%s\' where res_model = \'%s\' and res_id = %s'
                                % (vals["file_name"], record._name, record.id))
        return record

    @api.multi
    @api.onchange('file')
    def _onchange_file(self):
        for record in self:
            record.user_id = self.env.user
