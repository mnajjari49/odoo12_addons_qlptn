# -*- coding: utf-8 -*-
###############################################################################
#
#    Công ty giải pháp phần mềm VNITPro.
#    Copyright (C) 2018-TODAY VNITPro(<http://vnitpro.vn>).
#
###############################################################################


{
    'name': 'Base-VNITPro',
    'description': 'Base module',
    'summary': 'Base module in VNITPro ERP',
    'category': 'base',
    "sequence": 2,
    'version': '1.0.0',
    'author': 'VNITPro',
    'website': 'http://vnitpro.vn',
    'depends': ['base', 'mail', 'board', 'web'],
    'demo': [
        'demo/mail_server_demo.xml',
        'demo/company_demo.xml',
    ],
    'data': [
        'views/asset_view.xml',
        'views/vnitpro_template.xml',
        'report/report_template.xml',
        'menu/system_sequence_menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
