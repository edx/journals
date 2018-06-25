"""
Search backend module
"""
from __future__ import absolute_import, unicode_literals

from django.conf import settings

from elasticsearch.helpers import bulk
from wagtail.search.backends.elasticsearch5 import (
    Elasticsearch5Index, Elasticsearch5Mapping, Elasticsearch5SearchBackend,
    Elasticsearch5SearchQueryCompiler, Elasticsearch5SearchResults)
from wagtail.search.index import class_is_indexed

JOURNAL_DOCUMENT_INDEX_NAME = '{}__journals_journaldocument'.format(settings.WAGTAILSEARCH_BACKENDS['default']['INDEX'])
JOURNAL_DOCUMENT_TYPE = 'wagtaildocs_abstractdocument_journals_journaldocument'
JOURNAL_DOCUMENT_ATTACHMENT_CONTENT_FIELD = 'attachment.content'
INGEST_ATTACHMENT_INDEX = '_ingest'
INGEST_ATTACHMENT_DOC_TYPE = 'pipeline'
INGEST_ATTACHMENT_ID = 'attachment'
INGEST_ATTACHMENT_DATA_FIELD = 'data'
VIDEO_DOCUMENT_TYPE = 'journals_video'
VIDEO_DOCUMENT_TRANSCRIPT_FIELD = 'transcript'

LARGE_TEXT_FIELD_SEARCH_PROPS = {
    'type': 'text',
    'analyzer': 'edgengram_analyzer',
    'search_analyzer': 'standard',
    'store': True,  # store separately from other fields
    'include_in_all': False,
    'term_vector': 'with_positions_offsets',  # this enables FVH for faster highlighting
}


class JournalsearchMapping(Elasticsearch5Mapping):

    def get_mapping(self):
        '''
        Override the index mappings for JOURNAL_DOCUMENT_TYPE
        To add specific settings for attachments
        '''
        mapping = super(JournalsearchMapping, self).get_mapping()

        if self.get_document_type() == JOURNAL_DOCUMENT_TYPE:
            # As the attachment content can be very large, these settings are important
            # to ensure fast searching and highlighting
            # inspired by https://blog.ambar.cloud/making-elasticsearch-perform-well-with-large-text-fields/
            # and https://blog.ambar.cloud/highlighting-large-documents-in-elasticsearch/
            source_properties = {
                '_source': {
                    'excludes': [INGEST_ATTACHMENT_DATA_FIELD, JOURNAL_DOCUMENT_ATTACHMENT_CONTENT_FIELD]
                }
            }
            attachment_properties = {
                'attachment.content': LARGE_TEXT_FIELD_SEARCH_PROPS
            }
            mapping[self.get_document_type()].update(source_properties)
            mapping[self.get_document_type()]['properties'].update(attachment_properties)

        elif self.get_document_type() == VIDEO_DOCUMENT_TYPE:
            source_properties = {
                '_source': {
                    'excludes': [VIDEO_DOCUMENT_TRANSCRIPT_FIELD]
                }
            }
            mapping[self.get_document_type()].update(source_properties)

        return mapping


class JournalsearchIndex(Elasticsearch5Index):
    '''Journal specific backend to Elasticsearch5'''
    def put(self):
        '''
        Called during index creation
        Override to setup the ingest_attachment plugin
        '''
        super(JournalsearchIndex, self).put()

        # TODO is this the right place? Only do it once if it doesn't exist
        if self.name == JOURNAL_DOCUMENT_INDEX_NAME:
            body = {'description': 'Extract attachment information',
                    'processors': [
                        {INGEST_ATTACHMENT_ID: {'field': INGEST_ATTACHMENT_DATA_FIELD}}
                    ]
                    }

            results = self.es.index(
                index=INGEST_ATTACHMENT_INDEX,
                doc_type=INGEST_ATTACHMENT_DOC_TYPE,
                id=INGEST_ATTACHMENT_ID,
                body=body
            )

            print('created index for _ingest attachment, results=', results)

    def add_item(self, item):
        '''
        Called when new item added to the index
        Need to override to include pipeline attribute for ingest_plugin attachment
        '''

        # Make sure the object can be indexed
        if not class_is_indexed(item.__class__):
            return

        # Get mapping
        mapping = self.mapping_class(item.__class__)
        if mapping.get_document_type() == JOURNAL_DOCUMENT_TYPE:
            results = self.es.index(
                self.name,
                mapping.get_document_type(),
                mapping.get_document(item),
                pipeline=INGEST_ATTACHMENT_ID,
                id=mapping.get_document_id(item)
            )
            print('in add_item with attachment results=', results)
        else:
            super(JournalsearchIndex, self).add_item(item)

    def add_items(self, model, items):
        '''
        Called by update_index management command
        Need to override so that ingest_plugin attachment items get recreated correctly
        '''
        if not class_is_indexed(model):
            return

        # Get mapping
        mapping = self.mapping_class(model)
        doc_type = mapping.get_document_type()

        if mapping.get_document_type() == JOURNAL_DOCUMENT_TYPE:
            # Create list of actions
            actions = []
            for item in items:
                # Create the action
                action = {
                    '_index': self.name,
                    '_type': doc_type,
                    '_id': mapping.get_document_id(item),
                    'pipeline': INGEST_ATTACHMENT_ID,
                }
                action.update(mapping.get_document(item))
                actions.append(action)

            print('in add_items with attachment')
            # Run the actions
            bulk(self.es, actions)
        else:
            super(JournalsearchIndex, self).add_items(model, items)


