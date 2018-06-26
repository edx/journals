from wagtail.wagtailcore import hooks
from wagtail.wagtaildocs.permissions import permission_policy as document_permission_policy
from wagtail.wagtailimages.permissions import permission_policy as image_permission_policy


@hooks.register('construct_document_chooser_queryset')
def documents_with_add_or_change_permissions_only(documents, request):  # pylint: disable=unused-argument
    """
    Show documents from those collections where user has add or change permissions
    """

    return document_permission_policy.instances_user_has_any_permission_for(
        request.user, ['add', 'change']
    )


@hooks.register('construct_image_chooser_queryset')
def images_with_add_or_change_permissions_only(images, request):  # pylint: disable=unused-argument
    """
    Show images from those collections where user has add or change permissions
    """

    return image_permission_policy.instances_user_has_any_permission_for(
        request.user, ['add', 'change']
    )
