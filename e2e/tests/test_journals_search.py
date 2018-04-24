from e2e.pages.search.journals import JournalsSearchPage
from e2e.tests.helpers import AcceptanceTest


class TestSearchPage(AcceptanceTest):
    """
    Tests for the Journals search page.
    """

    def test_search_page_existence(self):
        """
        Make sure that search page is accessible.
        """
        JournalsSearchPage(self.browser).visit()
