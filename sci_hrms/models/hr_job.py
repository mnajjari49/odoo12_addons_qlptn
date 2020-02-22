# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError, UserError

class JobWelfare(models.Model):
    _name = "hr.job.welfare"

    name = fields.Char("Name", required=True)
    color = fields.Integer(string='Color Index', default=10)

    _sql_constraints = [
            ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]

class HRJob(models.Model):
    _inherit = 'hr.job'
    address_location = fields.Text(string='Địa điểm làm việc')
    total_payroll = fields.Integer(string='Tổng định biên', default=1)
    point_kpi = fields.Float('Hệ số điểm', digits=(16, 1), default=1)
    group_job = fields.Many2one('hr.group.job', string='Bộ phận', help='Chọn bộ phận nhóm vị trí')
    categ_ids = fields.Many2many('hr.applicant.category', string="Job tags")
    welfare_ids = fields.Many2many('hr.job.welfare', string="Phúc lợi")
    date_open = fields.Date("Từ Ngày", default=fields.Date.today())
    date_closed = fields.Date("Đến Ngày")
    type_id = fields.Many2one('hr.recruitment.degree', "Bằng Cấp")
    experience = fields.Selection([('0', 'Chưa có kinh nghiệm'), ('1', 'Có kinh nghiệm'), ('2', 'Không yêu cầu kinh nghiệm')], default='1')
    experience_from = fields.Float("Years", digits=(16, 1))
    experience_to = fields.Float("Years", digits=(16, 1))
    salary_type = fields.Selection([('usd', 'USD'), ('vnd', 'VNĐ'), ('ltt', 'Lương thỏa thuận'), ('lct', 'Cạnh tranh')], default='vnd')
    salary_proposed = fields.Float("Proposed Salary", digits=(16, 0))
    salary_proposed_extra = fields.Float("Proposed Salary Extra", digits=(16, 0))
    job_industry = fields.Many2one('hr.industry.job', "Ngành nghề")
    hr_responsible_id = fields.Many2one('hr.employee', 'Quản lý')
    description = fields.Html(string='Job Description')
    req_job = fields.Html(string='Job requirements')

    state = fields.Selection(default='open', compute='_get_state', store=True)
    website_published = fields.Boolean(compute='_get_state')
    is_published = fields.Boolean(compute='_get_state', store=True)
    no_of_recruitment2 = fields.Integer(string='To recruit' ,compute='_get_no_of_recruitment', store=True)
    periods = fields.One2many('hr.recruitment.period', 'job_position', 'Recruitment history')

    # fields for reporting, should be remove if report template is made
    no_of_employee_at_time = fields.Integer('Employee at time', compute='_get_employee_moves')
    employees_in = fields.Integer('Employees move in', compute='_get_employee_moves')
    employees_out = fields.Integer('Employees move out', compute='_get_employee_moves')

    @api.onchange('department_id')
    def _onchange_department(self):
        self.hr_responsible_id = self.department_id.manager_id

    def _get_employee_moves(self):
        at_date = self.env.context.get('employee_at_date')
        for record in self:
            if at_date:
                record.employees_out = self.env['hr.resignation'].search_count([('expected_revealing_date', '>=', at_date), ('state', '=', 'approved'), ('job', '=', record.id)])
                record.employees_in = self.env['hr.employee'].search_count([('joining_date', '>=', at_date), ('job_id', '=', record.id)])
                record.no_of_employee_at_time = record.no_of_employee + record.employees_out - record.employees_in
            else:
                record.employees_in = 0
                record.employees_out = 0
                record.no_of_employee_at_time = record.no_of_employee

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(HRJob, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        for line in res:
            jobs = self.env['hr.job']
            if '__domain' in line:
                jobs = self.search(line['__domain'])
            if 'employees_in' in fields:
                line['employees_in'] = sum(jobs.mapped('employees_in'))
            if 'employees_out' in fields:
                line['employees_out'] = sum(jobs.mapped('employees_out'))
            if 'no_of_employee_at_time' in fields:
                line['no_of_employee_at_time'] = sum(jobs.mapped('no_of_employee_at_time'))
        return res

    @api.depends('periods', 'periods.end_date')
    def _get_state(self):
        # Todo: check back later with HR to see if they want to auto close recruitment or not
        for record in self:
            if not record.periods or (record.periods and record.periods[-1].end_date):
                record.state = 'open'
                record.website_published = False
                record.is_published = False
            else:
                record.state = 'recruit'
                record.website_published = True
                record.is_published = True

    @api.depends('no_of_employee', 'total_payroll')
    def _get_no_of_recruitment(self):
        for record in self:
            record.no_of_recruitment2 = record.total_payroll - record.no_of_employee

    @api.constrains('point_kpi')
    def _check_number(self):
        for record in self:
            number = record.point_kpi
            if number and number < 0:
                raise ValidationError('Hệ số điểm phải > 0')

    @api.onchange('department_id')
    def _onchange_address_full(self):
        if self.department_id:
            self.address_location = self.department_id.address_location

    def start_recruitment_period(self):
        self.ensure_one()
        if self.state == 'open':
            if self.no_of_employee >= self.total_payroll:
                raise UserError(_('Number of employees is at limit.'))
            if self.periods.filtered(lambda p: p.start_date == fields.date.today()):
                self.periods.filtered(lambda p: p.start_date == fields.date.today()).sudo().unlink()
            return {
                'name': _('Start recruitment'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr.recruitment.period',
                'view_id': self.env.ref('sci_hrms.hr_recruitment_period_popup').id,
                'target': 'new',
                'context': {'default_job_position': self.id},
            }

    @api.one
    def end_recruitment_period(self):
        for record in self:
            if record.state == 'recruit':
                record.write({'state': 'open',
                            'website_published': False})
                if record.periods and not record.periods[-1].end_date:
                    record.periods[-1].sudo().write({'end_date': fields.Date.today()})


class GroupJob(models.Model):
    _name = "hr.group.job"
    _description = "Nhóm vị trí"

    name = fields.Text(string="Bộ phận")


class IndustryJob(models.Model):
    _name = "hr.industry.job"
    _description = "Ngành nghề"

    name = fields.Text(string="Ngành nghề")


class EmployeeEntryDocuments(models.Model):
    _inherit = 'employee.checklist'

    group_job_ids = fields.Many2many('hr.group.job', string="Bộ phận")


class RecruitmentPeriod(models.Model):
    _name = "hr.recruitment.period"
    _description = 'Recruitment history'

    job_position = fields.Many2one('hr.job', 'Job position')
    department = fields.Many2one('hr.department', 'Department', related='job_position.department_id')
    start_date = fields.Date('Start date')
    end_date = fields.Date('End date', compute='_get_end_date', store=True)
    expected_recruitment = fields.Integer('Expected recruitment')
    applicants = fields.One2many('hr.applicant', 'recruit_period', 'Applicants', context={'active_test': False})
    applicants_num = fields.Integer('Number of applicants', compute='_get_nums', store=True)
    employees_num = fields.Integer('Hired employees', compute='_get_nums', store=True)
    success_rate = fields.Float('Success rate', compute='_get_nums', store=True, group_operator='avg')
    to_recruit = fields.Integer('To recruit')

    @api.multi
    def name_get(self):
        return [(record.id, record.job_position.name + ' - ' + record.start_date.strftime('%d/%m/%Y')) for record in self]

    @api.depends('applicants', 'applicants.emp_id')
    def _get_nums(self):
        for record in self:
            record.applicants_num = len(record.applicants)
            record.employees_num = len(record.applicants.filtered(lambda a: a.emp_id))
            record.success_rate = record.employees_num / record.applicants_num * 100 if record.applicants_num > 0 else 0

    @api.depends('employees_num', 'expected_recruitment')
    def _get_end_date(self):
        for record in self:
            if record.employees_num == record.expected_recruitment:
                record.end_date = fields.Date.today()
                # self.env['hr.job'].sudo().browse(self.job_position.id).write({'state': 'open'})
                # self.job_position.state = 'open'

    @api.constrains('expected_recruitment')
    def constrain_expected_recruitment(self):
        for record in self:
            if record.expected_recruitment > (record.job_position.total_payroll - record.job_position.no_of_employee):
                raise UserError(_("Expected recruitment excess limit."))

    @api.model
    def create(self, vals):
        if not vals.get('start_date'):
            vals['start_date'] = fields.Date.today()
        res = super(RecruitmentPeriod, self).create(vals)
        res.job_position.write({'state': 'recruit',
                               'website_published': True})
        return res

    @api.multi
    def action_save(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

