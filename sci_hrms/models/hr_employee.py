# -*- coding: utf-8 -*-

import logging
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, AccessError, Warning
import pytz
from odoo import fields, models, api, tools
from odoo.exceptions import UserError
from odoo.tools.translate import _

import requests

_logger = logging.getLogger(__name__)


class Employee(models.Model):
    _inherit = ['hr.employee']
    # trường được thêm
    employee_id = fields.Char('Employee ID')
    joining_date = fields.Date('Joining Date', default=datetime.now().date())
    work_duration = fields.Char('Seniority', compute='_get_work_duration')
    tz = fields.Selection('_tz_get', string='Timezone', required=True, default='Asia/Ho_Chi_Minh')
    hr_point_kpi = fields.Float('Điểm tuyển dụng', digits=(16, 1), compute='_get_hr_point_kpi')
    hr_user_id = fields.Many2one('res.users', "Responsible", track_visibility="onchange", default=lambda self: self.env.uid)
    applicants = fields.One2many('hr.applicant', 'emp_id', 'Applicant')
    resignations = fields.One2many('hr.resignation', 'employee_id', 'Resignation')
    group_job = fields.Many2one('hr.group.job', string='Bộ phận', help='Chọn bộ phận nhóm vị trí')
    contract_type = fields.Many2one('hr.contract.type', string="Loại hợp đồng")
    contract_date = fields.Date('Ngày hợp đồng')
    entry_checklist_domain = fields.Many2many('employee.checklist', string='Check list domain', compute='_get_checklist_domain')

    _sql_constraints = [
        ('employee_id_uniq', 'unique (employee_id)', 'Mã nhân viên đã tồn tại!'),
        ('employee_email_uniq', 'unique (work_email)', 'Email nhân viên đã tồn tại!')
    ]

    @api.one
    @api.depends('contract_type', 'contract_date')
    def _get_hr_contract(self):
        data_contract = self.env['hr.contract'].search([('employee_id', '=', self.id)], limit=1,order='write_date desc')
        for obj_contract in data_contract:
            self.contract_type = obj_contract.type_id.id
            self.contract_date = obj_contract.date_start

    @api.one
    @api.depends('job_id')
    def _get_checklist_domain(self):
        checklist = self.env['employee.checklist']
        if not self.job_id:
            self.entry_checklist_domain = checklist.search([('group_job_ids', '=', False)])
        else:
            self.entry_checklist_domain = checklist.search(['|', ('group_job_ids', 'in', [self.job_id.group_job.id]), ('group_job_ids', '=', False)])

    @api.multi
    def _get_entry_progress(self):
        for each in self:
            total_len = self.env['employee.checklist'].search_count([('id', 'in', each.entry_checklist_domain.ids), '|',
                 ('group_job_ids', 'in', [each.job_id.group_job.id]),
                 ('group_job_ids', '=', False)])
            document_ids = self.env['hr.employee.document'].sudo().search([('employee_ref', '=', each.id)])
            entry_len = len(document_ids)
            if total_len != 0:
                each.entry_progress = (entry_len * 100) / total_len

    @api.one
    @api.depends('applicants.job_id.point_kpi', 'resignations.type_reason.point_kpi')
    def _get_hr_point_kpi(self):
        self.hr_point_kpi = 0
        start_date = fields.Date.to_date(self.env.context.get('start_date'))
        end_date = fields.Date.to_date(self.env.context.get('end_date'))
        # Todo: Case of normal view without context, should be remove if not needed
        if not start_date or not end_date:
            if self.applicants:
                self.hr_point_kpi = self.applicants[0].job_id.point_kpi
                if self.resignations:
                    self.hr_point_kpi *= (1 - self.resignations[0].type_reason.point_kpi / 100)
        # View with context for start_date and end_date
        else:
            if self.applicants:
                if start_date < self.joining_date < end_date:
                    self.hr_point_kpi += self.applicants[0].job_id.point_kpi
                if self.resignations and self.resign_date and start_date < self.resign_date < end_date:
                    self.hr_point_kpi -= self.applicants[0].job_id.point_kpi * self.resignations[0].type_reason.point_kpi / 100

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(Employee, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        for line in res:
            employees = self.env['hr.employee']
            if '__domain' in line:
                employees = self.search(line['__domain'])
            if 'hr_point_kpi' in fields:
                line['hr_point_kpi'] = sum(employees.mapped('hr_point_kpi'))
        return res

    @api.model
    def _tz_get(self):
        return [(x, x) for x in pytz.all_timezones]

    @api.multi
    def sci_create(self):
        if not self.user_id:
            if not self.work_email:
                raise Warning(_('Please fill work email address before creating an account.'))
            else:
                user = self.env['res.users'].create({'name': self.name,
                                                     'image': self.image,
                                                     'login': self.work_email,
                                                     'email': self.work_email})
                self.user_id = user.id
        else:
            return {
                'name': 'User',  # Lable
                'res_id': self.user_id.id,
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('base.view_users_form').id,
                'res_model': 'res.users',  # your model
                'target': 'new',  # if you want popup
                # 'context': "{'generic_request_id': uid}",  # if you need
            }

    @api.multi
    def account_request(self):
        request_ticket = self.env['project.task'].search(
            [('project_id', '=', self.env.ref('sci_hrms.acc_request').id),
             ('employee_id', '=', self.id)])
        if not request_ticket:
            self.env['project.task'].create({'name': self.name,
                                             'project_id': self.env.ref('sci_hrms.acc_request').id,
                                             'type_id': self.env.ref('sci_hrms.acc_request_new').id,
                                             'internal': True,
                                             'employee_id': self.id,
                                             'user_id': self.env.ref('sci_hrms.acc_request').user_id.id,
                                             'create_uid': self.env.uid})
        else:
            return {
                'name': 'Account request',  # Lable
                'res_id': request_ticket.id,
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('project.view_task_form2').id,
                'res_model': 'project.task',  # your model
                # 'target': 'current',
                # 'context': "{'generic_request_id': uid}",  # if you need
            }


    @api.one
    @api.depends('joining_date', 'resign_date')
    def _get_work_duration(self):
        if self.resign_date:
            duration = relativedelta(self.resign_date, self.joining_date)
        else:
            duration = relativedelta(date.today(), self.joining_date)
        y = str(duration.years) + (' year', ' years')[duration.years > 1]
        m = str(duration.months) + (' month', ' months')[duration.months > 1]
        d = str(duration.days) + (' day', ' days')[duration.days > 1]
        self.work_duration = '%s %s %s' % (('', y)[duration.years > 0],
                                           ('', m)[duration.months > 0],
                                           ('', d)[duration.days > 0])

    @api.model
    def convert_emp_id_to_external_id(self, limit=2000):
        emps_external_id_data = self.env['ir.model.data'].search([('model', '=', 'hr.employee'), ('name', 'ilike', 'hr_employee_')], limit=limit)
        for data in emps_external_id_data:
            emp = self.env['hr.employee'].browse(data.res_id)
            if emp.employee_id:
                data.name = emp.employee_id

    @api.model
    def revamp_job_department(self):
        all_emps = self.env['hr.employee'].search([])
        for emp in all_emps:
            if emp.job_id and emp.department_id:
                if not emp.job_id.department_id:
                    emp.job_id.department_id = emp.department_id
                elif emp.job_id.department_id != emp.department_id:
                    alt_job = self.env['hr.job'].search([('name', '=', emp.job_id.name),
                                                         ('department_id', '=', emp.department_id.id)])
                    if not alt_job:
                        alt_job = self.env['hr.job'].create({'name': emp.job_id.name,
                                                            'department_id': emp.department_id.id})
                    emp.job_id = alt_job


class Department(models.Model):
    _inherit = ['hr.department']

    # 2 truong đếm số nhan vien va don vi cap duoi
    child_department_count = fields.Integer(string='child nums', compute='count_department', store=True)
    employee_count = fields.Integer(string='emp nums', compute='count_employee')
    address_location = fields.Text(string='Địa điểm')
    partner_latitude = fields.Float(string='Vĩ độ Địa lý', digits=(16, 5))
    partner_longitude = fields.Float(string='Kinh độ Địa lý', digits=(16, 5))
    root_parent = fields.Many2one('hr.department', string='Brand')

    @api.model
    def create(self, vals):
        res = super(Department, self).create(vals)
        if not res.parent_id:
            res.root_parent = res.id
        else:
            res.root_parent = self.env['hr.department'].search([('id', 'parent_of', res.id), ('parent_id', '=', False)], limit=1).id
        return res

    @api.multi
    def write(self, vals):
        res = super(Department, self).write(vals)
        if vals.get('parent_id'):
            for record in self:
                if not record.parent_id:
                    record.root_parent = record.id
                else:
                    record.root_parent = self.env['hr.department'].search([('id', 'parent_of', res.id), ('parent_id', '=', False)], limit=1).id
        return res

    # ham dem don vi cap duoi
    @api.one
    @api.depends('child_ids')
    def count_department(self):
        self.child_department_count = len(self.child_ids)

    # ham dem nhan vien trong don vi
    @api.one
    @api.depends('member_ids')
    def count_employee(self):
        child_list = self.env['hr.department'].search([('parent_id', 'child_of', [self.id])])
        for item in child_list:
            self.employee_count += len(item.member_ids)

    # button to link manager
    @api.multi
    def action_get_manager_view(self):
        if self.manager_id:
            return {
                'name': 'Manager',  # Lable
                'res_id': self.manager_id.id,
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr.employee',  # your model
                # 'target': 'new',  # if you want popup
                # 'context': ctx,  # if you need
            }
        else:
            return None

    @api.onchange('address_location')
    def _onchange_address_full(self):
        Department.geo_localize(self)

    def geo_find(addr, apikey=False):
        if not addr:
            return None

        if not apikey:
            raise UserError(_('''API key for GeoCoding (Places) required.\n
                              Save this key in System Parameters with key: google.api_key_geocode, value: <your api key>
                              Visit https://developers.google.com/maps/documentation/geocoding/get-api-key for more information.
                              '''))

        url = "https://maps.googleapis.com/maps/api/geocode/json"
        try:
            result = requests.get(url, params={'sensor': 'false', 'address': addr, 'key': apikey}).json()
        except Exception as e:
            raise UserError(_(
                'Cannot contact geolocation servers. Please make sure that your Internet connection is up and running (%s).') % e)

        if result['status'] != 'OK':
            if result.get('error_message'):
                _logger.error(result['error_message'])
                error_msg = _('Unable to geolocate, received the error:\n%s'
                              '\n\nGoogle made this a paid feature.\n'
                              'You should first enable billing on your Google account.\n'
                              'Then, go to Developer Console, and enable the APIs:\n'
                              'Geocoding, Maps Static, Maps Javascript.\n'
                              % result['error_message'])
                raise UserError(error_msg)

        try:
            geo = result['results'][0]['geometry']['location']
            return float(geo['lat']), float(geo['lng'])
        except (KeyError, ValueError):
            return None

    @classmethod
    def _geo_localize(cls, apikey, address_location):
        result = Department.geo_find(address_location, apikey)
        return result

    @api.multi
    def geo_localize(self):
        if self.address_location:
            # We need country names in English below
            apikey = self.env['ir.config_parameter'].sudo().get_param('google.api_key_geocode')
            result = self._geo_localize(apikey, self.address_location)
            if result:
                self.partner_latitude = result[0]
                self.partner_longitude = result[1]
        return True
    
    
class HRResignation(models.Model):
    _inherit = 'hr.resignation'
    
    brand = fields.Many2one('hr.department', 'Brand', related='employee_id.department_id.root_parent', store=True)
    work_duration = fields.Char('Seniority', related='employee_id.work_duration')