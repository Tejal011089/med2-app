from __future__ import unicode_literals
import webnotes
import webnotes.model.doc
import webnotes.model.doctype
from webnotes.model.doc import Document
from webnotes.utils import cstr, cint, flt,add_days
from webnotes.utils.datautils import UnicodeWriter
from webnotes import _
import datetime
from datetime import date,timedelta
import dateutil
import calendar
from webnotes.utils import nowdate
from webnotes.utils import validate_email_add

sql = webnotes.conn.sql

data_keys = webnotes._dict({
        "data_separator": 'Start entering data below this line',
        "main_table": "Table:",
        "parent_table": "Parent Table:",
        "columns": "Column Name:"
})

doctype_dl = None

@webnotes.whitelist()
def get_doctypes():
    return [r[0] for r in webnotes.conn.sql("""select name from `tabDocType` 
                where document_type = 'Master' or allow_import = 1""")]


@webnotes.whitelist()
def get_doctype_options():
        doctype = webnotes.form_dict['doctype']
        return [doctype] + filter(None, map(lambda d: \
                d.doctype=='DocField' and d.fieldtype=='Table' and d.options or None,
                webnotes.model.doctype.get(doctype)))

@webnotes.whitelist()
def get_template():
        global doctype_dl

        doctype = webnotes.form_dict['doctype']
        parenttype = webnotes.form_dict.get('parent_doctype')

        doctype_dl = webnotes.model.doctype.get(doctype)
        tablecolumns = [f[0] for f in webnotes.conn.sql('desc `tab%s`' % doctype)]

        def getinforow(docfield):
                """make info comment"""
                if docfield.fieldtype == 'Select':
                        if not docfield.options:
                                return ''
                        elif docfield.options.startswith('link:'):
                                return 'Valid %s' % docfield.options[5:]
                        else:
                                return 'One of: %s' % ', '.join(filter(None, docfield.options.split('\n')))
                if docfield.fieldtype == 'Link':
                        return 'Valid %s' % docfield.options
                if docfield.fieldtype in ('Int'):
                        return 'Integer'
                if docfield.fieldtype == "Check":
                        return "0 or 1"
                else:
                        return ''

        w = UnicodeWriter()
        key = 'name'

        w.writerow(['Data Import Template'])
        w.writerow([data_keys.main_table, doctype])

        if parenttype != doctype:
                w.writerow([data_keys.parent_table, parenttype])
                key = 'parent'
        else:
                w.writerow([''])

        w.writerow([''])
        w.writerow(['Notes:'])
        w.writerow(['Please do not change the template headings.'])
        w.writerow(['First data column must be blank.'])
        w.writerow(['Only mandatory fields are necessary for new records. You can delete non-mandatory columns if you wish.'])
        w.writerow(['For updating, you can update only selective columns.'])
        w.writerow(['If you are uploading new records, leave the "name" (ID) column blank.'])
        w.writerow(['If you are uploading new records, "Naming Series" becomes mandatory, if present.'])
        w.writerow(['You can only upload upto 5000 records in one go. (may be less in some cases)'])
        if key == "parent":
                w.writerow(['"Parent" signifies the parent table in which this row must be added'])
                w.writerow(['If you are updating, please select "Overwrite" else existing rows will not be deleted.'])
        w.writerow([''])
        labelrow = ["Column Labels", "ID"]
        fieldrow = [data_keys.columns, key]
        mandatoryrow = ['Mandatory:', 'Yes']
        typerow = ['Type:', 'Data (text)']
        inforow = ['Info:', '']
        columns = [key]

        def append_row(t, mandatory):
                docfield = doctype_dl.get_field(t)

                if docfield and ((mandatory and docfield.reqd) or not (mandatory or docfield.reqd)) \
                        and (t not in ('parenttype', 'trash_reason')) and not docfield.hidden:
                        fieldrow.append(t)
                        labelrow.append(docfield.label)
                        mandatoryrow.append(docfield.reqd and 'Yes' or 'No')
                        typerow.append(docfield.fieldtype)
                        inforow.append(getinforow(docfield))
                        columns.append(t)

        # get all mandatory fields
        for t in tablecolumns:
                append_row(t, True)

        # all non mandatory fields
        for t in tablecolumns:
                append_row(t, False)

        w.writerow(labelrow)
        w.writerow(fieldrow)
        w.writerow(mandatoryrow)
        w.writerow(typerow)
        w.writerow(inforow)

        w.writerow([data_keys.data_separator])

        if webnotes.form_dict.get('with_data')=='Yes':
                data = webnotes.conn.sql("""select * from `tab%s` where docstatus<2""" % doctype, as_dict=1)
                for d in data:
                        row = [""]
                        for c in columns:
                                row.append(d.get(c, ""))
                        w.writerow(row)

        # write out response as a type csv
        webnotes.response['result'] = cstr(w.getvalue())
        webnotes.response['type'] = 'csv'
        webnotes.response['doctype'] = doctype

