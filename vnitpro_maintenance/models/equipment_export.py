# -*-coding: utf-8 -*-


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
import logging
from odoo.exceptions import Warning, UserError

_logger = logging.getLogger(__name__)


class EmsEquipmentExport(models.Model):
    _name = 'ems.equipment.export'
    _inherit = 'mail.thread'
    _description = 'Equipments Export'

    @api.model
    def _default_code(self):
        last_id = self.search([], order='id desc', limit=1).id
        _logger.warning(last_id)
        last_id += 1
        code = 'EX' + str(last_id).zfill(5)
        return code

    code = fields.Char('Số phiếu', size=30, required=True,
                       track_visibility='onchange', default=lambda self: self._default_code())
    type = fields.Selection([('import', 'Nhận bàn giao'), ('export', 'Xuất bàn giao')], string='Loại bàn giao', default="export", required=True)
    export_date = fields.Date('Ngày bàn giao', required=True, track_visibility='onchange', default=fields.Date.today())

    category_id = fields.Many2one('vnitpro.maintenance.equipment.category', 'Phòng chủ quản', required=True)
    employee_id = fields.Many2one('hr.employee', string='Nhân sự giao', required=True)

    department_id = fields.Many2one('hr.department', 'Phòng ban sử dụng', required=True)
    parent_id = fields.Many2one('hr.employee', 'Quản lý', readonly="1")
    employee_use = fields.Many2one('hr.employee', string='Nhân sự nhận', required=True,
                                   domain="[('department_id', '=', department_id)]")

    description = fields.Text(size=600, track_visibility="onchange")
    equipment_ids = fields.One2many('ems.equipment.export.detail', 'export_id', 'Thiết bị', track_visibility='onchange')
    attachment_ids = fields.One2many('vnitpro.base.attachment', 'equipment_export_id', 'Attachment Files')
    state = fields.Selection([('draft', 'Dự thảo'), ('approved', 'Xác nhận')], string='Status', default='draft',
                             track_visibility='always')
    checklist_domain = fields.Many2many('vnitpro.device.main', compute='_get_checklist_domain')

    @api.onchange('department_id')
    def _onchange_department(self):
        self.parent_id = self.department_id.manager_id

    @api.one
    @api.depends('type', 'category_id', 'employee_id')
    def _get_checklist_domain(self):
        checklist = self.env['vnitpro.device.main']
        if self.type == 'import':
            domain = [('activate', '=', 'usage')]
            if self.employee_id:
                domain.append(('employee_id', '=', self.employee_id.id))
            self.checklist_domain = checklist.search(domain)
        else:
            domain = [('activate', '=', 'not_used')]
            if self.category_id:
                domain.append(('category_id', '=', self.category_id.id))
            self.checklist_domain = checklist.search(domain)

    @api.multi
    def approve(self):
        self.state = 'approved'
        if self.type == 'import':
            for item in self.equipment_ids:
                item.equipment_id.activate = 'not_used'
                item.equipment_id.department_id = None
                item.equipment_id.employee_id = None
        else:
            for item in self.equipment_ids:
                item.equipment_id.activate = 'usage'
                item.equipment_id.department_id = self.department_id.id
                item.equipment_id.parent_id = self.parent_id.id
                item.equipment_id.employee_id = self.employee_use.id

    def _compute_attachment_ids(self):
        for task in self:
            attachment_ids = self.env['ir.attachment'].search([('res_id', '=', task.id), ('res_model', '=', 'ems.equipment.export')]).ids
            message_attachment_ids = task.mapped('message_ids.attachment_ids').ids  # from mail_thread
            task.attachment_ids = list(set(attachment_ids) - set(message_attachment_ids))

    _sql_constraint = [
        ('unique_code', 'unique(code)', 'Code must be unique per equipment'),
    ]

    @api.multi
    @api.constrains('code')
    def _compute_special_character_code(self):
        for record in self:
            if not re.match("^[a-zA-Z0-9_/\\\\]*$", record.code):
                raise ValidationError(_("Please Provide valid Code."))

    @api.multi
    @api.onchange('code')
    def _compute_upper_code(self):
        for record in self:
            if record.code:
                code = record.code
                record.code = code.upper()



class BaseAttachment(models.Model):
    _inherit = "vnitpro.base.attachment"

    equipment_export_id = fields.Many2one(
        'ems.equipment.export', 'Support ticket', ondelete="cascade")