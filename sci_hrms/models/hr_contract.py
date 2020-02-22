from odoo import fields, api, models, _
import datetime
from dateutil.relativedelta import relativedelta
from odoo.http import request
from odoo.exceptions import ValidationError
import pytz

def canh_bao_tang_luong(i):
    exp_date = i.salary_year + relativedelta(years=1)
    lst_email_follow = []
    if i.employee_id.parent_id:
        lst_email_follow.append(i.employee_id.parent_id.work_email)
    if i.job_id.user_id:
        lst_email_follow.append(i.job_id.user_id.email)
    if len(lst_email_follow) > 0:
        mail_content = "Kính gửi: <b>" + i.employee_id.parent_id.name + "</b><br/> Nhân sự bạn phụ trách quản lý:" + \
                       "<br/> -Họ vào tên: " + i.employee_id.name + "<br/> - Điện thoại: " + i.employee_id.work_phone + \
                       "<br/> - Email: " + i.employee_id.work_email
        if i.name:
            mail_content += "<br/> - Kiểu hợp đồng: " + str(i.name)
        if i.date_start:
            mail_content += "<br/> - Ngày bắt đầu: " + str(i.date_start.strftime('%d/%m/%Y'))
        if i.date_end:
            mail_content += "<br/> - Ngày kết thúc: " + str(i.date_end.strftime('%d/%m/%Y'))
        mail_content += "<br/> Đã sắp đến kỳ tăng lương vui lòng làm bảng đánh giá nhận tổng hợp những đóng góp trong quá trình làm việc." + \
                        "<br/>Trân trọng cám ơn!"
        main_content = {
            'subject': ('THÔNG BÁO NHÂN SỰ CHUẨN BỊ ĐẾN KỲ TĂNG LƯƠNG.'),
            'author_id': i.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': ",".join(lst_email_follow),
        }
        i.env['mail.mail'].create(main_content).send()
        i.write({
            'salary_year': exp_date
        })


