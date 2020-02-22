# -*- coding: utf-8 -*-
###############################################################################
#
#    Công ty giải pháp phần mềm VNITPro.
#    Copyright (C) 2018-TODAY VNITPro(<http://vnitpro.vn>).
#    Create by MinhND - Developer of VNITPro
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class ExtraDevice(models.Model):
    _name = 'vnitpro.device.extra'
    _inherit = 'vnitpro.device'
    _description = 'Device Type'

    main_device_id = fields.Many2one('vnitpro.device.main', required=True, string='Thiết bị chính')
    amount = fields.Integer('Số lượng', size=5)
    # unit_id = fields.Many2one('vnitpro.unit', string='Đơn vị', required=True)
    description_images_ids = fields.One2many('vnitpro.device.extra.image', 'extra_device_id', 'Hình ảnh mô tả')
    parts_in_device_ids = fields.One2many('vnitpro.device.parts.in', 'extra_device_id', 'Linh kiện/Vật tư')
    count_parts_in_device = fields.Integer('Quantity Parts In Devices', compute="_compute_quantity_of_parts_in_device")

    @api.constrains('amount')
    def check_amount(self):
        if self.amount <= 0:
            raise ValidationError(_('Quantity must be greater than 0'))

    @api.depends('parts_in_device_ids')
    def _compute_quantity_of_parts_in_device(self):
        for record in self:
            record.count_parts_in_device = len(record.parts_in_device_ids)

    def get_parts_in_device_in_main_device(self):
        action = self.env.ref('vnitpro_device.act_vnitpro_device_parts_in_view').read()[0]
        if self:
            action['display_name'] = self.display_name
            action['context'] = {'search_default_extra_device_id': self.id}
        return action

    @api.model
    def create(self, vals):
        device = super(ExtraDevice, self).create(vals)
        payload = {'device_ids': device.id, 'device_type': 'extra'}
        self.env['product.product'].sudo().search([('id', '=', device.product_id.id)]).write(payload)
        return device

    @api.multi
    def write(self, vals):
        if vals.get('product_id'):
            self.env['product.product'].sudo().search([('id', '=', self.product_id.id)]).write(
                {'device_ids': 0, 'device_type': False})
            payload = {'device_ids': self.id, 'device_type': 'extra'}
            self.env['product.product'].sudo().search([('id', '=', vals.get('product_id'))]).write(payload)
        return super(ExtraDevice, self).write(vals)

class ExtraDeviceImages(models.Model):
    _name = 'vnitpro.device.extra.image'
    _inherit = 'vnitpro.device.image'
    _description = 'Extra Device Image'

    extra_device_id = fields.Many2one('vnitpro.device.extra', 'Extra Device', required=True, ondelete="cascade")
