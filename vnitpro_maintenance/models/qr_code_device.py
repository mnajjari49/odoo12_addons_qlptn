# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.http import request
import qrcode
import base64
from io import BytesIO

def generate_qr_code(url):
    qr = qrcode.QRCode(
             version=1,
             error_correction=qrcode.constants.ERROR_CORRECT_L,
             box_size=20,
             border=4,
             )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    temp = BytesIO()
    img.save(temp, format="PNG")
    qr_img = base64.b64encode(temp.getvalue())
    return qr_img

class QRCodeInvoice(models.Model):
    _inherit = 'vnitpro.device.main'

    qr_image = fields.Binary("QR Code", compute='_generate_qr_code')

    @api.one
    def _generate_qr_code(self):
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        self.qr_image = generate_qr_code(base_url)