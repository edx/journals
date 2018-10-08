"""
Views for journals app
"""
import json
import logging
from io import StringIO

from django.contrib.auth.decorators import login_required
from django.core import management
from django.core.exceptions import PermissionDenied
from django.core.management import CommandError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.defaultfilters import linebreaks
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from wagtail.contrib.modeladmin.views import WMABaseView, EditView, CreateView, DeleteView
from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel, ObjectList
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.navigation import get_explorable_root_page
from wagtail.wagtailadmin.views.pages import move_choose_destination
from wagtail.wagtailcore.models import Collection

from journals.apps.journals.api_utils import get_discovery_journal
from journals.apps.journals.wagtailadmin.forms import JournalEditForm, JournalCreateForm
from journals.apps.journals.wagtailadmin.tasks import task_run_management_command
from journals.apps.journals.models import Journal, Organization
from journals.apps.journals.permissions import video_permission_policy
from journals.apps.journals.utils import add_messages

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


class JournalIndexView(WMABaseView):
    """
        Journal Index View for wagtail CMS
    """

    def append_discovery_data(self, journals):
        """
            get relevant data from discovery and then add to Journal objects
        """
        uuid_list = ','.join([str(uuid) for uuid in journals.values_list('uuid', flat=True)])
        journals_discovery_data = get_discovery_journal(
            self.request.site.siteconfiguration.discovery_journal_api_client, uuid_list
        )
        for journal in journals:
            journal_discovery_data = next(
                (data for data in journals_discovery_data if data['uuid'] == str(journal.uuid)), None)
            if journal_discovery_data:
                setattr(journal, 'price', journal_discovery_data['price'])
                setattr(journal, 'currency', journal_discovery_data['currency'])
                setattr(journal, 'status', journal_discovery_data['status'])

    def get(self, request, *args, **kwargs):
        """
           Handle GET request
        """

        if request.user.is_superuser:
            journals = Journal.objects.all()
        else:
            journals = Journal.objects.filter(organization__site=request.site)
        # Ordering
        if 'ordering' in request.GET and request.GET['ordering'] in [
            'name', 'organization'
        ]:
            ordering = request.GET['ordering']
        else:
            ordering = 'name'
        journals = journals.order_by(ordering)

        # Pagination
        paginator, journals = paginate(request, journals)  # pylint: disable=unused-variable

        self.append_discovery_data(journals.object_list)

        action_url_name = self.url_helper.get_action_url_name('index')
        create_url_name = self.url_helper.get_action_url_name('create')

        return render(request, 'journals/admin_index.html', {
            'view': self,
            'ordering': ordering,
            'journals': journals,
            'popular_tags': [],
            'action_url_name': action_url_name,
            'create_url_name': create_url_name
        })


class JournalAdminEditView(EditView):
    """
        Edit view for Journal in wagtail CMS
    """
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('status'),
            FieldPanel('video_course_ids'),
        ])
    ]
    edit_handler = ObjectList(panels)

    def get_edit_handler_class(self):
        """
            Overridden to get custom handler
        """
        return self.edit_handler.bind_to_model(self.model)

    def get_initial(self):
        """
            Overridden to get initial for journal status from discovery
        """
        initials = super(JournalAdminEditView, self).get_initial()
        journal_discovery_results = get_discovery_journal(
            self.request.site.siteconfiguration.discovery_journal_api_client, self.instance.uuid
        )
        if journal_discovery_results:
            initials. update({'status': True if journal_discovery_results[0]['status'] == 'active' else False})
        return initials

    def get_form_class(self):
        """
            Returns the form class to use in this view
        """
        return JournalEditForm

    def form_invalid(self, form):
        """
            Overridden to fix for wagtail not displaying non-field related errors.
            Code snippet is taken from wagtail latest release (2.1.1)
        """
        messages.validation_error(
            self.request, self.get_error_message(), form
        )
        return self.render_to_response(self.get_context_data())

    def update_journal_on_other_services(self, data):
        """
            Using publish_journal command update Journal other services like discovery and e-commerce etc
        """
        stdout, stderr = StringIO(), StringIO()
        management.call_command('publish_journals', update=self.instance.uuid, publish=data['status'], stdout=stdout,
                                stderr=stderr)

        add_messages(self.request, 'success', stdout.getvalue().split('\n'))
        add_messages(self.request, 'error', stderr.getvalue().split('\n'))

    def post(self, request, *args, **kwargs):
        """
            Overridden to call update journal command if form is valid
        """
        form = self.get_form()
        if form.is_valid():
            response = self.form_valid(form)
            self.update_journal_on_other_services(form.cleaned_data)
            return response
        else:
            return self.form_invalid(form)


