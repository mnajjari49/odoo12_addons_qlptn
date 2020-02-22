# -*- coding: utf-8 -*-
import werkzeug
import json
import base64
from random import randint
import os
import datetime
import requests
import logging
_logger = logging.getLogger(__name__)

import odoo.http as http
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.addons.http_routing.models.ir_http import slug

class SupportTicketController(http.Controller):

    @http.route('/support/approve/<ticket_id>', type='http', auth="public")
    def support_approve(self, ticket_id, **kwargs):
        support_ticket = request.env['website.support.ticket'].sudo().browse( int(ticket_id) )

        awaiting_approval = request.env['ir.model.data'].get_object('website_support','awaiting_approval')

        if support_ticket.state_id.id == awaiting_approval.id:
            #Change the ticket state to approved
            website_ticket_state_approval_accepted = request.env['ir.model.data'].get_object('website_support','website_ticket_state_approval_accepted')
            support_ticket.state_id = website_ticket_state_approval_accepted.id

            #Also change the approval
            approval_accepted = request.env['ir.model.data'].get_object('website_support','approval_accepted')

            #Send an email out to everyone in the category notifing them the ticket has been approved
            notification_template = request.env['ir.model.data'].sudo().get_object('website_support', 'support_ticket_approval_user')
            support_ticket_menu = request.env['ir.model.data'].sudo().get_object('website_support', 'website_support_ticket_menu')
            support_ticket_action = request.env['ir.model.data'].sudo().get_object('website_support', 'website_support_ticket_action')

            # for my_user in support_ticket.category_id.cat_user_ids:
            #     values = notification_template.generate_email(support_ticket.id)
            #     values['body_html'] = values['body_html'].replace("_ticket_url_", "web#id=" + str(support_ticket.id) + "&view_type=form&model=website.support.ticket&menu_id=" + str(support_ticket_menu.id) + "&action=" + str(support_ticket_action.id) ).replace("_user_name_",  my_user.partner_id.name)
            #     #values['body'] = values['body_html']
            #     values['email_to'] = my_user.partner_id.email
            #
            #     send_mail = request.env['mail.mail'].sudo().create(values)
            #     send_mail.send()
            #
            #     #Remove the message from the chatter since this would bloat the communication history by a lot
            #     send_mail.mail_message_id.res_id = 0

            return "Request Approved Successfully"
        else:
            return "Ticket does not need approval"

    @http.route('/support/disapprove/<ticket_id>', type='http', auth="public")
    def support_disapprove(self, ticket_id, **kwargs):
        support_ticket = request.env['website.support.ticket'].sudo().browse( int(ticket_id) )

        awaiting_approval = request.env['ir.model.data'].get_object('website_support','awaiting_approval')

        if support_ticket.state_id.id == awaiting_approval.id:
            #Change the ticket state to disapproved
            website_ticket_state_approval_rejected = request.env['ir.model.data'].get_object('website_support','website_ticket_state_approval_rejected')
            support_ticket.state_id = website_ticket_state_approval_rejected.id

            #Also change the approval
            approval_rejected = request.env['ir.model.data'].get_object('website_support','approval_rejected')
            # support_ticket.approval_id = approval_rejected.id

            #Send an email out to everyone in the category notifing them the ticket has been approved
            notification_template = request.env['ir.model.data'].sudo().get_object('website_support', 'support_ticket_approval_user')
            support_ticket_menu = request.env['ir.model.data'].sudo().get_object('website_support', 'website_support_ticket_menu')
            support_ticket_action = request.env['ir.model.data'].sudo().get_object('website_support', 'website_support_ticket_action')

            for my_user in support_ticket.category_id.cat_user_ids:
                values = notification_template.generate_email(support_ticket.id)
                values['body_html'] = values['body_html'].replace("_ticket_url_", "web#id=" + str(support_ticket.id) + "&view_type=form&model=website.support.ticket&menu_id=" + str(support_ticket_menu.id) + "&action=" + str(support_ticket_action.id) ).replace("_user_name_",  my_user.partner_id.name)
                #values['body'] = values['body_html']
                values['email_to'] = my_user.partner_id.email

                send_mail = request.env['mail.mail'].sudo().create(values)
                send_mail.send()

                #Remove the message from the chatter since this would bloat the communication history by a lot
                send_mail.mail_message_id.res_id = 0
                
            return "Request Rejected Successfully"
        else:
            return "Ticket does not need approval"

    @http.route('/support/survey/<portal_key>', type="http", auth="public", website=True)
    def support_ticket_survey(self, portal_key):
        """Display the survey"""

        support_ticket = request.env['website.support.ticket'].sudo().search([('portal_access_key','=', portal_key)])

        if support_ticket.support_rating:
            return "Survey Already Complete"
        else:
            return http.request.render('website_support.support_ticket_survey_page', {'support_ticket': support_ticket})


    @http.route('/support/survey/process/<portal_key>', type="http", auth="public", website=True)
    def support_ticket_survey_process(self, portal_key, **kw):
        """Insert Survey Response"""

        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value

        if 'rating' not in values:
            return "Please select a rating"

        support_ticket = request.env['website.support.ticket'].sudo().search([('portal_access_key','=', portal_key)])

        if support_ticket.support_rating:
            return "Survey Already Complete"
        else:
            support_ticket.support_rating = values['rating']
            support_ticket.support_comment = values['comment']
            return http.request.render('website_support.support_survey_thank_you', {})

    @http.route('/support/account/create', type="http", auth="public", website=True)
    def support_account_create(self, **kw):
        """  Create no permission account"""

        setting_allow_user_signup = request.env['ir.default'].get('website.support.settings', 'allow_user_signup')

        if setting_allow_user_signup:
            return http.request.render('website_support.account_create', {})
        else:
            return "Account creation has been disabled"

    @http.route('/support/account/create/process', type="http", auth="public", website=True)
    def support_account_create_process(self, **kw):
        """  Create no permission account"""

        setting_allow_user_signup = request.env['ir.default'].get('website.support.settings', 'allow_user_signup')

        if setting_allow_user_signup:
 
            values = {}
            for field_name, field_value in kw.items():
                values[field_name] = field_value

            #Create the new user
            new_user = request.env['res.users'].sudo().create({'name': values['name'], 'login': values['login'], 'email': values['login'], 'password': values['password'] })

            #Remove all permissions
            new_user.groups_id = False

            #Add the user to the support group
            support_group = request.env['ir.model.data'].sudo().get_object('website_support', 'support_group')
            support_group.users = [(4, new_user.id)]

            #Also add them to the portal group so they can access the website
            group_portal = request.env['ir.model.data'].sudo().get_object('base','group_portal')
            group_portal.users = [(4, new_user.id)]

            #Automatically sign the new user in
            request.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
            request.session.authenticate(request.env.cr.dbname, values['login'], values['password'])

            #Redirect them to the support page
            return werkzeug.utils.redirect("/support/help")
        else:
            return "Account creation has been disabled"

    @http.route('/support/help', type="http", auth="public", website=True)
    def support_help(self, **kw):
        """Displays all help groups and thier child help pages"""

        permission_list = []
        for perm_group in request.env.user.groups_id:
            permission_list.append(perm_group.id)

        # help_groups = http.request.env['website.support.help.group'].sudo().search(['|', ('group_ids', '=', False ), ('group_ids', 'in', permission_list), ('website_published','=',True)])
        #
        # setting_allow_user_signup = request.env['ir.default'].get('website.support.settings', 'allow_user_signup')

        manager = False
        # if request.env['website.support.department.contact'].sudo().search_count([('user_id','=',request.env.user.id)]) == 1:
        #     manager = True

        return http.request.render('website_support.support_help_pages', {'help_groups': [], 'setting_allow_user_signup': [], 'manager': manager})

    @http.route('/support/ticket/reporting', type="http", auth="user", website=True)
    def support_ticket_reporting(self, **kw):
        """ Displays stats related to tickets in the department """

        #Just get the first department, managers in multiple departments are not supported
        # department = request.env['website.support.department.contact'].search([('user_id','=',request.env.user.id)])[0].wsd_id
        department = None
        extra_access = []
        # for extra_permission in department.partner_ids:
        #     extra_access.append(extra_permission.id)

        support_tickets = http.request.env['website.support.ticket'].sudo().search(['|', ('partner_id','=',request.env.user.partner_id.id), ('partner_id', 'in', extra_access), ('partner_id','!=',False) ])        

        support_ticket_count = len(support_tickets)

        return http.request.render('website_support.support_ticket_reporting', {'department': department, 'support_ticket_count': support_ticket_count})

    @http.route('/support/ticket/submit', type="http", auth="public", website=True)
    def support_submit_ticket(self, **kw):
        """Let's public and registered user submit a support ticket"""
        person_name = ""
        person_email = ""
        person_phone = ""
        recaptcha_site_key =""
        if http.request.env.user.employee_id:
            person_name = http.request.env.user.employee_id.name
            person_email = http.request.env.user.employee_id.work_email
            person_phone = http.request.env.user.employee_id.work_phone

        category_access = []
        for category_permission in http.request.env.user.groups_id:
            category_access.append(category_permission.id)
            
        ticket_categories = http.request.env['vnitpro.maintenance.equipment.category'].sudo().search([])

        setting_max_ticket_attachments = request.env['ir.default'].get('website.support.settings', 'max_ticket_attachments')
        setting_max_ticket_attachment_filesize = request.env['ir.default'].get('website.support.settings', 'max_ticket_attachment_filesize')
        # website = request.env['website'].get_current_website()
        # if website:
        #     recaptcha_site_key = website.recaptcha_site_key
        return http.request.render('website_support.support_submit_ticket', {'categories': ticket_categories, 'person_name': person_name, 'email': person_email, 'phone': person_phone, 'department': '', 'setting_max_ticket_attachments': setting_max_ticket_attachments, 'setting_max_ticket_attachment_filesize': setting_max_ticket_attachment_filesize, 'setting_google_captcha_client_key': recaptcha_site_key})

    @http.route('/support/feedback/process/<help_page>', type="http", auth="public", website=True)
    def support_feedback(self, help_page, **kw):
        """Process user feedback"""

        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value

        #Don't want them distorting the rating by submitting -50000 ratings
        if int(values['rating']) < 1 or int(values['rating']) > 5:
            return "Invalid rating"

        #Feeback is required
        if values['feedback'] == "":
            return "Feedback required"

        request.env['website.support.help.page.feedback'].sudo().create({'hp_id': int(help_page), 'feedback_rating': values['rating'], 'feedback_text': values['feedback'] })

        return werkzeug.utils.redirect("/support/help")

    @http.route('/helpgroup/new/<group>', type='http', auth="user", website=True)
    def help_group_create(self, group, **post):
        """Add new help group via content menu"""
        help_group = request.env['website.support.help.group'].create({'name': group})
        return werkzeug.utils.redirect("/support/help")

    @http.route('/helppage/new', type='http', auth="user", website=True)
    def help_page_create(self, group_id, help_page_name, **post):
        """Add new help page via content menu"""
        help_page = request.env['website.support.help.page'].create({'group_id': group_id,'name': help_page_name})
        return werkzeug.utils.redirect("/support/help/%s/%s?enable_editor=1" % (slug(help_page.group_id), slug(help_page)))

    @http.route('/support/help/<model("website.support.help.group"):help_group>', type='http', auth="public", website=True)
    def help_group(self, help_group):
        """Displays help group template"""
        if help_group.website_published:
            return http.request.render("website_support.help_group", {'help_group':help_group})
        else:
            return request.render('website.404')

    @http.route(['''/support/help/<model("website.support.help.group"):help_group>/<model("website.support.help.page", "[('group_id','=',help_group[0])]"):help_page>'''], type='http', auth="public", website=True)
    def help_page(self, help_group, help_page, enable_editor=None, **post):
        """Displays help page template"""
        if help_group.website_published and help_page.website_published and (request.env.user in help_group.sudo().group_ids.users or len(help_group.group_ids) == 0):
            return http.request.render("website_support.help_page", {'help_page':help_page})
        else:
            return request.render('website.404')

    @http.route('/support/ticket/process', type="http", auth="public", website=True, csrf=True)
    def support_process_ticket(self, **kwargs):
        """Adds the support ticket to the database and sends out emails to everyone following the support ticket category"""
        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        if values['my_gold'] != "256":
            return "Bot Detected"

        # website = request.env['website'].get_current_website()
        # if website:
        #     recaptcha_site_key = website.recaptcha_site_key
        #     # Redirect them back if they didn't answer the captcha
        #     if 'g-recaptcha-response' not in values:
        #         return werkzeug.utils.redirect("/support/ticket/submit")
        #
        #     payload = {'secret': recaptcha_site_key, 'response': str(values['g-recaptcha-response'])}
        #     response_json = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload)
        #
        #     if response_json.json()['success'] is not True:
        #         er = response_json.json()['error-codes']
        #         return werkzeug.utils.redirect("/support/ticket/submit" + "?error_captcha={0}" % er)
        my_attachment = ""
        file_name = ""

        create_dict = {'person_name':values['person_name'],'phone':values['phone'],'department':values['department'], 'category_id': values['category'], 'email':values['email'], 'description':values['description'], 'subject':values['subject'], 'attachment': my_attachment, 'attachment_filename': file_name}

        create_dict['channel'] = 'website'
        if http.request.env.user.name != "Public user":
            partner = http.request.env.user.partner_id
            create_dict['partner_id'] = partner.id
            #Add to the communication history of the logged in user
            partner.message_post(body="Customer " + partner.name + " has sent in a new support ticket", subject="New Support Ticket")
        else:
            #Automatically assign the partner if email matches
            search_partner = request.env['res.partner'].sudo().search([('email','=', values['email'] )])
            if len(search_partner) > 0:
                create_dict['partner_id'] = search_partner[0].id

        new_ticket_id = request.env['website.support.ticket'].sudo().create(create_dict)

        if 'file' in values:

            for c_file in request.httprequest.files.getlist('file'):
                data = c_file.read()

                if c_file.filename:
                    request.env['vnitpro.base.attachment'].sudo().create({
                        'file_name': c_file.filename,
                        'file': base64.b64encode(data),
                        'user_id': http.request.env.user.id,
                        'support_ticket_id': new_ticket_id.id
                    })

        return werkzeug.utils.redirect("/support/ticket/thanks")


    @http.route('/support/ticket/thanks', type="http", auth="public", website=True)
    def support_ticket_thanks(self, **kw):
        """Displays a thank you page after the user submits a ticket"""
        return http.request.render('website_support.support_thank_you', {})

    @http.route('/support/ticket/view', type="http", auth="user", website=True)
    def support_ticket_view_list(self, **kw):
        """Displays a list of support tickets owned by the logged in user"""

        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value
        
        #Determine which tickets the logged in user can see
        ticket_access = []
        
        #Can see own tickets
        ticket_access.append(http.request.env.user.partner_id.id)

        #If the logged in user is a department manager then add all the contacts in the department to the access list
        # for dep in request.env['website.support.department.contact'].sudo().search([('user_id','=',http.request.env.user.id)]):
        #     for contact in dep.wsd_id.partner_ids:
        #         ticket_access.append(contact.id)

        search_t = [('partner_id', 'in', ticket_access), ('partner_id','!=',False)]
        
        if 'state' in values:
            search_t.append(('state_id', '=', int(values['state'])))

        support_tickets = request.env['website.support.ticket'].sudo().search(search_t)

        # no_approval_required = request.env['ir.model.data'].get_object('website_support','no_approval_required')
        change_requests = request.env['website.support.ticket'].sudo().search([('partner_id', 'in', ticket_access), ('partner_id','!=',False)], order="planned_time desc")

        ticket_states = request.env['vnitpro.maintenance.stage'].sudo().search([])

        return request.render('website_support.support_ticket_view_list', {'support_tickets':support_tickets,'ticket_count':len(support_tickets), 'change_requests': change_requests, 'request_count': len(change_requests), 'ticket_states': ticket_states})

    @http.route('/support/ticket/view/<ticket>', type="http", auth="user", website=True)
    def support_ticket_view(self, ticket):
        """View an individual support ticket"""

        #Determine which tickets the logged in user can see
        ticket_access = []
        
        #Can see own tickets
        ticket_access.append(http.request.env.user.partner_id.id)

        #If the logged in user is a department manager then add all the contacts in the department to the access list
        # for dep in request.env['website.support.department.contact'].sudo().search([('user_id','=',http.request.env.user.id)]):
        #     for contact in dep.wsd_id.partner_ids:
        #         ticket_access.append(contact.id)

        setting_max_ticket_attachments = request.env['ir.default'].get('website.support.settings', 'max_ticket_attachments')
        setting_max_ticket_attachment_filesize = request.env['ir.default'].get('website.support.settings', 'max_ticket_attachment_filesize')

        # Only let the user this ticket is assigned to view this ticket
        support_ticket = http.request.env['website.support.ticket'].sudo().search([('partner_id', 'in', ticket_access), ('partner_id','!=',False), ('id','=',ticket) ])[0]
        return http.request.render('website_support.support_ticket_view', {'support_ticket':support_ticket, 'setting_max_ticket_attachments': setting_max_ticket_attachments, 'setting_max_ticket_attachment_filesize': setting_max_ticket_attachment_filesize})

    @http.route('/support/portal/ticket/view/<portal_access_key>', type="http", auth="public", website=True)
    def support_portal_ticket_view(self, portal_access_key):
        """View an individual support ticket (portal access)"""

        support_ticket = http.request.env['website.support.ticket'].sudo().search([('portal_access_key','=',portal_access_key) ])[0]
        return http.request.render('website_support.support_ticket_view', {'support_ticket':support_ticket, 'portal_access_key': portal_access_key})

    @http.route('/support/portal/ticket/comment', type="http", auth="public", website=True)
    def support_portal_ticket_comment(self, **kw):
        """Adds a comment to the support ticket"""

        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value

        support_ticket = http.request.env['website.support.ticket'].sudo().search([('portal_access_key','=', values['portal_access_key'] ) ])[0]

        request.env['website.support.ticket.message'].sudo().create({'ticket_id':support_ticket.id, 'by': 'customer','content':values['comment']})

        support_ticket.state_id = request.env['ir.model.data'].sudo().get_object('website_support', 'website_ticket_state_customer_replied')


        attachments = []
        if 'file' in values:

            for c_file in request.httprequest.files.getlist('file'):
                data = c_file.read()

                if c_file.filename:
                    request.env['vnitpro.base.attachment'].sudo().create({
                        'file_name': c_file.filename,
                        'file': base64.b64encode(data),
                        'user_id': http.request.env.user.id,
                        'support_ticket_id': support_ticket.id
                    })
                    attachments.append( (c_file.filename, data) )

        request.env['website.support.ticket'].sudo().browse(support_ticket.id).message_post(body=values['comment'], subject="Support Ticket Reply", message_type="comment", attachments=attachments)

        return werkzeug.utils.redirect("/support/portal/ticket/view/" + str(support_ticket.portal_access_key) )

    @http.route('/support/ticket/comment',type="http", auth="user")
    def support_ticket_comment(self, **kw):
        """Adds a comment to the support ticket"""

        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value

        ticket = http.request.env['website.support.ticket'].sudo().search([('id','=',values['ticket_id'])])

        # Only the ticket owner can comment on the ticket, no department managers
        if ticket.partner_id.id == http.request.env.user.partner_id.id:

            request.env['website.support.ticket.message'].sudo().create({'ticket_id':ticket.id, 'by': 'customer','content':values['comment']})
            # ticket.state_id = request.env['ir.model.data'].sudo().get_object('website_support', 'website_ticket_state_customer_replied')

            attachments = []
            if 'file' in values:

                for c_file in request.httprequest.files.getlist('file'):
                    data = c_file.read()

                    if c_file.filename:
                        request.env['vnitpro.base.attachment'].sudo().create({
                            'file_name': c_file.filename,
                            'file': base64.b64encode(data),
                            'user_id': http.request.env.user.id,
                            'support_ticket_id': ticket.id
                        })

                        attachments.append( (c_file.filename, data) )

            message_post = ticket.sudo().message_post(body=values['comment'], subject="Support Ticket Reply", message_type="comment", attachments=attachments)
            message_post.author_id = request.env.user.partner_id.id
        else:
            return "You do not have permission to submit this commment"

        return werkzeug.utils.redirect("/support/ticket/view/" + str(ticket.id))

    @http.route('/support/ticket/close',type="http", auth="user")
    def support_ticket_close(self, **kw):
        """Close the support ticket"""

        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value

        ticket = http.request.env['website.support.ticket'].sudo().search([('id','=',values['ticket_id'])])

        #check if this user owns this ticket
        if ticket.partner_id.id == http.request.env.user.partner_id.id or ticket.partner_id in http.request.env.user.partner_id.stp_ids:

            # customer_closed_state = request.env['ir.model.data'].sudo().get_object('website_support', 'website_ticket_state_customer_closed')
            # ticket.state_id = customer_closed_state

            ticket.close_time = datetime.datetime.now()
            ticket.close_date = datetime.date.today()

            diff_time = ticket.close_time - ticket.create_date
            ticket.time_to_close = diff_time.seconds

            # ticket.sla_active = False
            # closed_state_mail_template = customer_closed_state.mail_template_id
            #
            # if closed_state_mail_template:
            #     closed_state_mail_template.send_mail(ticket.id, True)

        else:
            return "You do not have permission to close this commment"

        return werkzeug.utils.redirect("/support/ticket/view/" + str(ticket.id))

    @http.route('/support/help/auto-complete',auth="public", website=True, type='http')
    def support_help_autocomplete(self, **kw):
        """Provides an autocomplete list of help pages"""
        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value

        return_string = ""

        my_return = []

        help_pages = request.env['website.support.help.page'].sudo().search([('name','=ilike',"%" + values['term'] + "%")],limit=5)

        for help_page in help_pages:
            return_item = {"label": help_page.name,"value": "/support/help/" + slug(help_page.group_id) + "/" + slug(help_page) }
            my_return.append(return_item) 

        return json.JSONEncoder().encode(my_return)