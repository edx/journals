"""
Views for journals app
"""
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from wagtail.contrib.modeladmin.views import WMABaseView
from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailcore.models import Collection

from journals.apps.journals.permissions import video_permission_policy


class VideoIndexView(WMABaseView):

    def get(self, request, *args, **kwargs):

        videos = video_permission_policy.instances_user_has_any_permission_for(
            request.user, ['change', 'delete']
        )

        # Ordering
        if 'ordering' in request.GET and request.GET['ordering'] in [
            'source_course_run', 'display_name', '-created_at'
        ]:
            ordering = request.GET['ordering']
        else:
            ordering = '-created_at'
        videos = videos.order_by(ordering)

        # Filter by collection
        current_collection = None
        collection_id = request.GET.get('collection_id')
        if collection_id:
            try:
                current_collection = Collection.objects.get(id=collection_id)
                videos = videos.filter(collection=current_collection)
            except (ValueError, Collection.DoesNotExist):
                pass

        # Search
        query_string = None
        if 'q' in request.GET:
            form = SearchForm(request.GET, placeholder=_("Search videos"))
            if form.is_valid():
                query_string = form.cleaned_data['q']
                videos = videos.search(query_string)
        else:
            form = SearchForm(placeholder=_("Search videos"))

        # Pagination
        paginator, videos = paginate(request, videos)  # pylint: disable=unused-variable

        collections = video_permission_policy.collections_user_has_any_permission_for(
            request.user, ['add', 'change']
        )
        if len(collections) < 2:
            collections = None
        action_url_name = self.url_helper.get_action_url_name('index')

        # Create response
        if request.is_ajax():
            return render(request, 'videos/results.html', {
                'view': self,
                'action_url_name': action_url_name,
                'ordering': ordering,
                'videos': videos,
                'query_string': query_string,
                'is_searching': bool(query_string),
            })
        else:
            return render(request, 'videos/index.html', {
                'view': self,
                'action_url_name': action_url_name,
                'ordering': ordering,
                'videos': videos,
                'query_string': query_string,
                'is_searching': bool(query_string),

                'search_form': form,
                'popular_tags': [],
                'user_can_add': False,
                'collections': collections,
                'current_collection': current_collection,
            })
