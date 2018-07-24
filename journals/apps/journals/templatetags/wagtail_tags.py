"""
This module has those template tags/filters which we use in Wagtail template overrides.
"""
from django import template

from journals.apps.journals.blocks import BLOCK_SPAN_ID_FORMATTER
from journals.apps.journals.models import WagtailModelManager
from journals.apps.journals.utils import make_md5_hash


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
    return BLOCK_SPAN_ID_FORMATTER.format(block_type=block_type, block_id=make_md5_hash(block_id))
