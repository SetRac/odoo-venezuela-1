# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Nhomar Hernandez <nhomar@vauxoo.com>
#
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
#
##############################################################################
from osv import osv
from osv import fields
from tools.translate import _
import addons
import base64

class wh_vat_installer(osv.osv_memory):
    """
    wh_vat_installer
    """
    _name='l10n_ve_withholding_iva.installer'
    _inherit = 'res.config.installer'
    _description = __doc__
    
    def default_get(self, cr, uid, fields, context=None):
        data = super(wh_vat_installer, self).default_get(cr, uid, fields, context=context)
        gaceta = open(addons.get_module_resource('l10n_ve_withholding_iva','files', 'RegimendeRetencionesdelIVA.odt'),'rb')
        data['gaceta'] = base64.encodestring(gaceta.read())
        return data
    
    _columns = {
        'name':fields.char('First Data', 34),
        'gaceta':fields.binary('Law related', readonly=True, help="Law related where we are referencing this module"),
        'description':fields.text('Description', readonly=True),
    }
    
    _defaults = {
        'name' : 'RegimendeRetencionesdelIVA.odt',
        'description' : """
        With this wizard you will configure all needs for work out of the box with 
        This module,
        First: Setting if The company will be withholding agent.
        Second: Create Minimal Journals.
        Third: Assign Account to work.
        Fourth: Ask if you have internet conexion and you want to connect to SENIAT
        and update all your partners information.
        """
    }
wh_vat_installer()

class wh_iva_config(osv.osv_memory):
    _name = 'wh_iva.config'
    _inherit = 'res.config'

    _columns = {
        'name': fields.char('Name', 64),
        'wh':fields.boolean('Are You Withholding Agent?'),
        #Move this action to withholding base.
        'vat':fields.char('Give VAT Number for your company.',12, help='Put your VAT number with this format VEYXXXXXXXX Where Y can be J-G-V-E and the rest are just numeric'),
    }
    _defaults = {
        'wh': True,
        'vat': 'VEJ147744443',
        'add': 'Av XXXX con Calle YYY Estado SSSS No 0000',
    }

    def _show_company_data(self, cr, uid, context=None):
        '''
        We only want to show the default company data in demo mode, otherwise users tend to forget
        to fill in the real company data in their production databases
        '''
        return self.pool.get('ir.model.data').get_object(cr, uid, 
                                                            'base',
                                             'module_meta_information').demo

    def default_get(self, cr, uid, fields_list=None, context=None):
        """ get default company if any, and the various other fields
        from the company's fields
        """
        defaults = super(wh_iva_config, self)\
              .default_get(cr, uid, fields_list=fields_list, context=context)
        user=self.pool.get('res.users').browse(cr,uid,[uid],context)
        pa_obj=self.pool.get('res.partner.address')
        #Set Vauxoo logo on config Window.
        logo = open(addons.get_module_resource('l10n_ve_withholding_iva',
                                            'images', 'angelfalls.jpg'),'rb')
        defaults['config_logo'] = base64.encodestring(logo.read())
        if not self._show_company_data(cr, uid, context=context):
            defaults['add']=''
            defaults['vat']=''
            return defaults
        return defaults

    def execute(self, cr, uid, ids, context=None):
        '''
        In this method I will configure all needs for work out of the box with 
        This module,
        First: Setting if The company will be agent of retention.
        Second: Create Minimal Journals.
        Third: Assign Account to work.
        Fourth: Ask if you have internet conexion and you want to connect to 
        SENIAT
        and update all your partners information.
        '''
        user=self.pool.get('res.users').browse(cr,uid,[uid],context)
        wiz=self.browse(cr,uid,ids,context)[0]
        p_obj=self.pool.get('res.partner')
        pa_obj=self.pool.get('res.partner.address')
        partner_id=user[0].company_id.partner_id.id
        if wiz.wh:
            p_obj.write(cr,uid,[partner_id],{'wh_iva_agent':1,
                                            'wh_iva_rate':75.00})
        else:
            p_obj.write(cr,uid,[partner_id],{'wh_iva_agent':0,
                                            'wh_iva_rate':75.00})
        if wiz.vat:
            add_ids=pa_obj.search(cr,uid,
                            [('partner_id','=',user[0].company_id.partner_id.id),
                            ('type','=','invoice')])
            if not add_ids:
                pa_obj.create(cr,uid,{'type':'invoice',
                                    'street':wiz.add ,
                                    'partner_id':partner_id},context)
            p_obj.write(cr,uid,[partner_id],{'vat':wiz.vat})

wh_iva_config()
