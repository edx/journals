'''Search view class'''
from __future__ import absolute_import, unicode_literals

from django.shortcuts import render
from wagtail.wagtailsearch.backends import get_search_backend
from wagtail.wagtailsearch.models import Query

from journals.apps.journals.models import JournalDocument, JournalImage, JournalPage, Video

MATCH_PHRASE_START_CHAR = '\"'
MATCH_PHRASE_END_CHAR = '\"'


class SearchDisplay:
    '''
    This class encapsulate search results in a form easily
    consumed by display template. Each SearchDisplay contains
    the top level page where the hit was found and a list of
    objects (i.e. Video, Documents) where the hit was found
    '''
    def __init__(self, journal_page):
        self.journal_page = journal_page
        if not hasattr(self.journal_page, 'score'):
            setattr(self.journal_page, 'score', 0)
        self.hit_list = [self.journal_page]
        self.max_score = self.journal_page.score
        self._set_type(self.journal_page)

    def add_hit(self, hit):
        self.hit_list.append(hit)
        if hit.score > self.max_score:
            self.max_score = hit.score
        self._set_type(hit)

    def get_hit_list_sorted(self):
        '''
        get the list of objects sorted by hit score
        '''
        return sorted(self.hit_list, key=lambda hit: hit.score, reverse=True)

    def _set_type(self, hit):
        setattr(hit, 'is_page', isinstance(hit, JournalPage))
        setattr(hit, 'is_doc', isinstance(hit, JournalDocument))
        setattr(hit, 'is_video', isinstance(hit, Video))
        setattr(hit, 'is_image', isinstance(hit, JournalImage))

    def __repr__(self):
        return '<SearchDisplay max_score:%s get_hit_list_sorted:%s>' % (self.max_score, self.get_hit_list_sorted())


def search(request):
    '''
    handler for search requests from the UI
    '''
    search_query = request.GET.get('query', '')

    if search_query:

        if search_query.startswith(MATCH_PHRASE_START_CHAR) and search_query.endswith(MATCH_PHRASE_END_CHAR):
            search_operator = 'and'
        else:
            search_operator = 'or'

        clean_query = search_query.replace(MATCH_PHRASE_START_CHAR, '')

        # TODO - limit number of search results and Pagination
        page_search_results = list(
            JournalPage.objects.live().search(clean_query, operator=search_operator).annotate_score('score')
        )

        # TODO - add pages as related field in SearchFields so we can filter on pages.live
        doc_search_results = list(
            JournalDocument.objects.all().search(clean_query, operator=search_operator).annotate_score('score')
        )
        video_search_results = list(
            get_search_backend().search(
                clean_query, Video.objects.all(), operator=search_operator
            ).annotate_score('score')
        )
        images_search_result = list(
            JournalImage.objects.all().search(clean_query, operator=search_operator).annotate_score('score')
        )

        results = dict()

        for hit in page_search_results + doc_search_results + images_search_result + video_search_results:
            if isinstance(hit, JournalPage):
                results[hit.id] = SearchDisplay(journal_page=hit)
            elif isinstance(hit, (JournalDocument, Video, JournalImage)):
                page_set = hit.journalpage_set.all().distinct()
                for parent_page in page_set:
                    results.setdefault(parent_page.id, SearchDisplay(journal_page=parent_page)).add_hit(hit)

        # Transform dict into sorted list (by score) of SearchDisplay objects
        sorted_results = sorted(results.values(), key=lambda page: page.max_score, reverse=True)

        # Record hit, this is for promotions
        query = Query.get(clean_query)
        query.add_hit()
    else:
        sorted_results = JournalPage.objects.none()

    # Pagination
    # TODO, merge all results into single page
    # page = request.GET.get('page', 1)
    # paginator = Paginator(page_search_results, 20)
    # try:
    #     page_search_results = paginator.page(page)
    # except PageNotAnInteger:
    #     page_search_results = paginator.page(1)
    # except EmptyPage:
    #     page_search_results = paginator.page(paginator.num_pages)

    return render(request, 'search.html', {
        'search_query': search_query,
        'search_results': sorted_results
    })
