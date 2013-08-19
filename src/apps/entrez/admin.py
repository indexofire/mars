# -*- coding: utf-8 -*-
from django.contrib import admin
from entrez.models import EntrezEntry, EntrezTerm


class AdminEntrezEntry(admin.ModelAdmin):
    list_display = ('eid', 'title', 'term', 'owner', 'db')
    list_filter = ('term', 'owner', 'db')
    search_fields = ('title', 'eid')


class AdminEntrezTerm(admin.ModelAdmin):
    pass


admin.site.register(EntrezEntry, AdminEntrezEntry)
admin.site.register(EntrezTerm, AdminEntrezTerm)
