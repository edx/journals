from bok_choy.web_app_test import WebAppTest


class AcceptanceTest(WebAppTest):
    """
    The base class of all acceptance tests.
    """

    def __init__(self, *args, **kwargs):
        super(AcceptanceTest, self).__init__(*args, **kwargs)
