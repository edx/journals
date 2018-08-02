"""
Views for journals app
"""
import json
import logging
from io import StringIO

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.decorators import login_required
from django.core import management
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.defaultfilters import linebreaks
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View, TemplateView

from wagtail.contrib.modeladmin.views import WMABaseView
from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailcore.models import Collection

from journals.apps.core.models import User
from journals.apps.journals.permissions import video_permission_policy
from journals.apps.journals.forms import UsersJournalAccessForm
from journals.apps.journals.models import Journal, JournalAccess, Organization
from journals.apps.journals.utils import parse_csv, get_default_expiration_date

log = logging.getLogger(__name__)


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


class JournalAccessView(View):
    """
    View to give journal's access to users.
    """
    template = "admin/journals/journal/import_users.html"

    def get_context(self, request, journal, journal_form=None):
        """
        Returns the context for UsersJournalAccessForm.
        """
        context = {
            'url': reverse('admin:import_users', args=[journal.id]),
            'journal_access_form': journal_form if journal_form else UsersJournalAccessForm(
                initial={'expiration_date': get_default_expiration_date(journal)}
            ),
            'opts': journal._meta,
        }
        context.update(admin.site.each_context(request))
        return context

    def get_or_create_journal_users(self, request, usernames):
        """
        Checks whether the usernames are valid (do exist in journal database)
        if a username doesn't exist then fetch its data from LMS and create
        a user in journal.apps.models.USER

        Returns:
            returns the set of valid usernames (exist in journal database)
        """
        start, offset = 0, settings.BATCH_SIZE_FOR_LMS_USER_API
        existing_users = User.objects.filter(username__in=usernames).values_list('username', flat=True)
        non_existing_users = list(set(usernames) - set(existing_users))
        while start < len(non_existing_users):
            users = set()
            users_lms_data = User.account_details(request, ",".join(non_existing_users[start:start + offset]))
            for user_data in users_lms_data:
                username = user_data['username']
                existing_users.add(username)
                users.add(
                    User(
                        username=username,
                        email=user_data.get('email', ""),
                        is_active=user_data.get('is_active', "False")
                    )
                )
                log.info("'{}' user has been added in journal.".format(username))
            User.objects.bulk_create(list(users))
            start = start + offset
        return existing_users

    def handle_users_import(self, request, journal, journal_access_form):
        """
        Give journal's access to given users.
        """
        usernames = set(
            parse_csv(
                journal_access_form.cleaned_data['bulk_upload_csv']
            )
        )
        valid_usernames = self.get_or_create_journal_users(request, usernames)
        JournalAccess.bulk_create_journal_access(
            valid_usernames,
            journal,
            journal_access_form.cleaned_data['expiration_date']
        )

        skipped_usernames = usernames - set(valid_usernames)
        if skipped_usernames:
            log.warning("Following usernames have been skipped: [{}]".format(", ".join(list(skipped_usernames))))
        return valid_usernames, skipped_usernames

    def _get_valid_journal(self, journal_id):
        journal = Journal.get_journal_by_id(journal_id=journal_id)
        if not journal:
            raise Http404
        return journal

    def get(self, request, journal_id):
        """
        GET request method for JournalAccessView.
        """
        return render(request, self.template, self.get_context(request, self._get_valid_journal(journal_id)))

    def post(self, request, journal_id):
        """
        POST request method for JournalAccessView.
        """
        journal = self._get_valid_journal(journal_id)
        journal_access_form = UsersJournalAccessForm(
            request.POST,
            request.FILES
        )
        if journal_access_form.is_valid():
            added_users, skipped_users = self.handle_users_import(request, journal, journal_access_form)
            messages.success(
                request,
                "'{}' users added successfully and '{}' users skipped.".format(
                    len(added_users),
                    len(skipped_users)
                )
            )
        return render(request, self.template, self.get_context(request, journal, journal_form=journal_access_form))


class VideoImportView(TemplateView):
    """
    View to support video import feature
    """

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.check_action_permitted(request.user):
            raise PermissionDenied
        return super(VideoImportView, self).dispatch(request, *args, **kwargs)

    def check_action_permitted(self, user):
        """
        Check only users with change permissions on videos can import videos
        """
        return video_permission_policy.user_has_permission(user, 'change')

    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            journals = Journal.objects.all()
        else:
            organization = get_object_or_404(Organization, site=request.site)
            journals = organization.journal_set.all()

        course_runs = {journal.id: journal.video_course_ids['course_runs'] for journal in journals}
        collections = video_permission_policy.collections_user_has_any_permission_for(
            request.user, ['add', 'change']
        )
        return render(request, 'videos/import_video.html', {
            'view': self,
            'collections': collections,
            'course_runs': json.dumps(course_runs),
            'journals': journals,
        })

    def post(self, request, *args, **kwargs):
        """
        Calls `gather_video` command to import videos fom lms
        """
        journal_id = int(request.POST.get('journal'))
        collection_id = int(request.POST.get('collection'))
        course_runs = request.POST.getlist('course_runs')
        stdout, stderr = StringIO(), StringIO()
        import_status = management.call_command(
            'gather_videos',
            journal_ids=[journal_id],
            course_runs=course_runs,
            collection_id=collection_id,
            stdout=stdout, stderr=stderr
        )
        success_message = stdout.getvalue()

        # strip import status message from stdout to avoid duplicate message
        success_message = success_message.replace(import_status, '')
        return JsonResponse({
            'journal': journal_id,
            'import_status': import_status,
            'success_message': linebreaks(success_message),
            'failure_message': linebreaks(stderr.getvalue()),
        })
