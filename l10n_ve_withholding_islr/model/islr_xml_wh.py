#!/usr/bin/python
# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
###############Credits######################################################
#    Coded by: Humberto Arocha           <humberto@openerp.com.ve>
#              Maria Gabriela Quilarque  <gabrielaquilarque97@gmail.com>
#              Javier Duran              <javier@vauxoo.com>             
#    Planified by: Nhomar Hernandez
#    Finance by: Helados Gilda, C.A. http://heladosgilda.com.ve
#    Audited by: Humberto Arocha humberto@openerp.com.ve
#############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
from openerp.tools import config
import time
import datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
import sys
import base64
from openerp.addons import decimal_precision as dp

class islr_xml_wh_doc(osv.osv):
    _name = "islr.xml.wh.doc"
    _description = 'Generate XML'

    def _get_amount_total(self,cr,uid,ids,name,args,context=None):
        """ Return withhold total amount
        """
        res = {}
        for xml in self.browse(cr,uid,ids,context):
            res[xml.id]= 0.0
            for line in xml.xml_ids:
                res[xml.id] += line.wh
        return res

    def _get_amount_total_base(self,cr,uid,ids,name,args,context=None):
        """ Return base total amount
        """
        res = {}
        for xml in self.browse(cr,uid,ids,context):
            res[xml.id]= 0.0
            for line in xml.xml_ids:
                res[xml.id] += line.base
        return res

    _columns = {
        'name':fields.char('Description',128, required=True, select=True, help = "Description about statement of income withholding"),
        'company_id': fields.many2one('res.company', 'Company', required=True, help="Company"),
        'state': fields.selection([
            ('draft','Draft'),
            ('confirmed', 'Confirmed'),
            ('done','Done'),
            ('cancel','Cancelled')
            ],'State', readonly=True, help="Voucher state"),
        'period_id':fields.many2one('account.period','Period',required=True, help="Period when the accounts entries were done"),
        'amount_total_ret':fields.function(_get_amount_total,method=True, digits=(16, 2), readonly=True, string='Income Withholding Amount Total', help="Amount Total of withholding"),
        'amount_total_base':fields.function(_get_amount_total_base,method=True, digits=(16, 2), readonly=True, string='Without Tax Amount Total', help="Total without taxes"),
        'xml_ids':fields.one2many('islr.xml.wh.line','islr_xml_wh_doc','XML Document Lines', readonly=True ,states={'draft':[('readonly',False)]}, help='XML withhold invoice line id'),
        'user_id': fields.many2one('res.users', 'Salesman', readonly=True, states={'draft':[('readonly',False)]}, help='Vendor user'),
    }
    _defaults = {
        'state': lambda *a: 'draft',
        'company_id': lambda self, cr, uid, context: \
                self.pool.get('res.users').browse(cr, uid, uid,
                    context=context).company_id.id,
        'user_id': lambda s, cr, u, c: u,

        'period_id': lambda self,cr,uid,context: self.period_return(cr,uid,context),
        'name':lambda self,cr,uid,context : 'Income Withholding '+time.strftime('%m/%Y')
    }

    def period_return(self,cr,uid,context=None):
        """ Return current period
        """
        period_obj = self.pool.get('account.period')
        fecha = time.strftime('%m/%Y')
        period_id = period_obj.search(cr,uid,[('code','=',fecha)])
        if period_id:
            return period_id[0]
        else:
            return False

    def search_period(self,cr,uid,ids,period_id,context=None):
        """ Return islr lines associated with the period_id
        @param period_id: period associated with returned islr lines
        """
        if context is None:
            context = {}
        res ={'value':{}}
        if period_id:
            islr_line = self.pool.get('islr.xml.wh.line')
            islr_line_ids = islr_line.search(cr,uid,[('period_id','=',period_id)],context=context)
            if islr_line_ids:
                res['value'].update({'xml_ids':islr_line_ids})
                return res
                
    def name_get(self, cr, uid, ids, context={}):
        """ Return id and name of all records
        """
        if not len(ids):
            return []
        
        res = [(r['id'], r['name']) for r in self.read(cr, uid, ids, ['name'], context)]
        return res

    def action_anular1(self, cr, uid, ids, context={}):
        """ Return the document to draft status
        """
        return self.write(cr, uid, ids, {'state':'draft'})

    def action_confirm1(self, cr, uid, ids, context={}):
        """ Passes the document to state confirmed
        """
        return self.write(cr, uid, ids, {'state':'confirmed'})

    def action_done1(self, cr, uid, ids, context={}):
        """ Passes the document to state done
        """
        root = self._xml(cr,uid,ids)
        self._write_attachment(cr,uid,ids,root,context)
        self.write(cr, uid, ids, {'state':'done'})
        return True

    def _write_attachment(self, cr,uid,ids,root,context):
        """ Codify the xml, to save it in the database and be able to 
        see it in the client as an attachment
        @param root: data of the document in xml
        """
        fecha = time.strftime('%Y_%m_%d_%H%M%S')
        name = 'ISLR_' + fecha +'.'+ 'xml'
        self.pool.get('ir.attachment').create(cr, uid, {
            'name': name,
            'datas': base64.encodestring(root),
            'datas_fname': name,
            'res_model': 'islr.xml.wh.doc',
            'res_id': ids[0],
            }, context=context
        )
        cr.commit()
        self.log(cr, uid, ids[0], _("File XML %s generated.") % name)

    def indent(self,elem, level=0):
        """ Return indented text
        @param level: number of spaces for indentation
        @param elem: text to indentig
        """
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


    def _xml(self, cr,uid,ids):
        """ Transform this document to XML format
        """
        root = ''
        for id in ids:
            wh_brw = self.browse(cr,uid,id)
            
            period = time.strptime(wh_brw.period_id.date_stop,'%Y-%m-%d')
            period2 = "%02d%0004d"%(period.tm_mon,period.tm_year)

            sql= '''SELECT partner_vat,control_number,porcent_rete,concept_code,invoice_number, SUM(COALESCE(base,0)) as base,account_invoice_id
            FROM islr_xml_wh_line 
            WHERE period_id= %s and id in (%s)
            GROUP BY partner_vat,control_number,porcent_rete,concept_code,invoice_number,account_invoice_id'''%(wh_brw.period_id.id,', '.join([str(i.id) for i in wh_brw.xml_ids]))
            cr.execute(sql)
            xml_lines=cr.fetchall()

            root = Element("RelacionRetencionesISLR")
            root.attrib['RifAgente'] = wh_brw.company_id.partner_id.vat[2:]
            root.attrib['Periodo'] = period2
            for line in xml_lines:
                partner_vat,control_number,porcent_rete,concept_code,invoice_number,base,inv_id=line
                detalle = SubElement(root,"DetalleRetencion")
                SubElement(detalle, "RifRetenido").text = partner_vat
                SubElement(detalle, "NumeroFactura").text =invoice_number
                SubElement(detalle, "NumeroControl").text = control_number
                SubElement(detalle, "CodigoConcepto").text = concept_code
                SubElement(detalle, "MontoOperacion").text = str(base)
                SubElement(detalle, "PorcentajeRetencion").text = str(porcent_rete)
        #~ ElementTree(root).write("/home/gabriela/openerp/Gabriela/5.0/Helados Gilda/islr_withholding/xml.xml")
        self.indent(root)
        return tostring(root,encoding="ISO-8859-1")

