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


class PartsInDevice(models.Model):
    _name = 'vnitpro.device.parts.in'
    _inherit = 'vnitpro.device'
    _description = 'Parts In Device'

    main_device_id = fields.Many2one('vnitpro.device.main', 'Thiết bị chính',
                                     related="extra_device_id.main_device_id")
    extra_device_id = fields.Many2one('vnitpro.device.extra', 'Thiết bị phụ tùng', required=True,
                                      track_visibility="onchange")
    amount = fields.Integer('Số lượng', size=3, track_visibility="onchange")
    # unit_id = fields.Many2one('vnitpro.unit', string='Đơn vị', required=True, default=lambda self: self._default_unit,
    #                           track_visibility="onchange")
    location = fields.Text('Vị trí', track_visibility="onchange")
    description_images_ids = fields.One2many('vnitpro.device.parts.in.image', 'parts_in_device_id',
                                             'Hình ảnh mô tả')

    def _default_unit(self):
        return self.env['vnitpro.unit'].search([], limit=1)

    @api.constrains('amount')
    def check_amount(self):
        if self.amount < 0:
            raise ValidationError(_('Quantity must be greater than 0'))

    @api.onchange('main_device_id')
    def onchange_main_device_id(self):
        for record in self:
            _logger.warning('okess')
            if record.extra_device_id.main_device_id != record.main_device_id or record.main_device_id == False:
                _logger.warning('diess')
                record.extra_device_id = False

    @api.model
    def create(self, vals):
        device = super(PartsInDevice, self).create(vals)
        payload = {'device_ids': device.id, 'device_type': 'part'}
        self.env['product.product'].sudo().search([('id', '=', device.product_id.id)]).write(payload)
        return device

    @api.multi
    def write(self, vals):
        if vals.get('product_id'):
            self.env['product.product'].sudo().search([('id', '=', self.product_id.id)]).write(
                {'device_ids': 0, 'device_type': False})
            payload = {'device_ids': self.id, 'device_type': 'part'}
            self.env['product.product'].sudo().search([('id', '=', vals.get('product_id'))]).write(payload)
        return super(PartsInDevice, self).write(vals)

class PartsInDeviceImages(models.Model):
    _name = 'vnitpro.device.parts.in.image'
    _inherit = 'vnitpro.device.image'
    _description = 'Parts In Device Image'

    parts_in_device_id = fields.Many2one('vnitpro.device.parts.in', 'Parts In Device', required=True,
                                         ondelete="cascade")
