# -*- coding: utf-8 -*-
###############################################################################
#
#    Công ty giải pháp phần mềm VNITPro.
#    Copyright (C) 2018-TODAY VNITPro(<http://vnitpro.vn>).
#
###############################################################################
import logging

_logger = logging.getLogger(__name__)


class Utils:
    @staticmethod
    def send_notify_permission(record, user_id, xml_id_act_window='', task='', message='', is_delete_perm=False):
        """
        :param record: procurement or project or contract
        :param user_id: user id for access right
        :param xml_id_act_window: ID action window in xml(open form or tree or kanban)
        :param task: string type access
        :param message: string message role
        :param is_delete_perm: bool if delete
        :return:
        """
        ch_obj = record.env['mail.channel']
        user = record.env['res.users'].browse(user_id)
        if user:
            ch_name = 'Process ' + record.code + ' - ' + record.name
            ch = ch_obj.sudo().search([('name', '=', str(ch_name))])
            if not ch:
                ch = ch_obj.create({'name': str('Process ' + record.code + ' - ' + record.name),
                                    'public': 'private', 'email_send': False,
                                    'channel_partner_ids': [(4, record.env.user.partner_id.id),
                                                            (4, user.partner_id.id)]})

            Utils._invite_partner(record=record, channel=ch, partner_id=user.partner_id.id)

            if is_delete_perm:
                Utils._unfollow_channel_without_bus(channel=ch, partner_id=user.partner_id.id)
                Utils._send_bus(record=record, channel=ch, partner_id=user.partner_id.id, message='unsubscribe')
                return
            action = record.env.ref('{}.{}'.format(record._name.replace(".", "_"), xml_id_act_window)).id
            url = "#id={}&view_type=form&model={}&action={}" \
                .format(record.id, record._name, action)
            body = '<div class="o_mail_notification">{} ' \
                   '<a href="#model=res.users&id={}" target="" ' \
                   'data-oe-model="res.users" ' \
                   'data-oe-id="{}">@{}</a>{} <a href="{}" target="">{}</a></div>' \
                .format(task, user.id, user.id, user.name, message, url,
                        str(record.code + ' - ' + record.name))
            ch.message_post(content_subtype='html',
                            subtype="mail.mt_comment",
                            message_type="comment", body=body)

    @staticmethod
    def send_notify_channel_with_message(record, message='', xml_id_act_window=''):
        """
        :param xml_id_act_window:
        :param record: procurement or project or contract
        :param message: string message to send
        :return:
        """
        ch_obj = record.env['mail.channel']
        ch_name = 'Process ' + record.code + ' - ' + record.name
        ch = ch_obj.sudo().search([('name', '=', str(ch_name))])
        if not ch:
            ch = ch_obj.create({'name': str('Process ' + record.code + ' - ' + record.name),
                                'public': 'private', 'email_send': False,
                                'channel_partner_ids': [(4, record.env.user.partner_id.id)]})

        action = record.env.ref('{}.{}'.format(record._name.replace(".", "_"), xml_id_act_window)).id
        url = "#id={}&view_type=form&model={}&action={}" \
            .format(record.id, record._name, action)
        body = '<div class="o_mail_notification">{}<a href="{}" target="">{}</a></div>' \
            .format(message, url, str(record.code + ' - ' + record.name))
        ch.message_post(content_subtype='html',
                        subtype="mail.mt_comment",
                        message_type="comment", body=body)

    @staticmethod
    def _unfollow_channel_without_bus(channel, partner_id):
        channel.write({'channel_partner_ids': [(3, partner_id)]})

    @staticmethod
    def _invite_partner(record, channel, partner_id):
        partners = record.env['res.partner'].browse(partner_id)
        partners_to_add = partners - channel.channel_partner_ids
        if partners_to_add:
            channel.write({'channel_last_seen_partner_ids': [(0, 0, {'partner_id': partner_id})
                                                             for partner_id in partners_to_add.ids]})
            Utils._send_bus(record=record, channel=channel, partner_id=partner_id, message='invite')

    @staticmethod
    def _send_bus(record, channel, partner_id, message):
        channel_info = channel.channel_info(message)[0]
        record.env['bus.bus'].sendone((record._cr.dbname, 'res.partner', partner_id), channel_info)
