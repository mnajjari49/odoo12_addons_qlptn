# -*- coding: utf-8 -*-

from odoo import fields, api, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class Applicant(models.Model):
    _inherit = "hr.applicant"

    recruit_period = fields.Many2one('hr.recruitment.period', 'Recruitment period', compute='_get_recruit_period', store=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], string='Gender', default="male")
    birthday = fields.Date('Date of Birth')
    address = fields.Char('Address')
    qualification = fields.Char('Qualification')
    college = fields.Char('College')
    last_workplace = fields.Char('Last workplace')
    social_facebook = fields.Char('facebook')

    @api.depends('job_id')
    def _get_recruit_period(self):
        for record in self:
            if record.job_id and not record.emp_id:
                if record.job_id and record.job_id.periods:
                    if record.job_id.periods[-1].end_date or record.job_id.periods[-1].expected_recruitment == record.job_id.periods[-1].employees_num:
                        raise UserError(_('No recruitment currently opened for this job.'))
                    else:
                        record.recruit_period = record.job_id.periods[-1]
                else:
                    raise UserError(_('No recruitment currently opened for this job.'))

    def website_form_input_filter(self, request, values):
        if 'partner_name' in values:
            values.setdefault('name', values['partner_name'])
        return values

    @api.multi
    def archive_applicant(self):
        self.write({'active': False})
        template = self.env.ref('hr_recruitment.email_template_data_applicant_refuse')
        mail_values = template.generate_email(self.id)
        mail_values['email_from'] = self.env['ir.mail_server'].search([], limit=1).smtp_user  # Todo: check back later
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()

    @api.multi
    def write(self, vals):
        for record in self:
            if vals.get('description'):
                if 'g-recaptcha-response' in vals.get('description'):
                    template = self.env.ref('hr_recruitment.email_template_data_applicant_congratulations')
                    mail_values = template.generate_email(record.id)
                    mail_values['email_from'] = self.env['ir.mail_server'].search([], limit=1).smtp_user  # Todo: check back later
                    mail = self.env['mail.mail'].create(mail_values)
                    mail.send()
                    return
            else:
                return super(Applicant, record).write(vals)

    @api.multi
    def create_employee_from_applicant(self):
        """ Create an hr.employee from the hr.applicants """
        employee = False
        for applicant in self:
            contact_name = False
            if applicant.partner_id:
                address_id = applicant.partner_id.address_get(['contact'])['contact']
                contact_name = applicant.partner_id.name_get()[0][1]
            else:
                new_partner_id = self.env['res.partner'].create({
                    'is_company': False,
                    'name': applicant.partner_name,
                    'email': applicant.email_from,
                    'phone': applicant.partner_phone,
                    'mobile': applicant.partner_mobile
                })
                address_id = new_partner_id.address_get(['contact'])['contact']
            if applicant.job_id and (applicant.partner_name or contact_name):
                applicant.job_id.write({'no_of_hired_employee': applicant.job_id.no_of_hired_employee + 1})
                employee = self.env['hr.employee'].create({
                    'name': applicant.partner_name or contact_name,
                    'job_id': applicant.job_id.id,
                    'group_job': applicant.job_id.group_job.id,
                    # 'hr_point_kpi': applicant.job_id.point_kpi,
                    'hr_user_id': applicant.user_id.id,
                    'address_home_id': address_id,
                    'department_id': applicant.department_id.id or False,
                    'address_id': applicant.company_id and applicant.company_id.partner_id
                                  and applicant.company_id.partner_id.id or False,
                    'work_email': applicant.department_id and applicant.department_id.company_id
                                  and applicant.department_id.company_id.email or False,
                    'work_phone': applicant.department_id and applicant.department_id.company_id
                                  and applicant.department_id.company_id.phone or False})
                applicant.write({'emp_id': employee.id})
                applicant.job_id.message_post(
                    body=_(
                        'New Employee %s Hired') % applicant.partner_name if applicant.partner_name else applicant.name,
                    subtype="hr_recruitment.mt_job_applicant_hired")
            else:
                raise UserError(_('You must define an Applied Job and a Contact Name for this applicant.'))

        employee_action = self.env.ref('hr.open_view_employee_list')
        dict_act_window = employee_action.read([])[0]
        dict_act_window['context'] = {'form_view_initial_mode': 'edit'}
        dict_act_window['res_id'] = employee.id
        return dict_act_window