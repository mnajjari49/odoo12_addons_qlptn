# -*-coding: utf-8 -*-


from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class EmsEquipmentExportDetail(models.Model):
    _name = 'ems.equipment.export.detail'
    _description = 'Equipments Export Detail'


    export_id = fields.Many2one(
        'ems.equipment.export', 'Export', required=True, ondelete='cascade')
    employee_use = fields.Many2one('hr.employee', string='Người sử dụng', required=True, related='export_id.employee_use')
    department_id = fields.Many2one('hr.department', 'Phòng ban', related='employee_use.department_id')
    type = fields.Selection(related='export_id.type')
    equipment_id = fields.Many2one('vnitpro.device.main', string='Vật tư', required=True, ondelete='cascade',
                                 help='Product-related data of the services')  #
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure', related='equipment_id.uom_id')
    export_date = fields.Date('Ngày bàn giao', related='export_id.export_date')
    note = fields.Text('Note', size=600, track_visibility="onchange")
