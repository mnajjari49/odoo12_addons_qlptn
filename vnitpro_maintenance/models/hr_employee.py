# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Authors: Avinash Nk, Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import models, fields, api, _


class HrCustody(models.Model):
    _inherit = 'hr.employee'

    custody_count = fields.Integer(compute='_custody_count', string='# Custody')

    # count of all custody contracts
    @api.multi
    def _custody_count(self):
        for each in self:
            custody_ids = self.env['vnitpro.device.main'].search([('employee_id', '=', each.id)])
            each.custody_count = len(custody_ids)

    # smart button action for returning the view of all custody contracts related to the current employee
    @api.multi
    def custody_view(self):
        for each1 in self:
            value = {
                'domain': str([('employee_id', '=', each1.id)]),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'vnitpro.device.main',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'name': _('Vật tư/Thiết bị'),
                'context': {}
            }
            return value
