# -*- coding: utf-8 -*-
#import re
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.mail import send_mail
import entrez
from entrez.settings import *
from entrez.managers import EntrezEntryManager
from entrez.utils import get_maxdate, get_mindate


class EntrezTerm(models.Model):
    STATUS = (
        (1, _("active")),
        (2, _("inactive")),
    )
    name = models.CharField(
        max_length=100,
        help_text=_("Give a unique name to remember"),
    )
    #slug = models.SlugField(unique=True)
    term = models.TextField(
        help_text=_("Keywords to trace as the rules in NCBI."),
    )
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='term_owner')
    period = models.PositiveSmallIntegerField(choices=ENTREZ_SEARCH_PERIOD, default=7)
    db = models.CharField(choices=ENTREZ_DATABASE_CHOICES, max_length=30, default='pubmed')
    creation_date = models.DateField(blank=True, null=False)
    lastedit_date = models.DateField(blank=True, null=False)
    status = models.PositiveSmallIntegerField(
        choices=STATUS,
        default=1,
    )

    class Meta:
        ordering = ['creation_date']

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        #return ('entrez-term-list', (), {'slug': self.slug})
        return ('entrez-term-list', (), {'pk': self.pk})

    @property
    def get_unread_entry_count(self):
        """Get unread entries numbers of a term"""
        # will raise a new database hit
        return EntrezEntry.objects.filter(term=self).un_read().count()

    @property
    def get_db_badge(self):
        return mark_safe("<span class=\"badge\">%s</span>" % self.db)

    def update_entry(self):
        """
        Update term's entry used in celery task

        Using text as return value right now because XML type is too
        heavy to fetch lots of although it's better for saving.
        """
        # define searcher's email
        entrez.email = self.owner.email
        search_options, fetch_options, func, spliter = self.switch()

        handler = entrez.esearch(**search_options)
        result = entrez.read(handler)
        handler.close()

        if result["Count"] == '0':
            return

        handler = entrez.efetch(id=','.join(result['IdList']), **fetch_options)
        entries = handler.read().strip('\n').split(spliter)
        handler.close()
        EntrezEntry.objects.bulk_create([func(entry) for entry in entries])

        if not settings.DEBUG and settings.EMAIL_HOST is not None:
            send_mail('Your Search for %s is finished' % self.term,
                      mark_safe(_('''There are %d numbers of entries founded. visit
                                  <a href="#">here</a> to see the result''' % len(entries))),
                      settings.EMAIL_HOST_USER, [self.owner.email], fail_silently=False)

    def switch(self):
        """
        Switching options by database type based on settings. See
        `settings.ENTREZ_DATABASE_CHOICES` also.
        """
        # todo: using lambda is better ?
        if self.db in settings.ENTREZ_OPTION_TYPE['s1']:
            # pubmed options
            search_options = self.search_options(datetype='edat')
            fetch_options = self.fetch_options(rettype='abstract')
            spliter = '\n\n\n'
            func = self.pubmed
        elif self.db == 'gene':
            search_options = self.search_options(rettype=False)
            fetch_options = self.fetch_options()
            spliter = '\n\n'
            func = self.gene
        elif self.db == 'epigenomics':
            search_options = self.search_options()
            fetch_options = self.fetch_options()
            spliter = '\n'
            func = self.epigenomics
        elif self.db == 'nuccore':
            search_options = self.search_options()
            fetch_options = self.fetch_options(rettype='acc')
            spliter = '\n'
            func = self.nuccore
        else:
            search_options = self.search_options()
            fetch_options = self.fetch_options()
            spliter = '\n'
            func = self.pubmed

        return search_options, fetch_options, func, spliter

    def search_options(self, **kwargs):
        """Return entrez.esearch's options"""
        options = {
            'db': self.db,
            'term': self.term,
            'retmax': ENTREZ_SEARCH_MAX,
            'datetype': 'pdat',
            'mindate': get_mindate(self.lastedit_date),
            'maxdate': get_maxdate(),
            'usehistory': 'y',
        }

        if kwargs:
            options.update(kwargs)

        return options

    def fetch_options(self, **kwargs):
        """Return entrez.efetch's options"""
        options = {
            'db': self.db,
            'retmode': 'text',
        }

        if kwargs:
            options.update(kwargs)

        return options

    # Should I use XML to save into fields? so buggy for these
    # fetch func. Need to dig the document more.

    def pubmed(self, entry):
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
            print "Can't find PMID in the string: %s" % e[-1]

        eid = e[-1][start:end]

        html = ''
        es = entry.split('\n\n')
        for e in es:
            html += '<p>' + e + '</p>'

        return EntrezEntry(content=entry, content_html=html, eid=eid, abstract=abstract,
                           term=self, db=self.db, owner=self.owner, title=title,
                           authors=authors, magzine=magzine)

    def epigenomics(self, entry):
        """Create epigenomics type entry"""
        entry = entry[entry.find(' ')+1:]

        return EntrezEntry(content=entry, content_html=entry, eid=entry, term=self,
                           db=self.db, owner=self.owner, title=entry)

    def gene(self, entry):
        """Create gene type entry"""
        entry = entry[entry.find(' ')+1:]
        e = entry.split('\n')
        eid = e[-1][e[-1].find(' ')+1:]
        title = e[0]

        return EntrezEntry(content=entry, eid=eid, term=self, content_html=entry,
                           db=self.db, owner=self.owner, title=title)

    def nuccore(self, entry):
        """Create nuccore type entry"""

        return EntrezEntry(content=entry, content_html=entry, term=self, eid=entry,
                           title=entry, owner=self.owner, db=self.db)


class EntrezEntry(models.Model):
    """
    Entrez's entry stored in django database
    """
    eid = models.CharField(max_length=20, blank=False, null=False)
    db = models.CharField(choices=ENTREZ_DATABASE_CHOICES, max_length=30, blank=False, null=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='entry_owner')
    term = models.ForeignKey(EntrezTerm, related_name='entry_term')
    content = models.TextField()
    content_html = models.TextField()
    title = models.CharField(max_length=512, blank=False, null=False)
    magzine = models.CharField(blank=True, max_length=512, help_text=_('If entry is a pubmed item'))
    authors = models.CharField(blank=True, max_length=512, help_text=_('If entry has authors'))
    abstract = models.TextField(blank=True, help_text=_('If entry is a pubmed item'))
    read = models.BooleanField(default=False)
    creation_time = models.DateTimeField(auto_now_add=True)
    lastedit_time = models.DateTimeField(auto_now=True)

    objects = EntrezEntryManager()

    class Meta:
        ordering = ['creation_time']
        #ordering = []

    def __unicode__(self):
        return self.title

    @property
    def get_db_badge(self):
        return mark_safe("<span class=\"badge\">%s</span>" % self.db)

    @property
    def real_url(self):
        return mark_safe("http://www.ncbi.nlm.nih.gov/%s/%s/" % (self.db, self.eid))

    #def save(self):
    #    self.content_html = self.content.replace('\n', '<br>')
    #    super(EntrezEntry, self).save()
