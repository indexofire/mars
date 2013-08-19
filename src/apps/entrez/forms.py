# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from entrez.models import EntrezTerm


class BootstrapForm(object):
    """
    Inherit with forms.Form or forms.ModelForm
    For example:
        class AnyForm(forms.Form, BootstrapForm):
            pass

        class AnyModelForm(forms.ModelForm, BootstrapForm):
            pass
    """

    def render_errors(self):
        if not self.errors:
            return ""
        output = []
        output.append(u'<div class="alert-message block-message error">')
        output.append(u'<a class="close" href="#">×</a>')
        output.append(u'<p><strong>%s</strong></p><ul>' % _('You got an error!'))
        for field, error in self.errors.items():
            output.append(u'<li><strong>%s</strong> %s</li>' % (field.title(), error[0]))
        output.append(u'</ul></div>')
        return mark_safe(u'\n'.join(output))

    def as_bootstrap(self):
        output = []
        #see original Form class __iter__ method
        for boundfield in self:
            row_template = u'''
            <div class="%(div_class)s %(required_label)s">
              %(label)s
              <div class="controls">
                %(field)s
                <span class="help-block">%(help_text)s</span>
              </div>
            </div>
            '''
            row_dict = {
                "div_class": "control-group",
                "required_label": boundfield.css_classes(),
                "field": boundfield.as_widget(),
                "label": boundfield.label_tag(attrs={'class': 'control-label', }),
                "help_text": boundfield.help_text,
            }

            if boundfield.errors:
                row_dict["div_class"] = "error"
                boundfield.field.widget.attrs["class"] = "error"

            output.append(row_template % row_dict)
        return mark_safe(u'\n'.join(output))


class AddTermForm(forms.ModelForm, BootstrapForm):
    class Meta:
        model = EntrezTerm
        exclude = ('owner', 'creation_date', 'lastedit_date', 'status')