class JournalAdminCreateView(CreateView):
    """
        Journals Create/Add view for wagtail CMS
    """
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('access_length'),
            FieldPanel('organization'),
            FieldPanel('video_course_ids'),
            FieldPanel('price'),
            FieldPanel('currency'),
        ])
    ]
    edit_handler = ObjectList(panels)

    def get_form_kwargs(self):
        """
            Overridden to add request to form kwargs
        """
        kwargs = super(JournalAdminCreateView, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def get_edit_handler_class(self):
        """
         Overridden to use custom edit_handle
        """
        return self.edit_handler.bind_to_model(self.model)

    def form_invalid(self, form):
        """
            Overridden to fix for wagtail not displaying non-field related errors.
            Code snippet is taken from wagtail latest release (2.1.1)
        """
        messages.validation_error(
            self.request, self.get_error_message(), form
        )
        return self.render_to_response(self.get_context_data())

    def get_form_class(self):
        """
        Returns the form class to use in this view
        """
        return JournalCreateForm

    def create_journal_on_other_services(self, data):
        """
            Using publish_journal command create Journal other services like discovery and e-commerce etc
        """
        stdout, stderr = StringIO(), StringIO()
        try:
            management.call_command('publish_journals', create=data['name'], org=data['organization'].name,
                                    access_length=data['access_length'], price=data['price'],
                                    currency=data['currency'], publish=False, stdout=stdout, stderr=stderr)
        except CommandError as e:
            add_messages(self.request, 'error', [str(e)])

        add_messages(self.request, 'success', stdout.getvalue().split('\n'))
        add_messages(self.request, 'error', stderr.getvalue().split('\n'))

    def post(self, request, *args, **kwargs):
        """
            Overridden to call create journal command if form is valid
        """
        form = self.get_form()
        if form.is_valid():
            response = self.form_valid(form)
            self.create_journal_on_other_services(form.cleaned_data)
            return response
        else:
            return self.form_invalid(form)


class JournalAdminDeleteView(DeleteView):
    """
        Journals Delete view for wagtail CMS
    """

    def confirmation_message(self):
        """overridden to custom confirmation message"""
        return _(
            'Are you sure you want to delete this {instance}? All pages created in this {instance} will be'
            ' deleted as well. Please use caution.'.format(instance=self.verbose_name)
        )

    def delete_journal_on_other_services(self):
        """
            Using publish_journal command delete Journal other services like discovery and e-commerce etc
        """
        stdout, stderr = StringIO(), StringIO()
        try:
            management.call_command('publish_journals', delete=self.instance.uuid, stdout=stdout, stderr=stderr)
        except CommandError as e:
            add_messages(self.request, 'error', [str(e)])

        add_messages(self.request, 'success', stdout.getvalue().split('\n'))
        add_messages(self.request, 'error', stderr.getvalue().split('\n'))

    def delete_instance(self):
        """ Overridden to delete using management command"""
        self.delete_journal_on_other_services()


class AdminCommandsView(TemplateView):
    """
    View to run management commands from wagtail admin
    """
    template_name = 'wagtailadmin/commands.html'
    allowed_commands = ['update_index', 'fixtree']

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return super(AdminCommandsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['allowed_commands'] = self.allowed_commands
        return kwargs

    def post(self, request, *args, **kwargs):
        """
        Runs given management command
        """
        management_command = request.POST.get('management_command')
        stdout, stderr = StringIO(), StringIO()
        if management_command not in self.allowed_commands:
            stderr.write('Unknown command "%s"' % management_command)
        else:
            try:
                task_run_management_command(management_command)
                stdout.write("Command %s successully queued to run in the background process." % management_command)
            except Exception as ex:  # pylint: disable=broad-except
                stderr.write(str(ex))

        return JsonResponse({
            'success_message': linebreaks(stdout.getvalue()),
            'failure_message': linebreaks(stderr.getvalue()),
        })


def move_page(request, page_to_move_id):
    """
    Args:
        request: http request object
        page_to_move_id: id of the page to move

    This method sets viewed_page id to site's root page and calls wagtail's move page view
    Reason we override `cms/pages/(page_to_move_id)/move` view is to show user only those
    destinations where user has permissions

    """
    viewed_page = get_explorable_root_page(request.user)
    return move_choose_destination(request, page_to_move_id, viewed_page_id=viewed_page.id)
