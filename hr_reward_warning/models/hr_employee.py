# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
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
from odoo.http import request

class HrAnnouncements(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def _announcement_count(self):
        for obj in self:
            announcement_ids = self.env['hr.announcement'].sudo().search([('is_announcement', '=', True),
                                                                          ('state', 'in', ('approved', 'done'))])
            total = len(announcement_ids)
            query ="""SELECT count(*) as count
                        FROM public.hr_announcement
                        Left Join hr_department_announcements on hr_department_announcements.announcement = hr_announcement.id
                        Where state in ('approved','done' ) and is_announcement = false and department = {0}""".format(obj.department_id.id if obj.department_id else 0)
            request._cr.execute(query)
            data = request._cr.dictfetchall()
            total += data[0]['count']
            query2 = """SELECT count(*) as count
                                    FROM public.hr_announcement
                                    Left Join hr_employee_announcements on hr_employee_announcements.announcement = hr_announcement.id
                                    Where state in ('approved','done' ) and is_announcement = false and employee = {0}""".format(obj.id)
            request._cr.execute(query2)
            data = request._cr.dictfetchall()
            total += data[0]['count']
            query3 = """SELECT count(*) as count
                                    FROM public.hr_announcement
                                    Left Join hr_job_position_announcements on hr_job_position_announcements.announcement = hr_announcement.id
                                    Where state in ('approved','done' ) and is_announcement = false and job_position = {0}""".format(obj.job_id.id if obj.job_id else 0)
            request._cr.execute(query3)
            data = request._cr.dictfetchall()
            total += data[0]['count']
            obj.announcement_count = total

    @api.multi
    def announcement_view(self):
        for obj in self:
            ann_obj = self.env['hr.announcement'].sudo().search([('is_announcement', '=', True),
                                                                 ('state', 'in', ('approved', 'done'))])
            ann_ids = []
            for each in ann_obj:
                ann_ids.append(each.id)
            query = """SELECT hr_announcement.id as id
                                    FROM public.hr_announcement
                                    Left Join hr_department_announcements on hr_department_announcements.announcement = hr_announcement.id
                                    Where state in ('approved','done' ) and is_announcement = false and department = {0}""".format(
                obj.department_id.id if obj.department_id else 0)
            request._cr.execute(query)
            data = request._cr.dictfetchall()
            for item in data:
                ann_ids.append(item.get('id'))
            query2 = """SELECT hr_announcement.id as id
                                                FROM public.hr_announcement
                                                Left Join hr_employee_announcements on hr_employee_announcements.announcement = hr_announcement.id
                                                Where state in ('approved','done' ) and is_announcement = false and employee = {0}""".format(
                obj.id)
            request._cr.execute(query2)
            data = request._cr.dictfetchall()
            for item in data:
                ann_ids.append(item.get('id'))
            query3 = """SELECT hr_announcement.id as id
                                                FROM public.hr_announcement
                                                Left Join hr_job_position_announcements on hr_job_position_announcements.announcement = hr_announcement.id
                                                Where state in ('approved','done' ) and is_announcement = false and job_position = {0}""".format(
                obj.job_id.id if obj.job_id else 0)
            request._cr.execute(query3)
            data = request._cr.dictfetchall()
            for item in data:
                ann_ids.append(item.get('id'))

            view_id = self.env.ref('hr_reward_warning.view_hr_announcement_form').id
            if ann_ids:
                if len(ann_ids) > 1:
                    value = {
                        'domain': str([('id', 'in', ann_ids)]),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'hr.announcement',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name': _('Announcements'),
                        'res_id': ann_ids
                    }
                else:
                    value = {
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'hr.announcement',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Announcements'),
                        'res_id': ann_ids and ann_ids[0]
                    }
                return value

    announcement_count = fields.Integer(compute='_announcement_count', string='# Announcements')