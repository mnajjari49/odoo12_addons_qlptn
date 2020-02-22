from odoo import fields, api, models


class Calendar(models.Model):
    _inherit = 'calendar.event'

    week_day_tree = fields.Selection([(0, 'Mon'), (1, 'Tue'), (2, 'Wed'), (3, 'Thu'), (4, 'Fri'), (5, 'Sat'), (6, 'Sun')],
                                     string='Week day', compute='_get_week_day')

    @api.depends('start')
    def _get_week_day(self):
        for record in self:
            record.week_day_tree = record.start.weekday()
