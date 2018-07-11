"""
Module for video chooser views
"""
from __future__ import absolute_import, unicode_literals

import json

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render

from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailcore.models import Collection

from journals.apps.journals.models import Video
from journals.apps.journals.permissions import video_permission_policy


def get_video_json(video):
    """
    helper function: given a video, return the json to pass back to the
    chooser panel
    """

    return json.dumps({
        'id': video.id,
        'display_name': video.display_name,
        'url': video.view_url,
        'edit_link': reverse(video.get_action_url_name('edit'), args=(video.id,)),
    })


def chooser(request):
    """
    Video chooser view with ability to search
    """
    videos = video_permission_policy.instances_user_has_any_permission_for(
        request.user, ['change', 'delete']
    )

    q = None
    if 'q' in request.GET or 'p' in request.GET or 'collection_id' in request.GET:
        collection_id = request.GET.get('collection_id')
        if collection_id:
            videos = videos.filter(collection=collection_id)

        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']

            videos = videos.search(q)
            is_searching = True
        else:
            videos = videos.order_by('-created_at')
            is_searching = False

        # Pagination
        paginator, videos = paginate(request, videos, per_page=10)  # pylint: disable=unused-variable

        return render(request, "videos/chooser/results.html", {
            'videos': videos,
            'query_string': q,
            'is_searching': is_searching,
        })
    else:
        searchform = SearchForm()

        collections = Collection.objects.all()
        if len(collections) < 2:
            collections = None

        videos = videos.order_by('-created_at')
        paginator, videos = paginate(request, videos, per_page=10)

        return render_modal_workflow(request, 'videos/chooser/chooser.html', 'videos/chooser/chooser.js', {
            'videos': videos,
            'uploadform': None,
            'searchform': searchform,
            'collections': collections,
            'is_searching': False,
        })


def video_chosen(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    return render_modal_workflow(
        request, None, 'videos/chooser/video_chosen.js',
        {'video_json': get_video_json(video)}
    )