def canh_bao_het_hop_dong(i):
    if i.employee_id.work_email:
        mail_employee = "Kính gửi: <b>" + i.employee_id.name + "</b>" + " <br/> Hợp đồng lao động của bạn đã sắp hết. Vui lòng liên hệ với quản lý trực tiếp của bạn để lấy mẫu đánh giá " + \
                        "quá trình làm việc.<br/>Trân trọng cám ơn!"
        main_employee = {
            'subject': ('SCI THÔNG BÁO - NHÂN SỰ HẾT HỢP ĐỒNG LAO ĐỘNG.'),
            'body_html': mail_employee,
            'email_to': ",".join([i.employee_id.work_email]),
        }
        i.env['mail.mail'].create(main_employee).send()

    if i.employee_id.parent_id:
        mail_parent = "Kính gửi: <b>" + i.employee_id.parent_id.name + "</b><br/> Nhân sự bạn quản lý:" + \
                      "<br/> - Họ vào tên: " + i.employee_id.name
        if i.employee_id.work_phone:
            mail_parent += "<br/> - Điện thoại: " + i.employee_id.work_phone
        if i.employee_id.work_email:
            mail_parent += "<br/> - Email: " + i.employee_id.work_email
        if i.name:
            mail_parent += "<br/> - Tên hợp đồng: " + str(i.name)
        if i.name:
            mail_parent += "<br/> - Loại hợp đồng: " + str(i.type_id.name)
        if i.date_start:
            mail_parent += "<br/> - Ngày bắt đầu: " + str(i.date_start.strftime('%d/%m/%Y'))
        if i.date_end:
            mail_parent += "<br/> - Ngày kết thúc: " + str(i.date_end.strftime('%d/%m/%Y'))
        mail_parent += "<br/> Đã sắp hết hạn hợp đồng lao động." \
                       "Vui lòng liên hệ với phòng Hành Chính Nhân Sự để lấy mẫu đánh giá quá trình làm việc. <br/>Trân trọng cám ơn!"
        main_parent = {
            'subject': ('SCI THÔNG BÁO - NHÂN SỰ BẠN QUẢN LÝ HẾT HỢP ĐỒNG LAO ĐỘNG.'),
            'body_html': mail_parent,
            'email_to': ",".join([i.employee_id.parent_id.work_email]),
        }
        i.env['mail.mail'].create(main_parent).send()

    if i.job_id.user_id:
        mail_hr = "Kính gửi: <b>" + i.job_id.user_id.name + "</b><br/> Nhân sự bạn phụ trách tuyển dụng:" + \
                  "<br/> - Họ vào tên: " + i.employee_id.name
        if i.employee_id.work_phone:
            mail_hr += "<br/> - Điện thoại: " + i.employee_id.work_phone
        if i.employee_id.work_email:
            mail_hr += "<br/> - Email: " + i.employee_id.work_email
        if i.name:
            mail_parent += "<br/> - Tên hợp đồng: " + str(i.name)
        if i.name:
            mail_parent += "<br/> - Loại hợp đồng: " + str(i.type_id.name)
        if i.date_start:
            mail_hr += "<br/> - Ngày bắt đầu: " + str(i.date_start.strftime('%d%m/%Y'))
        if i.date_end:
            mail_hr += "<br/> - Ngày kết thúc: " + str(i.date_end.strftime('%d%m/%Y'))
        mail_hr += "<br/> - Phòng ban: " + i.employee_id.department_id.name + \
                       "<br/> Đã sắp hết hạn hợp đồng lao động." \
                       "Vui lòng làm mẫu đánh giá quá trình làm việc gửi tới nhân sự. <br/>Trân trọng cám ơn!"
        main_hr = {
            'subject': ('SCI THÔNG BÁO - NHÂN SỰ BẠN PHỤ TRÁCH TUYỂN DỤNG HẾT HỢP ĐỒNG LAO ĐỘNG.'),
            'body_html': mail_hr,
            'email_to': ",".join([i.job_id.user_id.email]),
        }
        i.env['mail.mail'].create(main_hr).send()


