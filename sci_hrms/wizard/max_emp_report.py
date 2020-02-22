# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date, timedelta
from calendar import monthrange


class RecruitmentPoint(models.TransientModel):
    _name = "sci.hr.max.emp.report"
    _description = 'Maximum employee report'

    type = fields.Selection([('current', 'Current'), ('at_date', 'Specific date')], default='current')
    at_date = fields.Date('Choose a date', default=date.today().replace(day=1, month=1))

    def open_report(self):
        form_view_id = self.env.ref('hr.view_hr_job_form').id
        if self.type == 'current':
            tree_view_id = self.env.ref('sci_hrms.hr_job_current_emp_tree_view').id
            return {
                    'type': 'ir.actions.act_window',
                    'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                    'view_mode': 'tree,form',
                    'name': _('Current employee report'),
                    'res_model': 'hr.job',
                    'context': dict(self.env.context, search_default_department=1, search_default_group_job=1),
                }
        else:
            tree_view_id = self.env.ref('sci_hrms.hr_job_history_emp_tree_view').id
            return {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Historical employee report'),
                'res_model': 'hr.job',
                'context': dict(self.env.context, employee_at_date=self.at_date, search_default_department=1, search_default_group_job=1),
            }