islr_xml_wh_doc()


class islr_xml_wh_line(osv.osv):
    _name = "islr.xml.wh.line"
    _description = 'Generate XML Lines'
    
    _columns = {
        'concept_id': fields.many2one('islr.wh.concept','Withholding Concept',help="Withholding concept associated with this rate",required=True, ondelete='cascade'),
        'period_id':fields.many2one('account.period','Period',required=False, help="Period when the journal entries were done"),
        'partner_vat': fields.char('VAT', size=10, required=True, help="Partner VAT"),
        'invoice_number': fields.char('Invoice Number',size=10,required=True, help="Number of invoice"),
        'control_number': fields.char('Control Number',size=8,required=True, help="Reference"),
        'concept_code': fields.char('Concept Code', size=10, required=True, help="Concept code"),
        'base': fields.float('Base Amount', required=True, help="Amount where a withholding is going to be computed from", digits_compute= dp.get_precision('Withhold ISLR')),
        'porcent_rete': fields.float('Withholding Rate', required=True, help="Withholding Rate", digits_compute= dp.get_precision('Withhold ISLR')),
        'wh':fields.float('Withheld Amount',required=True, help="Withheld amount to partner", digits_compute= dp.get_precision('Withhold ISLR')),
        'rate_id':fields.many2one('islr.rates', 'Person Type',domain="[('concept_id','=',concept_id)]",required=True, help="Person type"),
        'islr_wh_doc_line_id':fields.many2one('islr.wh.doc.line','Income \
            Withholding Document', ondelete='cascade', help="Income Withholding\
            Document"),
        'account_invoice_line_id':fields.many2one('account.invoice.line','Invoice Line', help="Invoice line to Withhold"),
        'account_invoice_id':fields.many2one('account.invoice','Invoice', help="Invoice to Withhold"),
        'islr_xml_wh_doc': fields.many2one('islr.xml.wh.doc','ISLR XML Document', help="Income tax XML Doc"),
        'partner_id': fields.many2one('res.partner','Partner',required=True, help="Partner object of withholding"),
        'sustract': fields.float('Subtrahend', help="Subtrahend", digits_compute= dp.get_precision('Withhold ISLR')),
        'islr_wh_doc_inv_id': fields.many2one('islr.wh.doc.invoices','Withheld Invoice',help="Withheld Invoices"),
    }
    _rec_name = 'partner_id'
    
    _defaults = {
        'invoice_number': lambda *a: '0',
        'control_number': lambda *a: '0',
    }

    def onchange_partner_vat(self, cr, uid, ids, partner_id, context={}):
        """ Changing the partner, the partner_vat field is updated.
        """
        partner_brw = self.pool.get('res.partner').browse(cr,uid,partner_id)
        return {'value' : {'partner_vat':partner_brw.vat[2:]}} 
        
        
    def onchange_code_perc(self, cr, uid, ids, rate_id, context={}):
        """ Changing the rate of the islr, the porcent_rete and concept_code fields
        is updated.
        """
        rate_brw = self.pool.get('islr.rates').browse(cr,uid,rate_id)
        return {'value' : {'porcent_rete':rate_brw.wh_perc,'concept_code':rate_brw.code}} 

islr_xml_wh_line()

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"

    _columns = {
        'wh_xml_id':fields.many2one('islr.xml.wh.line','XML Id', help="XML withhold line id"),
    }
    _defaults = {
        'wh_xml_id': lambda *a: 0,
    }
account_invoice_line()
