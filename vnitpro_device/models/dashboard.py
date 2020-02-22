# -*- coding: utf-8 -*-
###############################################################################
#
#    Công ty giải pháp phần mềm VNITPro.
#    Copyright (C) 2018-TODAY VNITPro(<http://vnitpro.vn>).
#    Create by MinhND - Developer of VNITPro
###############################################################################

from odoo import models, fields, api, _
import datetime
import logging

_logger = logging.getLogger(__name__)


class DepartmentDashboard(models.Model):
    _inherit = 'hr.department'

    main_device_ids = fields.One2many('vnitpro.device.main', 'department_id', 'Main Device List')
    count_main_device = fields.Integer('Count Main Device', compute="_compute_main_device")

    @api.one
    @api.depends('main_device_ids')
    def _compute_main_device(self):
        child_list = self.env['hr.department'].search([('parent_id', 'child_of', [self.id])])
        for item in child_list:
            self.count_main_device += len(item.main_device_ids)

    def get_main_device_in_department(self):
        action = self.env.ref('vnitpro_device.act_vnitpro_device_main_view').read()[0]
        if self:
            action['display_name'] = self.display_name
            action['context'] = {'search_default_department_id': self.id, 'default_department_id': self.id}
        return action