DATETYPE = [('days', 'Ngày'), ('months', 'tháng'), ('years', 'năm')]
class HR_Contract(models.Model):
    _inherit = 'hr.contract'

    last_salary = fields.Date('Kỳ xét duyệt lần cuối', readonly="1")
    salary_deadline_type = fields.Selection(DATETYPE, 'Date Type', default="years", required=True,
                                            track_visibility="onchange")
    salary_deadline = fields.Integer('Thời hạn xét duyệt', size=3, track_visibility="onchange", default=1)
    salary_year = fields.Date(string="Ngày xét lương", compute="_compute_status")
    salary_status = fields.Text('Tình trạng', compute="_compute_status")
    type_id = fields.Many2one('hr.contract.type', string="Loại hợp đồng", required=True,
                              default=lambda self: self.env['hr.contract.type'].search([], limit=1))
    # added by Thanh
    basic_salary = fields.Monetary('Basic salary', digits=(16, 2), track_visibility="onchange")
    allowance = fields.Monetary('Allowance')
    KPI_salary = fields.Monetary('KPI salary')
    name = fields.Char(compute='_get_contract_name', store=True, default='New contract')
    decision_number = fields.Char('Decision number', readonly=True)

    @api.depends('salary_deadline', 'salary_deadline_type', 'date_start')
    def _compute_deadline_display(self):
        for record in self:
            if record.salary_deadline > 0 and record.salary_deadline_type:
                time_type = ''
                if record.salary_deadline_type == 'days':
                    time_type = _('days')
                elif record.salary_deadline_type == 'months':
                    time_type = _('months')
                elif record.salary_deadline_type == 'years':
                    time_type = _('years')
                record.salary_year = str(record.salary_deadline) + ' ' + time_type
            else:
                record.salary_year = _('Undefined')

    @api.depends('salary_deadline', 'salary_deadline_type', 'date_start', 'last_salary')
    def _compute_status(self):
        for record in self:
            maintenance_msg = ''
            if record.date_start:
                date_start = record.date_start
                if record.salary_deadline > 0 and record.salary_deadline_type:
                    if record.last_salary and record.last_salary > record.date_start:
                        date = datetime.datetime.strptime(record.last_salary, '%Y-%m-%d').date()
                    else:
                        date = date_start
                    deadine_salary = self.count_deadline(date, record.salary_deadline_type,
                                                              record.salary_deadline)
                    days = deadine_salary['days']
                    record.salary_year = deadine_salary['date']
                    if days < 0:
                        maintenance_msg += ('Quá hạn xét tăng lương {0} ngày').format(str(abs(days)))
                    elif days == 0:
                        maintenance_msg += ('Hôm nay là ngày xét tăng lương')
                    elif days < 15:
                        maintenance_msg += ('{0} ngày nữa là ngày xét tăng lương').format(str(abs(days)))
            record.salary_status = maintenance_msg

    def count_deadline(self, date, date_type, index):
        time = datetime.datetime.now()
        tz_current = pytz.timezone(self._context.get('tz') or 'UTC')  # get timezone user
        tz_database = pytz.timezone('UTC')
        time = tz_database.localize(time)
        time = time.astimezone(tz_current)
        time = time.date()
        if date_type == 'days':
            date += relativedelta(days=+index)
        elif date_type == 'months':
            date += relativedelta(months=+index)
        elif date_type == 'years':
            date += relativedelta(years=+index)
        days = (date - time).days
        return {'date': date, 'days': days}

    @api.multi
    def print_contract(self):
        contract_type_xml_id = self.type_id.get_external_id()[self.type_id.id]
        templates = self.env['temp.creation'].search([('reference', 'ilike', contract_type_xml_id.split('_')[-1])])
        if self.department_id:
            grant_parent_dept = self.department_id.root_parent
            grant_parent_dept_xml_id = grant_parent_dept.get_external_id()[grant_parent_dept.id]
            template = templates.filtered(lambda t: t.reference.split('-')[0] == grant_parent_dept_xml_id)
            if not template:
                template = templates.filtered(lambda t: t.reference.split('-')[0] == 'sci')
        else:
            template = templates.filtered(lambda t: t.reference.split('-')[0] == 'sci')
        if not template:
            raise ValidationError(_('Contract template not available, please contact your admin.'))
        return {'name': (_('Contract')),
                'type': 'ir.actions.act_window',
                'res_model': 'temp.wizard',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'inline',
                'view_id': self.env.ref('ms_templates.report_wizard').id,
                'context': {'default_template_id': template.id}}

    @api.depends('employee_id', 'type_id')
    def _get_contract_name(self):
        for record in self:
            str_name = ''
            if record.employee_id.employee_id:
                str_name = record.employee_id.employee_id
                if record.employee_id.name:
                    str_name += '-' + record.employee_id.name
                    if record.type_id:
                        str_name += '-' + record.type_id.name
            record.name = str_name

    @api.model
    def create(self, vals):
        res = super(HR_Contract, self).create(vals)
        res.decision_number = self.env['ir.sequence'].next_by_code('hr.decision.number')
        return res

    @api.model
    def update_salary_deadline(self):
        data = self.search([('state', 'in', ('open', 'pending'))])
        dt = datetime.datetime.now().date()
        for record in data:
            if record.date_end and record.date_end >= record.salary_year:
                s = record.salary_year + relativedelta(days=-10)
                if dt == s:
                    canh_bao_tang_luong(record)

            if record.date_end:
                ed = record.date_end + relativedelta(days=-10)
                if dt == ed:
                    canh_bao_het_hop_dong(record)
        return True
