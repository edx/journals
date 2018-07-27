"""
Objects that model SearchResults and used by Serializer.
These are not database models.
"""
from journals.apps.journals.models import JournalPage, JournalDocument, JournalImage, Video
from journals.apps.journals.blocks import PDF_BLOCK_TYPE, VIDEO_BLOCK_TYPE, IMAGE_BLOCK_TYPE, RICH_TEXT_BLOCK_TYPE
from journals.apps.journals.templatetags.wagtail_tags import get_block_fragment_identifier


class SearchResults(object):
    """
    This class encapsulates SearchResults
    """
    def __init__(self, search_meta_data, hit_list):
        """
        Args:
            search_meta_data: SearchMetaData object
            hit_list: list of SearchHit objects
        """
        self.meta = search_meta_data
        self.hits = hit_list


class SearchHit(object):
    """
    This class encapsulates a SearchHit object
    """
    def __init__(self, search_meta_data, hit_list):
        """
        Args:
            search_meta_data: SearchMetaData object
            hit_list: list of SearchHit objects
        """
        self.meta = search_meta_data
        self.hits = hit_list


class SearchHit(object):
    """
    This class encapsulates a SearchHit object
    """
    def __init__(self, journal_page, component=None):
        """
        Args:
            journal_page: JournalPage that contains the search hit, if None it will be calculated
            component: Specific object type that contains the hit (JournalImage, JournalDocument, Video)
            If none then hit is text found in the base JournalPage itself
        """

        self._set_page_info(journal_page)

        # Setup block information
        if component:
            self._set_type_info(component)
        else:
            self._set_type_info(journal_page)

    def _set_page_info(self, journal_page):
        """
        Set information about Page that hit was found on
        """
        about_page = journal_page.get_journal_about_page()
        self.journal_about_page_id = about_page.id
        self.journal_id = about_page.journal.id
        self.journal_name = about_page.title
        self.page_id = journal_page.id
        self.page_title = journal_page.title
        self.page_path = journal_page.url_path  # TODO change this to list of parent page names WL-1720
<<<<<<< 92e54e0277907a4bc992520698e914afe6daaf5b
=======
        self.page_list_other = []
        # Setup enclosing Journal
        about_page = journal_page.get_journal_about_page()
        self.journal_about_page_id = about_page.id
        self.journal_id = about_page.journal.id
        self.journal_name = about_page.title
>>>>>>> add function to search subtypes, more clear access check, other review comments

    def _set_type_info(self, component):
        """
        Set members related to block specific info
        """
        self.block_id = component.id

        self.highlights = component.search_results_metadata.get('highlights', [])
        self.score = getattr(component, 'score', 0)
        self.span_id = ''

        if isinstance(component, JournalPage):
            self.block_type = RICH_TEXT_BLOCK_TYPE
            self.block_title = component.title
        elif isinstance(component, JournalImage):
            self.block_type = IMAGE_BLOCK_TYPE
            self.block_title = component.title
        elif isinstance(component, JournalDocument):
            self.block_type = PDF_BLOCK_TYPE
            self.block_title = component.title
        elif isinstance(component, Video):
            self.block_type = VIDEO_BLOCK_TYPE
            self.block_title = component.display_name

        if not self.block_type == RICH_TEXT_BLOCK_TYPE:
            self.span_id = get_block_fragment_identifier(self.block_id, self.block_type)

    def __lt__(self, other):
        """
        comparator needed for sorting via bisect function
        """
        return self.score < other


class SearchMetaData(object):
    """
    Object to encapsulate meta-data about the search
    """
    def __init__(self):
        self.total_count = 0
        self.text_count = 0
        self.image_count = 0
        self.video_count = 0
        self.doc_count = 0
