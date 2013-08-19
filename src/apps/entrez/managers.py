# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
from django.db import models
from django.db.models.query import QuerySet


def get_current_date():
    return date(datetime.now().year, datetime.now().month, datetime.now().day)


class EntryTermManager(models.Manager):
    """
    Return all terms which need to fetch as queryset.
    """

    @property
    def interval(self):
        return (get_current_date() - timedelta(days=self.model._meta.search_period))

    def get_fetch_terms(self):
        return self.get_query_set().filter(lastedit_date=self.interval, status=1)


class EntrezEntryQuerySet(QuerySet):
    def my_entry_items(self, user):
        return self.filter(feed__user=user)

    def un_read(self):
        return self.filter(read=False)

    def read(self):
        return self.filter(read=True)


class EntrezEntryManager(models.Manager):
    def get_query_set(self):
        return EntrezEntryQuerySet(self.model, using=self._db)

    def my_entry_items(self, user):
        return self.get_query_set().my_entry_items(user)

    def un_read(self):
        return self.get_query_set().un_read()

    def read(self):
        return self.get_query_set().read()
