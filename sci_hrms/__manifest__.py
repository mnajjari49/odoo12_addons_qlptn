# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
{
    'name': 'SCI HRMS',
    'version': '1.2',
    'category': 'Human Resources',
    'sequence': 1,
    'summary': 'Centralize employee information',
    'description': "",
    'website': 'https://www.odoo.com/page/employees',
    'depends': ['hr','hr_recruitment','hr_contract', 'project','website_hr_recruitment','ohrms_core', 'ms_templates'],
    'data': [
        'data/hr_data.xml',
        'data/hr_job_data.xml',
        'data/ir_cron_data.xml',
        'views/hr_employee_views.xml',
        'views/hr_department_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_applicant_views.xml',
        'views/hr_resignation_view.xml',
        'views/hr_job_views.xml',
        'views/hr_project_views.xml',
        'views/templates.xml',
        'views/views_captcha.xml',
        'views/web.xml',
        'views/website_hr_recruitment_templates.xml',
        'wizard/recruitment_point.xml',
        'wizard/max_emp_report.xml',
        'security/ir.model.access.csv',
        'security/group.xml',
    ],
    'demo': [],
    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
###################################################################################
