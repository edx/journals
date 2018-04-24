from bok_choy.page_object import PageObject

from e2e.pages import BASE_URL


class JournalsSearchPage(PageObject):
    """
    Journals search page
    """

    url = "{base}/search".format(base=BASE_URL)

    def is_browser_on_page(self):
        return self.q(css='#search_results').present
