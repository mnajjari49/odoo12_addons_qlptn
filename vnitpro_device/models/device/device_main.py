# -*- coding: utf-8 -*-
###############################################################################
#
#    Công ty giải pháp phần mềm VNITPro.
#    Copyright (C) 2018-TODAY VNITPro(<http://vnitpro.vn>).
#    Create by MinhND - Developer of VNITPro
###############################################################################

from odoo import models, fields, api, _
import logging
from dateutil.relativedelta import relativedelta
import datetime
from datetime import timedelta
import pytz

_logger = logging.getLogger(__name__)
DATETYPE = [('days', 'Ngày'), ('months', 'tháng'), ('years', 'năm')]

class MainDevice(models.Model):
    _name = 'vnitpro.device.main'
    _inherit = 'vnitpro.device'
    _description = 'Main Device'

    department_id = fields.Many2one('hr.department', 'Phòng ban sử dụng', readonly="1")
    parent_id = fields.Many2one('hr.employee', 'Quản lý', readonly="1")
    employee_id = fields.Many2one('hr.employee', string="Người sử dụng",  domain="[('department_id', '=', department_id)]", readonly="1")
    partner_id = fields.Many2one('res.partner', string='Nhà cung cấp', domain="[('supplier', '=', 1)]")
    description_images_ids = fields.One2many('vnitpro.device.main.image', 'main_device_id', 'Hình ảnh mô tả')
    extra_device_ids = fields.One2many('vnitpro.device.extra', 'main_device_id', 'Thiết bị phụ tùng')
    count_extra_device = fields.Integer('Quantity Of Extra Devices', compute="_compute_quantity_of_extra_device")
    serial_no = fields.Char('Serial Number')
    equipment_lvl = fields.Selection([(1, 'Cấp độ 1'), (2, 'Cấp độ 2'), (3, 'Cấp độ 3'), (4, 'Cấp độ 4'), (5, 'Cấp độ 5')], 'Cấp độ CL')

    # Sửa chữa
    last_repair = fields.Date('Sửa chữa lần cuối', readonly="1")
    repair_deadline = fields.Integer('Thời hạn sửa chữa', size=3, track_visibility="onchange")
    repair_deadline_type = fields.Selection(DATETYPE, 'Date Type', default="months", required=True,
                                            track_visibility="onchange")
    repair_deadline_display = fields.Char('Thời hạn sửa chữa', compute="_compute_deadline_display")
    repair_status = fields.Text('Tình trạng', compute="_compute_status")
    repair_expire_date = fields.Date('Ngày đến hạn', compute="_compute_status",
                                     store=True)  # Ngày đến hạn sửa chữa
    # Bảo dưỡng
    last_maintenance = fields.Date('Bảo dưỡng lần cuối', readonly="1")
    maintenance_deadline = fields.Integer('Thời hạn bảo dưỡng', size=3, track_visibility="onchange")
    maintenance_deadline_type = fields.Selection(DATETYPE, 'Date Type', default="months", required=True,
                                                 track_visibility="onchange")
    maintenance_deadline_display = fields.Char('Thời hạn bảo dưỡng', compute="_compute_deadline_display")
    maintenance_status = fields.Text('Tình trạng', compute="_compute_status")
    maintenance_expire_date = fields.Date('Ngày đến hạn', compute="_compute_status",
                                          store=True)  # Ngày đến hạn bảo dưỡng

    @api.onchange('department_id')
    def _onchange_department(self):
        self.parent_id = self.department_id.manager_id

    @api.depends('extra_device_ids')
    def _compute_quantity_of_extra_device(self):
        for record in self:
            record.count_extra_device = len(record.extra_device_ids)

    def get_extra_device_in_main_device(self):
        action = self.env.ref('vnitpro_device.act_vnitpro_device_extra_view').read()[0]
        if self:
            action['display_name'] = self.display_name
            action['context'] = {'search_default_main_device_id': self.id}
        return action

    @api.onchange('department_id')
    def _onchange_category(self):
        self.employee_id = None

    @api.depends('maintenance_deadline', 'maintenance_deadline_type', 'repair_deadline', 'repair_deadline_type',
                 'first_date_use')
    def _compute_deadline_display(self):
        for record in self:
            if record.maintenance_deadline > 0 and record.maintenance_deadline_type:
                time_type = ''
                if record.maintenance_deadline_type == 'days':
                    time_type = _('days')
                elif record.maintenance_deadline_type == 'months':
                    time_type = _('months')
                elif record.maintenance_deadline_type == 'years':
                    time_type = _('years')
                record.maintenance_deadline_display = str(record.maintenance_deadline) + ' ' + time_type
            else:
                record.maintenance_deadline_display = _('Undefined')

            if record.repair_deadline > 0 and record.repair_deadline_type:
                time_type = ''
                if record.repair_deadline_type == 'days':
                    time_type = _('days')
                elif record.repair_deadline_type == 'months':
                    time_type = _('months')
                elif record.repair_deadline_type == 'years':
                    time_type = _('years')
                record.repair_deadline_display = str(record.repair_deadline) + ' ' + time_type
            else:
                record.repair_deadline_display = _('Undefined')

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

    @api.depends('last_maintenance', 'last_repair', 'first_date_use', 'repair_deadline', 'maintenance_deadline', 'repair_deadline_type', 'maintenance_deadline_type')
    def _compute_status(self):
        for record in self:
            repair_msg = ''
            maintenance_msg = ''
            if record.first_date_use:
                # first_date_use = datetime.datetime.strptime(record.first_date_use, '%Y-%m-%d').date()
                first_date_use = record.first_date_use
                # maintenance
                if record.maintenance_deadline > 0 and record.maintenance_deadline_type:
                    if record.last_maintenance and record.last_maintenance > record.first_date_use:
                        date = record.last_maintenance
                    else:
                        date = first_date_use
                    deadine_maintenance = self.count_deadline(date, record.maintenance_deadline_type,
                                                              record.maintenance_deadline)
                    days = deadine_maintenance['days']
                    record.maintenance_expire_date = deadine_maintenance['date']
                    if days < 0:
                        maintenance_msg += ('Quá hạn bảo dưỡng {0} ngày').format(str(abs(days)))
                    elif days == 0:
                        maintenance_msg += ('Hôm nay là ngày bảo dưỡng')
                    elif days < 15:
                        maintenance_msg += ('{0} ngày nữa là ngày bảo dưỡng').format(str(abs(days)))
                # # repair
                if record.repair_deadline > 0 and record.repair_deadline_type:
                    if record.last_repair and record.last_repair > record.first_date_use:
                        date = datetime.datetime.strptime(record.last_repair, '%Y-%m-%d').date()
                    else:
                        date = first_date_use
                    deadline_repair = self.count_deadline(date, record.repair_deadline_type, record.repair_deadline)
                    days = deadline_repair['days']
                    record.repair_expire_date = deadline_repair['date']
                    if days < 0:
                        repair_msg += ('Quá hạn sửa chữa {0} ngày').format(str(abs(days)))
                    elif days == 0:
                        repair_msg += ('Hôm nay là ngày sửa chữa')
                    elif days < 30:
                        repair_msg += ('{0} ngày nữa là ngày sửa chữa').format(str(abs(days)))

            record.maintenance_status = maintenance_msg
            record.repair_status = repair_msg

    @api.model
    def create(self, vals):
        device = super(MainDevice, self).create(vals)
        payload = {'device_ids': device.id, 'device_type': 'main'}
        self.env['product.product'].sudo().search([('id', '=', device.product_id.id)]).write(payload)
        return device

    @api.multi
    def write(self, vals):
        if vals.get('product_id'):
            self.env['product.product'].sudo().search([('id', '=', self.product_id.id)]).write(
                {'device_ids': 0, 'device_type': False})
            payload = {'device_ids': self.id, 'device_type': 'main'}
            self.env['product.product'].sudo().search([('id', '=', vals.get('product_id'))]).write(payload)
        return super(MainDevice, self).write(vals)

class MainDeviceImages(models.Model):
    _name = 'vnitpro.device.main.image'
    _inherit = 'vnitpro.device.image'
    _description = 'Main Device Image'

    main_device_id = fields.Many2one('vnitpro.device.main', 'Main Device', required=True, ondelete="cascade")
