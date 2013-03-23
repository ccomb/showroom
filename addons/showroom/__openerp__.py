#==============================================================================
#                                                                             =
#    showroom module for OpenERP, showroom
#    Copyright (C) 2013 Gorfou (<http://http://gorfou.fr>)
#                         Christophe Combelles <ccomb@gorfou.fr>
#                                                                             =
#    This file is a part of showroom
#                                                                             =
#    showroom is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#                                                                             =
#    showroom is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#                                                                             =
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#                                                                             =
#==============================================================================
{
    'name': 'Showroom',
    'version': '0.1',
    'category': 'showroom',
    'description': """
    Demo management application
    """,
    'author': 'Gorfou',
    'website': 'http://showroom.io',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'groups.xml',
        'view.xml',
        'server/view.xml',
        'server/ir.model.access.csv',
        'template/ir.model.access.csv',
        'template/view.xml',
        'application/ir.model.access.csv',
        'application/view.xml',
        'data/company.xml',
        'data/user.xml',
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'AGPL-3',
}
