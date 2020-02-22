# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HRProject(models.Model):
    _inherit = 'project.task'

    internal = fields.Boolean('Internal')
    employee_id = fields.Many2one('hr.employee', string='Employee')

