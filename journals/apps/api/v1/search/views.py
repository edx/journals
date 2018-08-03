""" API for searching content of Journals
    Usage:
        /api/v1/search/<journal_id>/?query=<query_string>&operator=<operator>&type=<type>
    Args:
        <journal_id>: The id for Journal object to search in. If omitted will search
        all of the published Journals the requested user has access to on the given Site
        <query_string>: The text to search, should be url encoded
        <operator>: 'or' - to match any terms in the query_string (default)
                    'and' - exact match for all the terms in the query_string
        <type>: 'all' - search across all content types (default)
                'images' - search for images only
                'documents' - search in documents only
                'videos' - search in videos only
    Returns:
        List of SearchResuls objects (see SearchResultsSerializer) sorted by hit score
"""
import bisect
import logging

from rest_framework.response import Response
from rest_framework.views import APIView

from wagtail.wagtailsearch.models import Query

from journals.apps.journals.models import (
    JournalAboutPage,
    JournalAccess,
    JournalDocument,
    JournalImage,
    JournalPage,
    Video
)
from journals.apps.api.serializers import SearchResultsSerializer
from journals.apps.api.v1.search.models import SearchResults, SearchHit, SearchMetaData

logger = logging.getLogger(__name__)

PARAM_QUERY = 'query'
PARAM_OPERATOR = 'operator'
PARAM_TYPE = 'type'
TYPE_IMAGE = 'images'
TYPE_DOCUMENT = 'documents'
TYPE_VIDEO = 'videos'
TYPE_ALL = 'all'
OPERATOR_OR = 'or'
OPERATOR_AND = 'and'


class SearchView(APIView):
    """
    View to return Journal SearchResults via RestAPI
    """
    # TODO: add pagination WL-1719

    def get(self, request, journal_id=None):
        """
        Get search results for specified journal or all journals
        for current site
        """
        search_results = self._search(request, journal_id)
        serializer = SearchResultsSerializer(search_results)
        return Response(serializer.data)

    def _search(self, request, journal_id=None):
        '''
        handler for search requests
        '''
        search_query = request.GET.get(PARAM_QUERY, None)
        search_operator = request.GET.get(PARAM_OPERATOR, OPERATOR_OR)
        search_filter = request.GET.get(PARAM_TYPE, TYPE_ALL)
        hit_list = []
        search_meta = SearchMetaData()

        # Get Journals user has access to
        about_pages = self._get_journals_for_user(request, journal_id)

        if not about_pages:
            return SearchResults(search_meta, hit_list)

        if search_query:

            clean_query = search_query  # TODO: do we need to do any cleansing of querystring?

            for about_page in about_pages:

                #  Only include pages beneath our root page that are live and public
                base_page_query = JournalPage.objects.live().public().descendant_of(about_page)

                if search_filter == TYPE_ALL:
                    # Search pages which will yield hits for text/HTML/RawHTML
                    page_search_results = base_page_query.search(
                        clean_query,
                        operator=search_operator
                    ).annotate_score(
                        'score'
                    )

                    self._add_to_hit_list(hit_list, page_search_results, journal_page_ids=None, base_page=True)
                    search_meta.text_count += page_search_results.count()

                if search_filter == TYPE_ALL or search_filter == TYPE_DOCUMENT:
                    journal_page_ids, doc_search_results = self._filetype_search(
                        base_page_query,
                        clean_query,
                        search_operator,
                        JournalDocument
                    )

                    self._add_to_hit_list(hit_list, doc_search_results, journal_page_ids, base_page=False)
                    search_meta.doc_count += doc_search_results.count()

                if search_filter == TYPE_ALL or search_filter == TYPE_IMAGE:
                    # Get the Images that are used in JournalPages beneath journal_root_page
                    journal_page_ids, image_search_results = self._filetype_search(
                        base_page_query,
                        clean_query,
                        search_operator,
                        JournalImage
                    )
                    self._add_to_hit_list(hit_list, image_search_results, journal_page_ids, base_page=False)
                    search_meta.image_count += image_search_results.count()

                if search_filter == TYPE_ALL or search_filter == TYPE_VIDEO:
                    # Get the list of Video id's that are used in JournalPages beneath journal_root_page
                    journal_page_ids, video_search_results = self._filetype_search(
                        base_page_query,
                        clean_query,
                        search_operator,
                        Video
                    )
                    self._add_to_hit_list(hit_list, video_search_results, journal_page_ids, base_page=False)
                    search_meta.video_count += video_search_results.count()

                query = Query.get(clean_query)
                query.add_hit()

            search_meta.total_count = len(hit_list)

        # return the list iterator in descending order with highest hit score first
        return SearchResults(search_meta, reversed(hit_list))

    def _filetype_search(self, base_page_query, query_string, search_operator, type_class):
        """
        Search
        """
        if type_class == JournalDocument:
            column = 'documents'
        elif type_class == JournalImage:
            column = 'images'
        elif type_class == Video:
            column = 'videos'
        else:
            return None

        id_clause = column + '__id'
        field = id_clause + '__isnull'

        # Get the list of <type_class> id's that are used in JournalPages beneath journal_root_page
        # i.e.
        # id_list = base_page_query.only('documents').filter(documents__id__isnull=False).distinct().
        # values_list('documents__id', 'id')

        id_list = base_page_query.only(
            '{column}'.format(column=column)
        ).filter(
            **{field: False}
        ).distinct().values_list(
            '{id_clause}'.format(id_clause=id_clause), 'id'
        )

        # list of component id's
        component_id_list = [item[0] for item in id_list]

        # Now search only objects with id's in the list
        results = type_class.objects.filter(
            id__in=component_id_list
        ).search(
            query_string,
            operator=search_operator
        ).annotate_score(
            'score'
        )

        journal_page_id_list = []

        if results.count():
            # list of journal page ids
            journal_page_id_list = [item[1] for item in id_list]

        return journal_page_id_list, results

    def _add_to_hit_list(self, results, search_results, journal_page_ids, base_page=True):
        """
        Add search_results to result list in sorted order by 'score'
        Args:
            results: list of SearchResults objects sorted by score (ascending)
            search_results: QuerySet representing the search results
            journal_page_ids: list of page id's that contain component hits
            base_page: True if search_results are for journal_page
        """
        for result in search_results:
            score = getattr(result, 'score', 0)
            position = bisect.bisect_left(results, score)
            if base_page:
                results.insert(position, SearchHit(journal_page=result, component=None))
            else:
                # find the specific JournalPages (from filtered list) where the Component
                # was found
                journal_page_list = result.journalpage_set.filter(
                    id__in=journal_page_ids
                ).only(
                    'id', 'title', 'url_path'
                ).live().distinct()

                for page in journal_page_list:
                    results.insert(position, SearchHit(journal_page=page, component=result))

    def _get_journals_for_user(self, request, journal_id=None):
        """
        Get the JournalAboutPages the user has access to view
        Args:
            request: Request object
            journal_id: specific journal_id to fetch
        Returns:
            List of JournalAboutPage objects user has access to view
        """
        about_pages = []

        journal_id_list = JournalAccess.get_user_accessible_journal_ids(request.user)

        if journal_id:
            if int(journal_id) in journal_id_list:
                about_pages.append(JournalAboutPage.objects.get(journal_id=journal_id))
        else:
            # get all live journals for the requested site that user has access to
            about_pages = request.site.root_page.get_children().live().specific().filter(
                journalaboutpage__journal__id__in=journal_id_list
            )

        return about_pages
