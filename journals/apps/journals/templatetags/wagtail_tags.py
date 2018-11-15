"""
This module has those template tags/filters which we use in Wagtail template overrides.
"""
from django import template
from wagtail.wagtailadmin.templatetags.wagtailadmin_tags import assignment_tag

from journals.apps.journals.journal_page_helper import UserJournalPagePermissionsProxy
from journals.apps.journals.models import WagtailModelManager
from journals.apps.journals.utils import get_span_id


register = template.Library()


@register.simple_tag(takes_context=True)
def collections_user_has_access(context, collections, request):
    """
    Args:
        context: template context
        collections: queryset of collection objects
        request: http request object

    Returns: queryset of collection objects striping those where user does not have add or change permissions

    """
    collection_type = 'documents'
    if 'videos' in context:
        collection_type = 'videos'
    elif 'images' in context:
        collection_type = 'images'
    return WagtailModelManager.get_user_collections(request.user, collection_type, collections)


@register.simple_tag(takes_context=True)
def get_buttons_for_obj(context, obj):
    """
    Args:
        context: template context
        obj: model instance

    Returns: list of wagtail admin buttons for given object

    """
    view = context['view']
    return view.button_helper.get_buttons_for_obj(
            obj, classnames_add=['button-small', 'button-secondary']
    )


@register.filter(name='fragment_identifier')
def get_block_fragment_identifier(block_id, block_type):
    """
    Args:
        block_id: Id of searched object for example Id of JournalDocument or Video or Image object
        block_type: e:g "image", "doc" or "xblock_video" etc

    Returns: block fragment identifier e.g "image-c81e728d9d4c2f636f067f89cc14862c"
    """
    return get_span_id(block_type, block_id)


@assignment_tag(takes_context=True)
def page_permissions(context, page):
    """
    Overridden this tag to use UserJournalPagePermissionsProxy class

    Usage: {% page_permissions page as page_perms %}
    Sets the variable 'page_perms' to a PagePermissionTester object that can be queried to find out
    what actions the current logged-in user can perform on the given page.
    """
    # Create a UserPagePermissionsProxy object to represent the user's global permissions, and
    # cache it in the context for the duration of the page request, if one does not exist already
    if 'user_page_permissions' not in context:
        context['user_page_permissions'] = UserJournalPagePermissionsProxy(context['request'].user)

    # Now retrieve a PagePermissionTester from it, specific to the given page
    return context['user_page_permissions'].for_page(page)
