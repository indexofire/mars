# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


ENTREZ_DEFAULT_CHOICES = (
    ("pubmed", "Pubmed"),
    ("epigenomics", "Epigenomics"),
    #("pmc", "Pubmed Central"),
    #("protein", "Protein"),
    ("nuccore", "Nucleotide"),
    #("nucgss", ),
    #("nucest", ),
    #("structure", ),
    #("genome", "Genome Database"),
    #("books", ),
    #("cancerchromosomes", ),
    #("cdd", ),
    #("gap", ),
    #("domains", ),
    ("gene", "Gene"),
    #("genomeprj", ),
    #("gensat", ),
    #("geo", ),
    #("gds", ),
    #("homologene", ),
    #("journals", ),
    #("mesh", "MeSH"),
    #("ncbisearch", ),
    #("nlmcatalog", ),
    #("omia", ),
    #("omim", ),
    #("popset", ),
    #("probe", ),
    #("proteinclusters", ),
    #("pcassay", ),
    #("pccompound", ),
    #("pcsubstance", ),
    ("snp", "SNP"),
    #("taxonomy", ),
    #("toolkit", ),
    #("unigene", ),
    #("unists", ),
)
ENTREZ_DATABASE_CHOICES = getattr(settings, 'ENTREZ_DATABASE_CHOICES', ENTREZ_DEFAULT_CHOICES)

ENTREZ_OPTION_TYPE = {
    's1': ["pubmed", ],
    's2': ["nuccore", ],
    's3': ["gene", ],
    's4': ["epigenomics", "snp"],
}

ENTREZ_DEFAULT_PERIOD = (
    (1, _('Everyday')),
    (7, _('Every Week')),
    (14, _('Every Two Weeks')),
)
ENTREZ_SEARCH_PERIOD = getattr(settings, 'ENTREZ_SEARCH_PERIOD', ENTREZ_DEFAULT_PERIOD)

ENTREZ_SEARCH_MAX = 1000
