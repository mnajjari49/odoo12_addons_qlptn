# -*- coding: utf-8 -*-
###############################################################################
#
#    Công ty giải pháp phần mềm VNITPro.
#    Copyright (C) 2018-TODAY VNITPro(<http://vnitpro.vn>).
#    Create by tam.pt
###############################################################################


{
    'name': 'SCI Device Management',
    'description': 'Device Management',
    'summary': 'Device Management',
    'category': 'Construction',
    "sequence": 3,
    'version': '1.0.0',
    'author': 'VNITPro',
    'website': 'http://vnitpro.vn',
    'depends': ['vnitpro_base', 'mail', 'sci_hrms', 'stock', 'hr_employee_updation'],
    'data': [
        'views/dashboard_view.xml',
        'views/device/device_extra.xml',
        'views/device/device_main.xml',
        'views/device/device_parts_in.xml',
        # 'views/general/unit.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'menu/device_menu.xml',
        'data/bien_ban_ban_giao_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
