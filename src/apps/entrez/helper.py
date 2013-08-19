# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.mail import send_mail
import entrez
from entrez.models import EntrezEntry
from entrez.settings import ENTREZ_OPTION_TYPE, ENTREZ_SEARCH_MAX
from entrez.utils import get_mindate, get_maxdate


def get_options(term):
    """
    Return options to entrez utils.
    """
    if term is None:
        raise

    options = {
        'search': {
            'db': term.db,
            'term': term.term,
            'retmax': ENTREZ_SEARCH_MAX,
            'datetype': 'pdat',
            'mindate': get_mindate(term.lastedit_date),
            'maxdate': get_maxdate(),
            'usehistory': 'y',
            'retmode': 'text',
        },
        'fetch': {
            'db': term.db,
            'retmode': 'text',
        },
        'splitter': '\n',
        'function': 'default',
    }

    if term.db in ENTREZ_OPTION_TYPE["s1"]:
        # database pubmed
        options["search"].update({'datetype': 'edat'})
        options["fetch"].update({'rettype': 'abstract'})
        options.update({'splitter': '\n\n\n', 'function': pubmed})
        return options
    elif term.db in ENTREZ_OPTION_TYPE["s2"]:
        # database nuccore
        options["fetch"].update({'rettype': 'acc'})
        options.update({'function': nuccore})
        return options
    elif term.db in ENTREZ_OPTION_TYPE["s3"]:
        # database gene
        options.update({'splitter': '\n\n', 'function': gene})
        return options
    else:
        return options


def pubmed(term, entry):
    """Create pubmed type entry"""
    # The output of pubmed text record is varible, so some of
    # articles info will not be correct.
    entry = entry[entry.find(' ')+1:]
    e = entry.split('\n\n')
    lines = len(e)
    if lines < 5:
        abstract = ''
    elif lines == 7 or e[-2].startswith('Copyright', 0, 15) or e[-2].startswith('copyright', 0, 15):
            abstract = e[-3].replace('\n', ' ')
    else:
        abstract = e[-2].replace('\n', ' ')

    authors = e[2].replace('\n', ' ')
    title = e[1].replace('\n', ' ')
    magzine = e[0].replace('\n', ' ').replace(' [Epub ahead of print]', '')

    try:
        start = e[-1].index('PMID: ')+6
        end = e[-1].index('  [PubMed')
    except ValueError:
        raise Exception("Can't find PMID in the string: %s" % e[-1])

    eid = e[-1][start:end]
    html = ''
    es = entry.split('\n\n')
    for e in es:
        html += '<p>' + e + '</p>'

    return EntrezEntry(content=entry, content_html=html, eid=eid, abstract=abstract,
                       term=term, db=term.db, owner=term.owner, title=title,
                       authors=authors, magzine=magzine)


def epigenomics(term, entry):
    """Create epigenomics type entry"""
    entry = entry[entry.find(' ')+1:]

    return EntrezEntry(content=entry, content_html=entry, eid=entry, term=term,
                       db=term.db, owner=term.owner, title=entry)


def gene(term, entry):
    """Create gene type entry"""
    entry = entry[entry.find(' ')+1:]
    e = entry.split('\n')
    eid = e[-1][e[-1].find(' ')+1:]
    title = e[0]

    return EntrezEntry(content=entry, eid=eid, term=term, content_html=entry,
                       db=term.db, owner=term.owner, title=title)


def nuccore(term, entry):
    """Create nuccore type entry"""

    return EntrezEntry(content=entry, content_html=entry, term=term, eid=entry,
                       title=entry, owner=term.owner, db=term.db)


def trace(term):
    """
    Trace user's term in NCBI.
    """
    # start to search
    entrez.email = term.owner.email
    options = get_options(term)

    handler = entrez.esearch(**options["search"])
    r = entrez.read(handler)
    handler.close()

    # if no search result or get errors
    if r["Count"] == '0':
        return

    # start to fetch
    handler = entrez.efetch(id=','.join(r['IdList']), **options["fetch"])
    entries = handler.read().strip('\n').split(options["splitter"])
    handler.close()
    EntrezEntry.objects.bulk_create([options["function"](term, entry) for entry in entries])

    if not settings.DEBUG and settings.EMAIL_HOST is not None:
        send_mail(_('Your Search for %s is finished') % term.term,
                  mark_safe(_('''There are %d numbers of entries
                  founded. visit <a href="#">here</a> to see the
                  esult''' % len(entries))), settings.EMAIL_HOST_USER,
                  [term.owner.email], fail_silently=False)
