# -*- coding: utf-8 -*-

import datetime
from datetime import timedelta
import pytz
from odoo.http import request
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class MaintenanceStage(models.Model):
    """ Model for case stages. This models the main stages of a Maintenance Request management flow. """

    _name = 'vnitpro.maintenance.stage'
    _description = 'Maintenance Stage'
    _order = 'sequence, id'

    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=20)
    fold = fields.Boolean('Folded in Maintenance Pipe')
    done = fields.Boolean('Request Done')


class MaintenanceEquipmentCategory(models.Model):
    _name = 'vnitpro.maintenance.equipment.category'
    _description = 'Maintenance Equipment Category'

    name = fields.Char('Category Name', required=True, translate=True)
    technician_user_id = fields.Many2one('hr.employee', 'Chịu trách nhiệm')
    color = fields.Integer('Color Index')
    note = fields.Text('Comments', translate=True)

    equipment_ids = fields.One2many('vnitpro.device.main', 'category_id', string='Thiết bị')
    equipment_count = fields.Integer(string="Equipment", compute='_compute_equipment_count')
    maintenance_ids = fields.One2many('vnitpro.maintenance.request', 'category_id', copy=False)
    maintenance_count = fields.Integer(string="Maintenance Count", compute='_compute_maintenance_count')

    team_count = fields.Integer(compute='_compute_team_count')

    # count of all custody contracts
    @api.multi
    def _compute_team_count(self):
        for each in self:
            custody_ids = self.env['vnitpro.maintenance.team'].search([('maintenance_category_id', '=', each.id)])
            each.team_count = len(custody_ids)

    @api.multi
    def _compute_equipment_count(self):
        equipment_data = self.env['vnitpro.device.main'].read_group([('category_id', 'in', self.ids)], ['category_id'],['category_id'])
        mapped_data = dict([(m['category_id'][0], m['category_id_count']) for m in equipment_data])
        for category in self:
            category.equipment_count = mapped_data.get(category.id, 0)

    @api.multi
    def _compute_maintenance_count(self):
        maintenance_data = self.env['vnitpro.maintenance.request'].read_group([('category_id', 'in', self.ids)], ['category_id'],['category_id'])
        mapped_data = dict([(m['category_id'][0], m['category_id_count']) for m in maintenance_data])
        for category in self:
            category.maintenance_count = mapped_data.get(category.id, 0)


class MaintenanceEquipment(models.Model):
    _inherit = 'vnitpro.device.main'

    category_id = fields.Many2one('vnitpro.maintenance.equipment.category', 'BP quản lý/bảo trì', required=True)
    maintenance_ids = fields.One2many('vnitpro.maintenance.request', 'equipment_id')
    maintenance_count = fields.Integer(compute='_compute_maintenance_count', string="Tổng số yêu cầu sửa chữa")
    certificate_count = fields.Integer(compute='_compute_maintenance_count', string="Tổng số bảo dưỡng định kỳ")
    custody_ids = fields.One2many('ems.equipment.export.detail', 'equipment_id', string="Danh sách bàn giao")

    @api.one
    @api.depends('maintenance_ids')
    def _compute_maintenance_count(self):
        self.maintenance_count = len(self.maintenance_ids.filtered(lambda m: m.maintenance_type == 'corrective'))
        self.certificate_count = len(self.maintenance_ids.filtered(lambda m: m.maintenance_type == 'preventive'))

    @api.model
    def update_maintenance(self):
        data = self.search([('activate', '=', 'usage')])
        for record in data:
            if record.first_date_use:
                first_date_use = record.first_date_use
                # maintenance
                if record.maintenance_deadline > 0 and record.maintenance_deadline_type:
                    if record.last_maintenance and record.last_maintenance > record.first_date_use:
                        date = datetime.datetime.strptime(record.last_maintenance, '%Y-%m-%d').date()
                    else:
                        date = first_date_use
                    deadine_maintenance = self.count_deadline(date, record.maintenance_deadline_type,
                                                              record.maintenance_deadline)
                    days = deadine_maintenance['days']
                    if days == 0:
                        payload = {
                            'name': "Bảo dưỡng định kỳ: " + '[' + record.default_code + '] ' + record.name,
                            'code': record.code,
                            'maintenance_type': 'preventive',
                            'description': "Yêu cầu bảo dưỡng định kỳ",
                            'owner_user_id': record.env.uid,
                            'category_id': record.category_id.id if record.category_id else None,
                            'priority': '2',
                            'equipment_id': record.id,
                            'user_id': record.category_id.technician_user_id.id if record.category_id.technician_user_id else None,
                            'request_date': datetime.datetime.now(),
                            'schedule_date': datetime.datetime.now() + timedelta(days=1),
                        }
                        req = self.env['vnitpro.maintenance.request'].create(payload)
                        profile = {
                            'person_name': record.employee_id.name if record.employee_id else None,
                            'email': record.employee_id.work_email if record.employee_id else None,
                            'phone': record.employee_id.work_phone if record.employee_id else None,
                            'department': record.department_id.name if record.department_id else None,
                            'request_ids': req.id
                        }
                        self.env['vnitpro.maintenance.profile'].create(profile)
                # # repair
                if record.repair_deadline > 0 and record.repair_deadline_type:
                    if record.last_repair and record.last_repair > record.first_date_use:
                        date = datetime.datetime.strptime(record.last_repair, '%Y-%m-%d').date()
                    else:
                        date = first_date_use
                    deadline_repair = self.count_deadline(date, record.repair_deadline_type, record.repair_deadline)
                    days = deadline_repair['days']
                    if days == 0:
                        payload = {
                            'name': "Sửa chữa định kỳ: " + record.name,
                            'code': record.code,
                            'maintenance_type': 'preventive',
                            'description': "Yêu cầu sửa chữa định kỳ",
                            'owner_user_id': record.env.uid,
                            'category_id': record.category_id.id if record.category_id else None,
                            'priority': '2',
                            'equipment_id': record.id,
                            'user_id': record.category_id.technician_user_id.id if record.category_id.technician_user_id else None,
                            'request_date': datetime.datetime.now(),
                            'schedule_date': datetime.datetime.now() + timedelta(hours=4),
                        }
                        req = self.env['vnitpro.maintenance.request'].create(payload)
                        profile = {
                            'person_name': record.employee_id.name if record.employee_id else None,
                            'email': record.employee_id.work_email if record.employee_id else None,
                            'phone': record.employee_id.work_phone if record.employee_id else None,
                            'department': record.department_id.name if record.department_id else None,
                            'request_ids': req.id
                        }
                        self.env['vnitpro.maintenance.profile'].create(profile)
        return True

