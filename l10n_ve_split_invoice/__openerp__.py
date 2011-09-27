# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
###############Credits######################################################
#    Coded by: nhomar@openerp.com.ve,
#    Planified by: Nhomar Hernandez
#    Finance by: Helados Gilda, C.A. http://heladosgilda.com.ve
#    Audited by: Humberto Arocha humberto@openerp.com.ve
#############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

{
    "name" : "Split Invoices",
    "version" : "0.2",
    "depends" : ["account"],
    "author" : "Vauxoo",
    "description" : """
For legal reasons in Venezuela we need just ONE invoice per page, with this module depending on your company configuration you will stablish the number of lines per invoice, with this you will be able of:
 
 1.-Add module for establishing the number of lines per invoice
 2.-Split Invoice according number of lines per invoice once you confirm it.
 """     ,
    "website" : "http://vauxoo.com",
    "category" : "Localization
    "init_xml" : [
    ],
    "demo_xml" : [
    ],
    "update_xml" : [
        "view/company_view.xml",
    ],
    "active": False,
    "installable": True,
}