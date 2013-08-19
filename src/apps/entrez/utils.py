# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
from entrez.settings import ENTREZ_SEARCH_MAX


def get_date():
    return date(
        datetime.now().year,
        datetime.now().month,
        datetime.now().day,
    )


def format_date(d=None):
    if d is not None:
        return '%s/%s/%s' % (d.year, d.month, d.day)
    else:
        raise Exception("No valid date!")


def get_maxdate(d=None):
    if d is None:
        return format_date(date.today() - timedelta(days=1))
    else:
        return format_date(d)


def get_mindate(d=None):
    if d is not None:
        return format_date(d)
    else:
        raise Exception("No valid date!")