@webnotes.whitelist()
def upload():
        webnotes.errprint("hello")
        from webnotes.utils.file_manager import get_uploaded_content
        """upload data"""
        global doctype_dl

        #webnotes.mute_emails = True
        from webnotes.utils.datautils import read_csv_content_from_uploaded_file

        # extra input params
        import json
        params = json.loads(webnotes.form_dict.get("params") or '{}')

        # header
        rows = read_csv_content_from_uploaded_file()
        i=0
        for r in rows:
                if i>1:
				#webnotes.errprint(r[2])
				
                                aa=datetime.datetime.strptime(r[2], '%d-%b-%y').date().strftime('%Y-%m-%d')
                                bb=Document('Attendance')
                                bb.employee=r[0]
                                webnotes.errprint(r[0])
                                dd="select employee_name from tabEmployee where name='"+r[0]+"'"
                                #webnotes.errprint(dd)
                                cc=webnotes.conn.sql(dd)
                                bb.employee_name=cc and cc[0][0] or ''
                                #webnotes.errprint(cc)
                                bb.status='Present'
                                bb.att_date=aa
                                bb.company='MedSynaptic'
				bb.fiscal_year='2014-2015'
                                bb.save(new=1)
                                webnotes.conn.commit()
                                #webnotes.errprint(bb)  
                i+=1

        return "Attendace successfully Uploaded..!"


def get_parent_field(doctype, parenttype):
        parentfield = None
        # get parentfield
        if parenttype:
                for d in webnotes.model.doctype.get(parenttype):
                        if d.fieldtype=='Table' and d.options==doctype:
                                parentfield = d.fieldname
                                break

                if not parentfield:
                        webnotes.msgprint("Did not find parentfield for %s (%s)" % \
                                (parenttype, doctype))
                        raise Exception

        return parentfield

def check_record(d, parenttype=None):
        """check for mandatory, select options, dates. these should ideally be in doclist"""

        from webnotes.utils.dateutils import parse_date
        if parenttype and not d.get('parent'):
                raise Exception, "parent is required."

        global doctype_dl
        if not doctype_dl:
                doctype_dl = webnotes.model.doctype.get(d.doctype)

        for key in d:
                docfield = doctype_dl.get_field(key)
                val = d[key]
                if docfield:
                        if docfield.reqd and (val=='' or val==None):
                                raise Exception, "%s is mandatory." % key

                        if docfield.fieldtype=='Select' and val and docfield.options:
                                if docfield.options.startswith('link:'):
                                        link_doctype = docfield.options.split(':')[1]
                                        if not webnotes.conn.exists(link_doctype, val):
                                                raise Exception, "%s must be a valid %s" % (key, link_doctype)
                                elif docfield.options == "attach_files:":
                                        pass
                                elif val not in docfield.options.split('\n'):
                                        raise Exception, "%s must be one of: %s" % (key,
                                                ", ".join(filter(None, docfield.options.split("\n"))))

                        if val and docfield.fieldtype=='Date':
                                d[key] = parse_date(val)
                        elif val and docfield.fieldtype in ["Int", "Check"]:
                                d[key] = cint(val)
                        elif val and docfield.fieldtype in ["Currency", "Float"]:
                                d[key] = flt(val)

def getlink(doctype, name):
        return '<a href="#Form/%(doctype)s/%(name)s">%(name)s</a>' % locals()

def delete_child_rows(rows, doctype):
        """delete child rows for all parents"""
        for p in list(set([r[1] for r in rows])):
                webnotes.conn.sql("""delete from `tab%s` where parent=%s""" % (doctype, '%s'), p)

def import_doc(d, doctype, overwrite, row_idx, submit=False):
        """import main (non child) document"""
        if webnotes.conn.exists(doctype, d['name']):
                if overwrite:
                        bean = webnotes.bean(doctype, d['name'])
                        bean.doc.fields.update(d)
                        if d.get("docstatus") == 1:
                                bean.update_after_submit()
                        else:
                                bean.save()
                        return 'Updated row (#%d) %s' % (row_idx, getlink(doctype, d['name']))
                else:
                        return 'Ignored row (#%d) %s (exists)' % (row_idx,
                                getlink(doctype, d['name']))
        else:
                bean = webnotes.bean([d])
                bean.insert()

                if submit:
                        bean.submit()

                return 'Inserted row (#%d) %s' % (row_idx, getlink(doctype,
                        bean.doc.fields['name']))

