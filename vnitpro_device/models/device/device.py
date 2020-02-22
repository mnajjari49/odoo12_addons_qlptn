# -*- coding: utf-8 -*-
###############################################################################
#
#    Công ty giải pháp phần mềm VNITPro.
#    Copyright (C) 2018-TODAY VNITPro(<http://vnitpro.vn>).
#    Create by MinhND - Developer of VNITPro
###############################################################################

from odoo import models, fields, api, _, tools

class Product(models.Model):
    _inherit = ['product.product']
    device_ids = fields.Integer(string='Device_id', default=0)
    device_type = fields.Selection(
        [('main', 'Thiết bị chính'), ('extra', 'Thiết bị phụ'), ('part', 'Phụ tùng')],'Loại thiết bị')

class Device(models.Model):
    _name = 'vnitpro.device'
    _description = "Device"
    _inherits = {
        'product.product': 'product_id',
    }

    stock_location = fields.Many2one('stock.location', string='Kho hàng', required=True,
                                     domain=[('usage', '=', 'internal')])
    equipment_domain = fields.Many2many('product.product', compute='_get_equipment_domain')
    product_id = fields.Many2one('product.product', string='Vật tư', required=True, ondelete='cascade',
                                 help='Product-related data of the services')
                                 # domain=[('device_ids', '=', 0), ('type', '=', 'product')])  #
    date_import = fields.Date('Ngày nhập', required=True, default=fields.Date.today(),
                              track_visibility="onchange")
    first_date_use = fields.Date('Ngày tính khấu hao', default=fields.Date.today())
    period = fields.Integer(string='Bảo hành(Tháng)')
    description = fields.Html('Mô tả', size=1500)
    activate = fields.Selection(
        [('not_used', 'Chưa sử dụng'), ('usage', 'Đang sử dụng'), ('liquidate', 'Chờ thanh lý'), ('less_use', 'Đang Hỏng'), ('loss', 'Đã bị Mất')],
        'Trạng thái', required=True, default='not_used', track_visibility="onchange")

    @api.one
    @api.depends('stock_location')
    def _get_equipment_domain(self):
        stock_quants = self.env['stock.quant'].search([('location_id', '=', self.stock_location.id), ('quantity', '>', 0)])
        self.equipment_domain = stock_quants.mapped('product_id')

class DeviceImages(models.Model):
    _name = 'vnitpro.device.image'
    _description = 'Device Image'

    name = fields.Char('Name', size=100, required=True)
    image = fields.Binary('Image')
    description = fields.Text('Description', size=600)
