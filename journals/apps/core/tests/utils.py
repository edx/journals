""" Helper Methods for Journal Tests and Test Data """
import uuid

from journals.apps.journals.blocks import RAW_HTML_BLOCK_TYPE
from .factories import JournalAboutPageFactory, JournalPageFactory, ImageFactory, DocumentFactory, VideoFactory, \
    RAW_HTML_BLOCK

# Default test data for a journal
TEST_JOURNAL_STRUCTURE = {
            "title": "test_journal_about_page",
            "structure": [
                {
                    "title": "test_page_1",
                    "children": [
                        {
                            "title": "test_page_1_a",
                            "children": [
                                {
                                    "title": "test_page_1_a_i",
                                    "children": []
                                },
                                {
                                    "title": "test_page_1_a_ii",
                                    "children": []
                                }
                            ]
                        },
                        {
                            "title": "test_page_1_b",
                            "children": []
                        }
                    ]
                },
                {
                    "title": "test_page_2",
                    "children": []
                },
                {
                    "title": "test_page_3",
                    "children": [
                        {
                            "title": "test_page_3_a",
                            "children": []
                        },
                        {
                            "title": "test_page_3_b",
                            "children": []
                        }
                    ]
                }
            ]
        }


# Helpers methods to create factories


def child_path_gen(parent_path):
    """
    Generates iterator of paths given the parent path
    Args:
         parent_path (str): Parent path (format ex: "00010002")
    Yields:
        (str): Child paths (format ex: "000100020001", "000100020002", "000100020003")
    """
    child_num = 0
    while True:
        child_num += 1
        if child_num > 9999:
            # Do not allow more then 9999 children per parent
            raise StopIteration

        child_path_suffix = "000" + str(child_num)
        child_path_suffix = child_path_suffix[:4]
        yield parent_path + child_path_suffix


def get_available_child_path(parent_page):
    """
    :param parent_page: for which we want to get upcoming child path
    :return: path that can be use to create new child for parent_page
    """
    if not parent_page.get_children():
        # There is not any child before, so we just can make first child
        return "{root_path}0001".format(root_path=parent_page.path)
    # Have to find last child and add 1 to get path for upcoming child
    child_path = int(parent_page.get_last_child().path[-4:]) + 1
    if child_path <= 9999:
        return "{root_path}{child_path:04}".format(root_path=parent_page.path, child_path=child_path)
    raise Exception("No more child can be added to {}".format(parent_page))


def create_journal_about_page_factory(journal, journal_structure, root_page, about_page_slug=None):
    """
    Creates JournalAboutPageFactory and all of its sub pages that are defined in the journal_structure

    Args:
        journal_structure (dict): defines the structure of the test journal
        about_page_slug (str): desired slug for the journal about page

    Returns:
        (JournalAboutPageFactory): JournalAboutPageFactory that has all the sub pages defined in the
            journal_structure
    """
    title = journal_structure['title']
    children = journal_structure['structure']

    path = get_available_child_path(root_page)
    depth = root_page.depth + 1
    numchild = len(children)
    about_page_factory = JournalAboutPageFactory(
        journal=journal,
        title=title,
        path=path,
        numchild=numchild,
        depth=depth,
        slug=about_page_slug
    )

    # just added JournalAboutPage to root_page as child above, so need to increment numchild for root_page
    root_page.numchild += 1
    root_page.save()

    child_path = child_path_gen(path)
    for child in children:
        create_nested_journal_pages(
            journal_page=child,
            path=next(child_path),
            depth=depth + 1,
            slug=child['title'],
            journal_about_page=about_page_factory
        )

    return about_page_factory


def create_nested_journal_pages(journal_page, path, depth, slug, journal_about_page):
    """
    Creates a JournalPageFactory and all its sub pages that are defined in the journal_page

    Args:
        journal_page (dict): defines attributes of journal page and the structure and attributes of its sub pages
        path (str): page path (format ex: "000300040001")
        depth (int): page depth
        slug (str): page slug

    Returns:
        (JournalPageFactory): JournalPageFactory and it will have also created the JournalPageFactories for its sub
            pages
    """

    title = None
    if 'title' in journal_page:
        title = journal_page['title']

    children = journal_page['children']
    numchild = len(children)
    journal_page = JournalPageFactory(
        title=title,
        path=path,
        numchild=numchild,
        depth=depth,
        slug=slug,
        journal_about_page=journal_about_page,
    )

    journal_page.images.add(ImageFactory())
    journal_page.documents.add(DocumentFactory())
    journal_page.videos.add(VideoFactory(block_id=uuid.uuid4()))

    journal_page.body = [(RAW_HTML_BLOCK_TYPE, RAW_HTML_BLOCK)]
    journal_page.save()

    child_path = child_path_gen(path)
    for child in children:
        create_nested_journal_pages(
            journal_page=child,
            path=next(child_path),
            depth=depth + 1,
            slug=child['title'],
            journal_about_page=journal_about_page,
        )


# Functions to compare test journals


def is_nested_list_equivalent(actual, expected):
    """
    Return True if actual has the same values and nodes as expected,
    actual may have some extra fields in child dicts, but they should have the same number of nodes
    """
    if len(actual) != len(expected):
        return False

    # the lists may not be sorted, so for every item in expected search through actual to find it
    # once the item has been found, mark that is has been found so we don't recursively compare it again
    for expected_item in expected:
        found_equivalent_item = False

        for actual_item in actual:
            if 'found_equivalent' in actual_item:
                continue

            if is_nested_dict_equivalent(actual_item, expected_item):
                found_equivalent_item = True
                actual_item['found_equivalent'] = True
                break

        # if an equivalent item has not been found for expected_item, these lists are not equivalent
        if not found_equivalent_item:
            return False

    # if an equivalent item was found for all items in expected, these lists are equivalent
    return True


def is_nested_dict_equivalent(actual, expected):
    """
    Return True if actual has the same fields and nodes as expected,
    actual may have some extra fields, but they should have the same number of nodes
    """
    # for each key in expected check whether it is equivalent to the same key in actual
    # if each key represent equivalent dicts, these dicts are equivalent
    for key in expected.keys():
        if not is_nested_json_equivalent(actual[key], expected[key]):
            return False
    return True


def is_nested_json_equivalent(actual, expected):
    """
    Return True if actual has the same fields and nodes as expected,
    actual may have some extra fields, but they should have the same number of nodes
   """
    # expected and actual with either be: None, dict, list or some value
    # different comparisions are required for each case
    if not expected:
        # if expected is false or None actual should also be
        return not actual
    elif isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return is_nested_dict_equivalent(actual, expected)
    elif isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        return is_nested_list_equivalent(actual, expected)
    else:
        return actual == expected