class JournalsearchSearchQuery(Elasticsearch5SearchQueryCompiler):
    '''Journal specific backend for SearchQuery'''
    def __init__(self, *args, **kwargs):

        super(JournalsearchSearchQuery, self).__init__(*args, **kwargs)
        if self.mapping.get_document_type() == JOURNAL_DOCUMENT_TYPE:
            # add attachment.content to search fields so we can highlight
            if self.fields:
                self.fields.append(JOURNAL_DOCUMENT_ATTACHMENT_CONTENT_FIELD)
            else:
                self.fields = ['_all', '_partials', JOURNAL_DOCUMENT_ATTACHMENT_CONTENT_FIELD]
        elif self.mapping.get_document_type() == VIDEO_DOCUMENT_TYPE:
            # add transcript to search fields so we can highlight
            if self.fields:
                self.fields.append(VIDEO_DOCUMENT_TRANSCRIPT_FIELD)
            else:
                self.fields = ['_all', '_partials', VIDEO_DOCUMENT_TRANSCRIPT_FIELD]

    def get_inner_query(self):
        '''
        Override to change the behavior of 'and' operator to make it function
        like 'match_phrase' operator instead so we can do exact phrase search
        '''
        if self.operator == 'or' or self.query_string is None:
            return super(JournalsearchSearchQuery, self).get_inner_query()
        else:
            # override to use match_phrase symantics instead of and operator
            fields = self.fields or ['_all', '_partials']

            if len(fields) == 1:
                query = {
                    'match_phrase': {
                        fields[0]: {
                            'query': self.query_string,
                        }
                    }
                }
            else:
                query = {
                    'multi_match': {
                        'query': self.query_string,
                        'fields': fields,
                        'type': 'phrase'
                    }
                }

            return query


class JournalsearchSearchResults(Elasticsearch5SearchResults):
    fields_param_name = 'stored_fields'

    def _do_search(self):
        # Params for elasticsearch query
        params = dict(
            index=self.backend.get_index_for_model(self.query.queryset.model).name,
            body=self._get_es_body(),
            _source=False,
            from_=self.start,
        )

        # Add highlights
        # TODO iterate over the fields in the query to generate this field list dynamically
        params['body']['highlight'] = {
            'fields': {
                '_all': {},
                '_partials': {},
                JOURNAL_DOCUMENT_ATTACHMENT_CONTENT_FIELD: {},
                VIDEO_DOCUMENT_TRANSCRIPT_FIELD: {},
            },
            'pre_tags': ['<b>'],
            'post_tags': ['</b>']
        }
        params[self.fields_param_name] = 'pk'

        # Add size if set
        if self.stop is not None:
            params['size'] = self.stop - self.start

        # Send to Elasticsearch
        hits = self.backend.es.search(**params)

        # Get pks from results
        pks = [hit['fields']['pk'][0] for hit in hits['hits']['hits']]
        meta_info = {
            str(hit['fields']['pk'][0]): [hit['_score'], hit.get('highlight', None)] for hit in hits['hits']['hits']
        }

        # Initialise results dictionary
        results = dict((str(pk), None) for pk in pks)

        # Find objects in database and add them to dict
        queryset = self.query.queryset.filter(pk__in=pks)
        for obj in queryset:
            results[str(obj.pk)] = obj

            if self._score_field:
                score = meta_info.get(str(obj.pk))[0]
                setattr(obj, self._score_field, score)

            # see if we have a highlight
            highlights = meta_info.get(str(obj.pk))[1]
            if highlights:
                # let's flaten into a list of highlighs
                values = highlights.values()
                highlight_list = [item for sublist in values for item in sublist]
                setattr(obj, 'search_results_metadata', {'highlights': highlight_list})

        # Return results in order given by Elasticsearch
        return [results[str(pk)] for pk in pks if results[str(pk)]]


class JournalsearchSearchBackend(Elasticsearch5SearchBackend):
    mapping_class = JournalsearchMapping
    index_class = JournalsearchIndex
    query_class = JournalsearchSearchQuery
    results_class = JournalsearchSearchResults


SearchBackend = JournalsearchSearchBackend
