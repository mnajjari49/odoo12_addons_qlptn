# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, exceptions
from random import randint
import datetime
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo import SUPERUSER_ID
from dateutil import tz
from odoo.http import request
import string
import random

import logging

_logger = logging.getLogger(__name__)


class WebsiteSupportTicket(models.Model):
    _name = "website.support.ticket"
    _description = "Website Support Ticket"
    _order = "create_date desc"
    _rec_name = "subject"
    _inherit = ['mail.thread']
    _translate = True

    @api.model
    def _read_group_state(self, states, domain, order):
        """ Read group customization in order to display all the states in the
            kanban view, even if they are empty
        """

        staff_replied_state = self.env['ir.model.data'].get_object('website_support',
                                                                   'website_ticket_state_staff_replied')
        customer_replied_state = self.env['ir.model.data'].get_object('website_support',
                                                                      'website_ticket_state_customer_replied')
        customer_closed = self.env['ir.model.data'].get_object('website_support',
                                                               'website_ticket_state_customer_closed')
        staff_closed = self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_staff_closed')

        exclude_states = [staff_replied_state.id, customer_replied_state.id, customer_closed.id, staff_closed.id]

        # state_ids = states._search([('id','not in',exclude_states)], order=order, access_rights_uid=SUPERUSER_ID)
        state_ids = states._search([], order=order, access_rights_uid=SUPERUSER_ID)

        return states.browse(state_ids)

    def get_code(self):
        size = 8
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))

    channel = fields.Selection([('website', 'Website'), ('email', 'Email'), ('phone', 'Phone'), ('other', 'Khác')],
                               string='Nguồn/Kênh')
    create_user_id = fields.Many2one('res.users', "Người tạo")
    priority_id = fields.Selection(
        [('0', 'Rất thấp'), ('1', 'Thấp'), ('2', 'Bình thường'), ('3', 'Cao'), ('4', 'Khẩn cấp')], string='Độ ưu tiên')
    parent_company_id = fields.Many2one(string="Công ty", related="partner_id.company_id")
    partner_id = fields.Many2one('res.partner', string="Nhân viên")
    category_id = fields.Many2one('vnitpro.maintenance.equipment.category', string='Bộ phận tiếp nhận')
    team_id = fields.Many2one('vnitpro.maintenance.team', string='Đội tiếp nhận',
                              domain="[('maintenance_category_id','=',category_id)]")
    user_id = fields.Many2one('hr.employee', 'Chịu trách nhiệm')
    person_name = fields.Char(string='Người gửi')
    email = fields.Char(string="Email")
    phone = fields.Char(string="Điện thoại")
    department = fields.Char(string="Phòng ban")
    support_email = fields.Char(string="Email hỗ trợ")
    subject = fields.Char(string="Chủ đề")
    description = fields.Text(string="Mô tả")
    conversation_history_ids = fields.One2many('website.support.ticket.message', 'ticket_id',
                                               string="Conversation History")
    attachment_ids = fields.One2many('vnitpro.base.attachment', 'support_ticket_id', 'Attachment Files')

    portal_access_key = fields.Char(string="Portal Access Key")
    ticket_number = fields.Char(string="Ticket Number", default=get_code)
    company_id = fields.Many2one('res.company', string="Company",
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'website.support.ticket'))
    request_id = fields.Many2one('vnitpro.maintenance.request', string="Tickets")
    support_rating = fields.Selection(
        [('1', 'Rất thấp'), ('2', 'Thấp'), ('3', 'Bình thường'), ('4', 'Tốt'), ('5', 'Rất tốt')], string='Đánh giá')
    support_comment = fields.Text(string="Support Comment")
    close_comment = fields.Html(string="Close Comment")
    close_time = fields.Datetime(string="Close Time")
    close_date = fields.Date(string="Close Date")
    closed_by_id = fields.Many2one('res.users', string="Closed By")
    time_to_close = fields.Integer(string="Time to close (seconds)")
    planned_time = fields.Datetime(string="Planned Time")
    planned_time_format = fields.Char(string="Planned Time Format", compute="_compute_planned_time_format")
    state_id = fields.Many2one('vnitpro.maintenance.stage', string="Trạng thái")
    approval_message = fields.Text(string="Approval Message")
    approve_url = fields.Char(compute="_compute_approve_url", string="Approve URL")
    disapprove_url = fields.Char(compute="_compute_disapprove_url", string="Disapprove URL")
    tag_ids = fields.Many2many('website.support.ticket.tag', string="Tags")
    body = fields.Text(string="Message Body")

    @api.one
    @api.depends('planned_time')
    def _compute_planned_time_format(self):

        # If it is assigned to the partner, use the partners timezone and date formatting
        if self.planned_time and self.partner_id and self.partner_id.lang:
            partner_language = self.env['res.lang'].search([('code', '=', self.partner_id.lang)])[0]

            # If we have timezone information translate the planned date to local time otherwise UTC
            if self.partner_id.tz:
                my_planned_time = self.planned_time.replace(tzinfo=tz.gettz('UTC'))
                local_time = my_planned_time.astimezone(tz.gettz(self.partner_id.tz))
                self.planned_time_format = local_time.strftime(
                    partner_language.date_format + " " + partner_language.time_format) + " " + self.partner_id.tz
            else:
                self.planned_time_format = self.planned_time.strftime(
                    partner_language.date_format + " " + partner_language.time_format) + " UTC"

        else:
            self.planned_time_format = self.planned_time

    @api.one
    def _compute_approve_url(self):
        self.approve_url = "/support/approve/" + str(self.id)

    @api.one
    def _compute_disapprove_url(self):
        self.disapprove_url = "/support/disapprove/" + str(self.id)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.person_name = self.partner_id.name
        self.email = self.partner_id.email
        self.phone = self.partner_id.phone

    @api.onchange('team_id')
    def _onchange_team_id(self):
        self.user_id = self.team_id.technician_user_id.id

    def message_new(self, msg, custom_values=None):
        """ Create new support ticket upon receiving new email"""

        defaults = {'support_email': msg.get('to'), 'subject': msg.get('subject')}

        # Extract the name from the from email if you can
        if "<" in msg.get('from') and ">" in msg.get('from'):
            start = msg.get('from').rindex("<") + 1
            end = msg.get('from').rindex(">", start)
            from_email = msg.get('from')[start:end]
            from_name = msg.get('from').split("<")[0].strip()
            defaults['person_name'] = from_name
        else:
            from_email = msg.get('from')

        defaults['email'] = from_email
        defaults['channel'] = "Email"

        # Try to find the partner using the from email
        search_partner = self.env['res.partner'].sudo().search([('email', '=', from_email)])
        if len(search_partner) > 0:
            defaults['partner_id'] = search_partner[0].id
            defaults['person_name'] = search_partner[0].name

        defaults['description'] = tools.html_sanitize(msg.get('body'))

        # Assign to default category
        setting_email_default_category_id = self.env['ir.default'].get('website.support.settings',
                                                                       'email_default_category_id')

        if setting_email_default_category_id:
            defaults['category_id'] = setting_email_default_category_id

        return super(WebsiteSupportTicket, self).message_new(msg, custom_values=defaults)

    def message_update(self, msg_dict, update_vals=None):
        """ Override to update the support ticket according to the email. """

        body_short = tools.html_sanitize(msg_dict['body'])

        # If the to email address is to the customer then it must be a staff member
        if msg_dict.get('to') == self.email:
            change_state = self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_staff_replied')
        else:
            change_state = self.env['ir.model.data'].get_object('website_support',
                                                                'website_ticket_state_customer_replied')

        self.state_id = change_state.id

        # Add to message history to keep HTML clean
        self.conversation_history_ids.create({'ticket_id': self.id, 'by': 'customer', 'content': body_short})

        return super(WebsiteSupportTicket, self).message_update(msg_dict, update_vals=update_vals)

    # @api.one
    # @api.depends('state_id')
    # def _compute_unattend(self):
    #
    #     if self.state_id.unattended == True:
    #         self.unattended = True

    @api.multi
    def request_approval(self):

        approval_email = self.env['ir.model.data'].get_object('website_support', 'support_ticket_approval')

        values = self.env['mail.compose.message'].generate_email_for_composer(approval_email.id, [self.id])[self.id]

        request_message = values['body']

        return {
            'name': "Request Approval",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'website.support.ticket.compose',
            'context': {'default_ticket_id': self.id, 'default_email': self.email, 'default_subject': self.subject,
                        'default_approval': True, 'default_body': request_message},
            'target': 'new'
        }

    @api.multi
    def open_close_ticket_wizard(self):

        return {
            'name': "Close Support Ticket",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'website.support.ticket.close',
            'context': {'default_ticket_id': self.id},
            'target': 'new'
        }

    def followers(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        body = ""
        if self.category_id.technician_user_id:
            body += "<p>Dear " + self.category_id.technician_user_id.name + ",</p>"
        body += "<p>Bạn vừa nhận được 1 yêu cầu hỗ trợ bảo trì/bảo dưỡng.</p>\
                      <p>Chi tiết yêu cầu: <a href='" + base_url + "/web#id=" + str(self.id) + "?model=website.support.ticket'>Click vào đây</a></p> <hr/>\
                      <b>Ticket Number:</b> " + self.ticket_number + "<br/>"
        if self.category_id:
            body += "<b>Bộ phận phụ trách:</b>" + self.category_id.name + "<br/>"
        if self.planned_time_format:
            body += "<b>Ngày gửi:</b>" + self.create_date + "<br/>"
        if self.person_name:
            body += "<b>:Người gửi</b>" + self.person_name + "<br/>"
        if self.department:
            body += "<b>:Phòng ban</b>" + self.department + "<br/>"
        if self.email:
            body += "<b>Email:</b>" + self.email + "<br/>"
        if self.phone:
            body += "<b>Phone:</b>" + self.phone + "<br/>"
        if self.description:
            body += "<b>Mô tả:</b>" + self.description
        lst_email = []
        if self.category_id.technician_user_id.work_email:
            lst_email.append(self.category_id.technician_user_id.work_email)
        if len(lst_email) > 0:
            main_employee = {
                'subject': ('SCI-Support: ' + self.subject),
                'body_html': body,
                'email_to': ",".join(lst_email),
            }
            self.env['mail.mail'].create(main_employee).send()

    @api.model
    def create(self, vals):
        # Get next ticket number from the sequence
        if not vals.get('ticket_number'):
            vals['ticket_number'] = WebsiteSupportTicket.get_code(self)

        vals['state_id'] = 1
        new_id = super(WebsiteSupportTicket, self).create(vals)

        new_id.portal_access_key = randint(1000000000, 2000000000)

        # Add them as a follower to the ticket so they are aware of any internal notes
        partner_ids = []
        for u in new_id.category_id.technician_user_id:
            partner_ids.append(u.id)
            WebsiteSupportTicket.followers(new_id)

        if new_id.user_id:
            support_ticket = request.env['vnitpro.maintenance.request'].sudo().search(
                [('code', '=', new_id.ticket_number)])
            if support_ticket:
                payload = {
                    'maintenance_team_id': new_id.team_id.id,
                    'user_id': new_id.user_id.id,
                }
                support_ticket.write(payload)
            else:
                payload = {
                    'name': new_id.subject,
                    'code': new_id.ticket_number,
                    'maintenance_type': 'corrective',
                    'ticket_id': [(4, new_id.id)],
                    'description': new_id.description,
                    'owner_user_id': new_id.env.uid,
                    'category_id': new_id.category_id.id if new_id.category_id else None,
                    'priority': new_id.priority_id,
                    'maintenance_team_id': new_id.team_id.id if new_id.team_id else None,
                    'user_id': new_id.user_id.id if new_id.user_id else None,
                    'request_date': new_id.create_date,
                    'schedule_date': datetime.datetime.now() + timedelta(hours=2),

                }
                req = self.env['vnitpro.maintenance.request'].create(payload)
                profile = {
                    'person_name': new_id.person_name,
                    'email': new_id.email,
                    'phone': new_id.phone,
                    'department': new_id.department,
                    'request_ids': req.id
                }
                self.env['vnitpro.maintenance.profile'].create(profile)
        return new_id

    @api.multi
    def write(self, values, context=None):
        update_rec = super(WebsiteSupportTicket, self).write(values)
        if values.get('user_id'):
            support_ticket = request.env['vnitpro.maintenance.request'].sudo().search(
                [('code', '=', self.ticket_number)])
            if support_ticket:
                payload = {
                    'maintenance_team_id': values.get('team_id'),
                    'user_id': values.get('user_id'),
                }
                support_ticket.write(payload)
            else:
                payload = {
                    'name': self.subject,
                    'code': self.ticket_number,
                    'ticket_id': [(4, self.id)],
                    'maintenance_type': 'corrective',
                    'description': self.description,
                    'owner_user_id': self.env.uid,
                    'category_id': self.category_id.id if self.category_id else None,
                    'priority': self.priority_id,
                    'maintenance_team_id': values.get('team_id'),
                    'user_id': values.get('user_id'),
                    'request_date': self.create_date,
                    'schedule_date': datetime.datetime.now() + timedelta(hours=2),
                }
                req = self.env['vnitpro.maintenance.request'].create(payload)
                profile = {
                    'person_name': self.person_name,
                    'email': self.email,
                    'phone': self.phone,
                    'department': self.department,
                    'request_ids': req.id
                }
                self.env['vnitpro.maintenance.profile'].create(profile)

        return update_rec

    def send_survey(self):
        notification_template = self.env['ir.model.data'].sudo().get_object('website_support', 'support_ticket_survey')
        values = notification_template.generate_email(self.id)
        send_mail = self.env['mail.mail'].create(values)
        send_mail.send(True)

    @api.one
    def send_reply(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        body = "{0}<hr/>"
        if self.portal_access_key:
            body += "<b>Chi tiết ticket:</b> <a href='" + base_url + "/support/portal/ticket/view/" + self.portal_access_key + ">Click vào đây</a><br/>"

        body += "<b>Ticket Number:</b>" + str(self.ticket_number) + "<br/>"
        if self.category_id:
            body += "<b>Bộ phận phụ trách:</b>" + self.category_id.name or '' + "<br/>"
        if self.planned_time_format:
            body += "<b>Ngày gửi:</b>" + self.create_date + "<br/>"
        if self.person_name:
            body += "<b>:Người gửi</b><br/>" + self.person_name
        if self.email:
            body += "<b>Email:</b><br/>" + self.email
        if self.description:
            body += "<b>Mô tả:</b><br/>" + self.description
        lst_email = []
        if self.team_id:
            lst_email.append(self.team_id.technician_user_id.email)
        if len(lst_email) > 0:
            main_employee = {
                'subject': ('SCI - ' + self.subject),
                'body_html': body,
                'email_to': ",".join(lst_email),
            }
            self.env['mail.mail'].create(main_employee).send()
        self.update({
            'team_id': self.team_id.id,
            'user_id': self.user_id.id,
        })

class BaseAttachment(models.Model):
    _inherit = "vnitpro.base.attachment"

    support_ticket_id = fields.Many2one(
        'website.support.ticket', 'Support ticket', ondelete="cascade")

class Maintenance(models.Model):
    _inherit = "vnitpro.maintenance.request"
    ticket_id = fields.One2many('website.support.ticket', 'request_id', string="Tickets",  readonly=True)
    attachment_ids = fields.One2many(string='Tệp đính kèm', related='ticket_id.attachment_ids', store=False)

class WebsiteSupportTicketApproval(models.Model):
    _inherit = "vnitpro.maintenance.stage"

    wst_id = fields.Many2one('website.support.ticket', string="Support Ticket")


class WebsiteSupportTicketMessage(models.Model):
    _name = "website.support.ticket.message"

    ticket_id = fields.Many2one('website.support.ticket', string='Ticket ID')
    by = fields.Selection([('staff', 'Staff'), ('customer', 'Customer')], string="By")
    content = fields.Html(string="Content")

    @api.model
    def create(self, values):

        new_record = super(WebsiteSupportTicketMessage, self).create(values)
        return new_record

class WebsiteSupportTicketTag(models.Model):
    _name = "website.support.ticket.tag"

    name = fields.Char(required=True, translate=True, string="Tag Name")

class WebsiteSupportTicketClose(models.TransientModel):
    _name = "website.support.ticket.close"

    ticket_id = fields.Many2one('website.support.ticket', string="Ticket ID")
    message = fields.Html(string="Close Message", required=True)

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            values = \
                self.env['mail.compose.message'].generate_email_for_composer(self.template_id.id, [self.ticket_id.id])[
                    self.ticket_id.id]
            self.message = values['body']

    def close_ticket(self):

        self.ticket_id.close_time = datetime.datetime.now()

        # Also set the date for gamification
        self.ticket_id.close_date = datetime.date.today()

        diff_time = self.ticket_id.close_time - self.ticket_id.create_date
        self.ticket_id.time_to_close = diff_time.seconds

        if self.ticket_id.state_id:
            message = "<ul class=\"o_mail_thread_message_tracking\">\n<li>State:<span> " + self.ticket_id.state_id.name + " </span><b>-></b> Nhân viên Closed </span></li></ul>"
        else:
            message = "<ul class=\"o_mail_thread_message_tracking\">\n<li><span> Nhân viên Closed </span></li></ul>"
        self.ticket_id.message_post(body=message, subject="Ticket Closed by Staff")

        self.ticket_id.close_comment = self.message
        self.ticket_id.closed_by_id = self.env.user.id

        self.ticket_id.sla_active = False
        ticket_state = self.env['vnitpro.maintenance.stage'].search([('code', '=', 'closed')], limit=1)
        if ticket_state:
            self.ticket_id.state_id = ticket_state.id

        # Auto send out survey
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        body = ""
        if self.ticket_id.person_name:
            body += "<p>Dear " + self.ticket_id.person_name + ",</p>"
        body += "<p>Chúng tôi muốn nhận được phản hồi của bạn về hỗ trợ</p>\
                <p><a href='" + base_url + "/support/survey/" + self.ticket_id.portal_access_key + "'>Click vào đây</a></p> <hr/>\
                <b>Ticket Number:</b> " + self.ticket_id.ticket_number + "<br/>"
        if self.ticket_id.category_id:
            body += "<b>Nhóm thiết bị:</b>" + self.ticket_id.category_id.name + "<br/>"
        if self.ticket_id.description:
            body += "<b>Mô tả:</b><br/>" + self.ticket_id.description
        lst_email = []
        if self.ticket_id.email:
            lst_email.append(self.ticket_id.email)
        if len(lst_email) > 0:
            main_employee = {
                'subject': ('SCI-Support: ' + self.ticket_id.subject),
                'body_html': body,
                'email_to': ",".join(lst_email),
            }
            self.env['mail.mail'].create(main_employee).send()