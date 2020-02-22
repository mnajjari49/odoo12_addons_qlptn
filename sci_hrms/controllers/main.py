# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.addons.website_hr_recruitment.controllers.main import WebsiteHrRecruitment  # Import the class
from odoo.addons.website_form.controllers.main import WebsiteForm  # Import the class
from werkzeug import urls, utils
from odoo.http import request
import base64
import json
from psycopg2 import IntegrityError
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomWebsiteHrRecruitmentController(WebsiteHrRecruitment):

    @http.route('''/jobs/detail/<model("hr.job", "[('website_id', 'in', (False, current_website_id))]"):job>''',
                type='http', auth="public", website=True)
    def jobs_detail(self, job, **kwargs):
        res = super(CustomWebsiteHrRecruitmentController, self).jobs_detail(job, **kwargs)
        if kwargs.get('source'):
            base_url = http.request.env["ir.config_parameter"].sudo().get_param("web.base.url")
            res.set_cookie('job_source', kwargs.get('source'), '/', 'localhost')
            cook_lang = request.httprequest.cookies.get('job_source')
            _logger.info(cook_lang)
        return res


class CustomWebsiteForm(WebsiteForm):

    # Check and insert values from the form on the model <model>
    @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        if model_name == 'hr.applicant':
            model_record = request.env['ir.model'].sudo().search(
                [('model', '=', model_name), ('website_form_access', '=', True)])
            if not model_record:
                return json.dumps(False)

            try:
                data = self.extract_data(model_record, request.params)
                cook_source = request.httprequest.cookies.get('job_source')
                if cook_source:
                    data['record']['source_id'] = cook_source
            # If we encounter an issue while extracting data
            except ValidationError as e:
                # I couldn't find a cleaner way to pass data to an exception
                return json.dumps({'error_fields': e.args[0]})

            try:
                id_record = self.insert_record(request, model_record, data['record'], data['custom'], data.get('meta'))
                if id_record:
                    self.insert_attachment(model_record, id_record, data['attachments'])

            # Some fields have additional SQL constraints that we can't check generically
            # Ex: crm.lead.probability which is a float between 0 and 1
            # TODO: How to get the name of the erroneous field ?
            except IntegrityError:
                return json.dumps(False)

            request.session['form_builder_model_model'] = model_record.model
            request.session['form_builder_model'] = model_record.name
            request.session['form_builder_id'] = id_record

            return json.dumps({'id': id_record})
        else:
            return super(CustomWebsiteForm, self).website_form(model_name, **kwargs)


class WebsiteFormCustom(WebsiteForm):
    @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        if model_name == 'hr.applicant':
            if 'g-recaptcha-response' in kwargs:
                if request.website.is_captcha_valid(kwargs['g-recaptcha-response']):
                    del kwargs['g-recaptcha-response']
                    return super(WebsiteFormCustom, self).website_form(model_name, **kwargs)
                else:
                    return super(WebsiteFormCustom, self).website_form(None, **kwargs)
            else:
                return super(WebsiteFormCustom, self).website_form(None, **kwargs)
        return super(WebsiteFormCustom, self).website_form(model_name, **kwargs)

class WebsiteSearchJob(http.Controller):
    @http.route('/jobs',type='http',auth='public',website=True)
    def search_job(self,search='',industry='',location='',**post):
        industries = request.env['hr.industry.job'].search([])
        domain = [('website_published', '=', True)]
        results = None
        location_dict = {'1': 'Hồ Chí Minh','2': 'Hà Nội','3': 'Bình Dương','4':'Cần Thơ','5':'Đà Nẵng','6':'Hải Phòng','7':'Nghệ An'}
        if search:
            post["search_key"] = search
            domain += [('name', 'ilike', search)]
        if industry:
            post["industry"] = industry
            if industry == 0:
                industry = None
            else:
                domain += [('job_industry.id', '=', industry)]
        if location:
            post['location'] = location
            domain += [('address_location', 'ilike', location_dict[location])]
        results = request.env['hr.job'].sudo().search(domain)
        count = len(results)
        if not results:
            values = {
                'jobs': None,
                'industries': industries,
            }
            return request.render("website_hr_recruitment.index", values)
        else:
            values = {
                'jobs': results,
                'industries': industries,
                'count_result': count,
            }
            return request.render("website_hr_recruitment.index", values)




