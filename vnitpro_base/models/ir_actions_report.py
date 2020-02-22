# -*- coding: utf-8 -*-
###############################################################################
#
#    Công ty giải pháp phần mềm VNITPro.
#    Copyright (C) 2018-TODAY VNITPro(<http://vnitpro.vn>).
#
###############################################################################

from odoo import api, _, models
from datetime import datetime
import time
import pytz
import logging
_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.multi
    def render_template(self, template, values=None):
        context = self.env.context.copy()
        context.update({'lang': self.env.user.partner_id.lang})
        self.env.context = context
        return super(IrActionsReport, self).render_template(template, values)
