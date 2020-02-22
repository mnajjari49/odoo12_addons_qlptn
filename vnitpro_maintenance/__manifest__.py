# -*- coding: utf-8 -*-

{
    'name': 'SCI Maintenance',
    'version': '1.0',
    'sequence': 125,
    'category': 'Human Resources',
    'description': """
        Track equipments and maintenance requests""",
    'summary': 'Track equipment and manage maintenance requests',
    'website': 'https://www.odoo.com/page/tpm-maintenance-software',
    'depends': ['mail', 'hr', 'vnitpro_device'],
    'data': [
        'security/maintenance.xml',
        'security/ir.model.access.csv',
        'data/maintenance_data.xml',
        'data/ir_cron_data.xml',
        'views/maintenance_views.xml',
        'views/device_main_views.xml',
        'views/equipment_export_view.xml',
        'views/hr_employee_view.xml',
    ],
    'demo': ['data/maintenance_demo.xml'],
    'installable': True,
    'application': True,
}
