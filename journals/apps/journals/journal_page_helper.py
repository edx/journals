""" Helpers for Journal Page Types """


class JournalPageMixin(object):
    """ This class contains methods that are shared between Journal Page Types """

    def get_nested_children(self):
        """ Return dict hierarchy with self as root """

        # TODO: can remove "url" field once we move to seperated front end
        structure = {
            "title": self.title,
            "children": None,
            "id": self.id,
            "url": self.url
        }
        children = self.get_children()
        if not children:
            return structure

        structure["children"] = [child.specific.get_nested_children() for child in children]
        return structure