class SCIMaintenanceRequest(models.Model):
    _name = 'vnitpro.maintenance.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Maintenance Request'
    _order = "id desc"

    @api.returns('self')
    def _default_stage(self):
        return self.env['vnitpro.maintenance.stage'].search([], limit=1)

    name = fields.Char('Subjects', required=True)
    code = fields.Char('Code', readonly="1")
    description = fields.Html('Mô tả')
    profile_id = fields.One2many('vnitpro.maintenance.profile', 'request_ids', string="Thông tin", readonly=True)
    request_date = fields.Datetime('Ngày yêu cầu', track_visibility='onchange', default=datetime.datetime.now(),
                                   help="Date requested for the maintenance to happen")
    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid)
    equipment_id = fields.Many2one('vnitpro.device.main', 'Thiết bị/Vật tư', track_visibility="onchange")
    category_id = fields.Many2one('vnitpro.maintenance.equipment.category', 'Bộ phận tiếp nhận', required=True,
                                  track_visibility="onchange")
    maintenance_team_id = fields.Many2one('vnitpro.maintenance.team', string='Đội tiếp nhận') #required=True, default=_get_default_team_id
    user_id = fields.Many2one('hr.employee', string='Người phụ trách', track_visibility='onchange')
    stage_id = fields.Many2one('vnitpro.maintenance.stage', string='Stage', ondelete='restrict', track_visibility='onchange',
                               group_expand='_read_group_stage_ids', default=_default_stage)
    priority = fields.Selection(
        [('0', 'Rất thấp'), ('1', 'Thấp'), ('2', 'Bình thường'), ('3', 'Cao'), ('4', 'Khẩn cấp')], string='Độ ưu tiên')
    color = fields.Integer('Color Index')
    close_date = fields.Date('Ngày đóng', help="Ngày bảo trì hoàn thành. ")
    kanban_state = fields.Selection([('normal', 'In Progress'), ('doing', 'Doing'), ('blocked', 'Blocked'), ('done', 'Ready for next stage')],
                                    string='Kanban State', required=True, default='normal', track_visibility='onchange')
    supervisor_ids = fields.Many2many('hr.employee', string='Danh sách nhân sự bảo trì',
                                      track_visibility="onchange", domain="[('active','=','usage')]")
    archive = fields.Boolean(default=False, help="Set archive to true to hide the maintenance request without deleting it.")
    maintenance_type = fields.Selection([('corrective', 'Corrective'), ('preventive', 'Preventive')], string='Loại bảo trì', default="corrective", readonly=True)
    schedule_date = fields.Datetime('Lịch hẹn', help="Ngày nhóm bảo trì lên kế hoạch bảo trì ")
    duration = fields.Float(help="Duration in hours and minutes.", string='Thời lượng')
    tools_description = fields.Html('Hiện trạng', translate=True)
    operations_description = fields.Html('Kết quả', translate=True)
    status = fields.Text('Tình trạng', compute="_compute_status")

    @api.depends('schedule_date')
    def _compute_status(self):
        for record in self:
            if record.stage_id.code in ['new', 'doing']:
                msg = ''
                time = datetime.datetime.now()
                tz_current = pytz.timezone(self._context.get('tz') or 'UTC')  # get timezone user
                tz_database = pytz.timezone('UTC')
                time = tz_database.localize(time)
                time = time.astimezone(tz_current)
                time = time.date()
                if record.schedule_date:
                    expected_date = record.schedule_date.date()
                    days = (expected_date - time).days
                    if days < 0:
                        msg += _('\n- Quá hạn hoàn thành %s ngày') % abs(days)
                    elif days == 0:
                        msg += _('\n- Hôm nay là hạn chót')
                    elif days < 7:
                        msg += _('\n- Còn %s ngày đến hạn hoàn thành') % abs(days)
            elif record.stage_id.code == 'done':
                msg = _('\n- Đã hoàn thành')
            elif record.stage_id.code == 'cancel':
                msg = _('\n- Đã hủy')
            else:
                msg = _('\n- Yêu cầu đã được đóng')
            record.status = msg

    @api.multi
    @api.onchange('category_id')
    def _onchange_category_id(self):
        for record in self:
            if record.equipment_id and record.equipment_id.category_id != record.category_id:
                record.equipment_id = False

    @api.onchange('maintenance_team_id')
    def _onchange_maintenance_team_id(self):
        self.user_id = self.maintenance_team_id.technician_user_id

    @api.multi
    def archive_equipment_request(self):
        self.write({'archive': True})

    @api.multi
    def reset_equipment_request(self):
        """ Reinsert the maintenance request into the maintenance pipe in the first stage"""
        first_stage_obj = self.env['vnitpro.maintenance.stage'].search([], order="sequence asc", limit=1)
        # self.write({'active': True, 'stage_id': first_stage_obj.id})
        self.write({'archive': False, 'stage_id': first_stage_obj.id})

    @api.onchange('category_id')
    def onchange_category_id(self):
        if not self.user_id or not self.equipment_id or self.user_id:
            self.user_id = self.category_id.technician_user_id

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        request = super(SCIMaintenanceRequest, self).create(vals)
        if request.owner_user_id or request.user_id:
            request._add_followers()
        return request

    @api.multi
    def write(self, vals):
        # Overridden to reset the kanban_state to normal whenever
        # the stage (stage_id) of the Maintenance Request changes.
        if vals and 'kanban_state' not in vals and 'stage_id' in vals:
            vals['kanban_state'] = 'normal'
        res = super(SCIMaintenanceRequest, self).write(vals)
        if vals.get('owner_user_id') or vals.get('user_id'):
            self._add_followers()
        if 'stage_id' in vals:
            ticket_state = self.env['vnitpro.maintenance.stage'].search([('id', '=', vals.get('stage_id'))], limit=1)
            if ticket_state.code == 'doing':
                kanban_state = 'doing'
            elif ticket_state.code == 'cancel':
                kanban_state = 'blocked'
            else:
                kanban_state = 'done'
            self.kanban_state = kanban_state
            time = datetime.datetime.now()
            if self.maintenance_type == 'corrective':
                web_ticket = request.env['website.support.ticket'].sudo().search([('ticket_number', '=', self.code)])
                if web_ticket:
                    payload = {
                        'state_id': vals.get('stage_id'),
                    }
                    web_ticket.write(payload)
            else:
                if ticket_state.code in ('done', 'closed'):
                    #update ngày tính khấu hao
                    device_main = request.env['vnitpro.device.main'].sudo().search([('code', '=', self.code)])
                    if device_main:
                        payload = {
                            'last_maintenance': datetime.datetime.now(),
                        }
                        device_main.write(payload)
            diff = time - self.schedule_date
            days, seconds = diff.days, diff.seconds
            hours = days * 24 + seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            mi = (diff.days*1440 + diff.seconds/60)
            self.filtered(lambda m: m.stage_id.done).write(
                {'close_date': fields.Date.today(),
                 'duration':  float(hours) + float(minutes) / 60})
        if vals.get('equipment_id'):
            # need to change description of activity also so unlink old and create new activity
            self.activity_unlink(['vnitpro_maintenance.mail_act_maintenance_request'])
        return res

    def _add_followers(self):
        for request in self:
            partner_ids = [request.user_id.id]
            # request.message_subscribe(partner_ids=partner_ids)
            SCIMaintenanceRequest.followers(self)

    def followers(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        body = ""
        if self.user_id:
            body += "<p>Dear " + self.user_id.name + ",</p>"
        body += "<p>Bạn vừa nhận được 1 yêu cầu bảo trì/bảo dưỡng.</p>\
                   <p>Chi tiết yêu cầu: <a href='" + base_url + "/web#id=" + str(self.id) + "?model=vnitpro.maintenance.request'>Click vào đây</a></p> <hr/>\
                   <b>Ticket Number:</b> " + str(self.code) + "<br/>"
        if self.maintenance_type == 'corrective':
            body += "<b>Loại bảo trì:</b> Khắc phục sự cố<br/>"
        else:
            body += "<b>Loại bảo trì:</b> Bảo dưỡng định kỳ<br/>"
        if self.category_id:
            body += "<b>Bộ phận phụ trách:</b> " + self.category_id.name + "<br/>"
        if self.maintenance_team_id:
            body += "<b>Đội phụ trách:</b> " + self.maintenance_team_id.name + "<br/>"
        if self.description:
            body += "<b>Mô tả:</b><br/>" + self.description
        lst_email = []
        if self.user_id.work_email:
            lst_email.append(self.user_id.work_email)
        if len(lst_email) > 0:
            main_employee = {
                'subject': ('SCI-Support: ' + self.name),
                'body_html': body,
                'email_to': ",".join(lst_email),
            }
            self.env['mail.mail'].create(main_employee).send()

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages in the
            kanban view, even if they are empty
        """
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

class MaintenanceProfile(models.Model):
    _name = 'vnitpro.maintenance.profile'

    person_name = fields.Char(string='Người sử dụng')
    email = fields.Char(string="Email")
    phone = fields.Char(string="Điện thoại")
    department = fields.Char(string="Phòng ban")
    request_ids = fields.Many2one('vnitpro.maintenance.request',  string="Thông tin sở hữu",  readonly=True)

class MaintenanceTeam(models.Model):
    _name = 'vnitpro.maintenance.team'
    _description = 'Maintenance Teams'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    maintenance_category_id = fields.Many2one('vnitpro.maintenance.equipment.category', string='Bộ phận tiếp nhận', required=True)
    technician_user_id = fields.Many2one('hr.employee', 'Chịu trách nhiệm', track_visibility='onchange')
    member_ids = fields.Many2many('hr.employee', 'maintenance_team_users_rel', string="Thành viên")
    color = fields.Integer("Color Index", default=0)
    request_ids = fields.One2many('vnitpro.maintenance.request', 'maintenance_team_id', copy=False)

    # For the dashboard only
    todo_request_ids = fields.One2many('vnitpro.maintenance.request', string="Requests", copy=False, compute='_compute_todo_requests')
    todo_request_count = fields.Integer(string="Number of Requests", compute='_compute_todo_requests')
    todo_request_count_date = fields.Integer(string="Number of Requests Scheduled", compute='_compute_todo_requests')
    todo_request_count_high_priority = fields.Integer(string="Number of Requests in High Priority", compute='_compute_todo_requests')
    todo_request_count_block = fields.Integer(string="Number of Requests Blocked", compute='_compute_todo_requests')
    todo_request_count_unscheduled = fields.Integer(string="Number of Requests Unscheduled", compute='_compute_todo_requests')

    @api.one
    @api.depends('request_ids.stage_id.done')
    def _compute_todo_requests(self):
        self.todo_request_ids = self.request_ids.filtered(lambda e: e.kanban_state == 'normal')
        self.todo_request_count = len(self.todo_request_ids)
        self.todo_request_count_date = len(self.request_ids.filtered(lambda e: e.kanban_state == 'doing'))
        self.todo_request_count_high_priority = len(self.request_ids.filtered(lambda e: e.priority in ('3','4','5')))
        self.todo_request_count_block = len(self.request_ids.filtered(lambda e: e.kanban_state == 'done'))
        self.todo_request_count_unscheduled = len(self.todo_request_ids.filtered(lambda e: not e.schedule_date))

    @api.one
    @api.depends('equipment_ids')
    def _compute_equipment(self):
        self.equipment_count = len(self.equipment_ids)
