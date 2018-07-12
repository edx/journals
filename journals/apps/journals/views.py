
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import get_permission_codename
from django.views.generic import View
from django.shortcuts import render
from django.urls import reverse

from .forms import UsersJournalAccessForm
from .models import Journal
from .utils import parse_csv, create_journal_access, get_default_expiration_date, get_object


class JournalAccessView(View):
    """
    View to give journal's access to users.
    """
    template = "admin/import_users.html"

    def get_admin_context(self, request, journal):
        """
        Returns the context for default admin panel
        """
        if journal:
            opts = journal._meta
            codename = get_permission_codename('change', opts)
            has_change_permission = request.user.has_perm('%s.%s' % (opts.app_label, codename))
            return {
                'has_change_permission': has_change_permission,
                'opts': opts
            }

    def get_context(self, request, journal_id, journal_form=None):
        """
        Returns the context for UsersJournalAccessForm.
        """
        journal = get_object(Journal, 'id', journal_id)
        context = {
            'url': reverse('admin:import_users', args=[journal_id]),
            'journal_access_form': UsersJournalAccessForm(
                initial={'expiration_date': get_default_expiration_date(journal)}
            ) if not journal_form else journal_form
        }
        context.update(admin.site.each_context(request))
        context.update(self.get_admin_context(request, journal))
        return context

    def _handle_users_import(self, journal_id, journal_access_form):
        """
        Give journal's access to given users.
        """
        usernames = set()
        csv_file = journal_access_form.cleaned_data['bulk_upload_csv']
        parsed_csv = parse_csv(csv_file, expected_columns={'username'})
        for index, row in enumerate(parsed_csv):
            username = row['username']
            if username not in usernames:
                usernames.add(username)
        return create_journal_access(
            usernames,
            journal_id,
            journal_access_form.cleaned_data['expiration_date']
        )

    def get(self, request, journal_id):
        """
        GET request method for JournalAccessView.
        """
        return render(request, self.template, self.get_context(request, journal_id))

    def post(self, request, journal_id):
        """
        POST request method for JournalAccessView.
        """
        journal_access_form = UsersJournalAccessForm(
            request.POST,
            request.FILES
        )
        if journal_access_form.is_valid():
            self._handle_users_import(journal_id, journal_access_form)
            messages.success(request, 'Users have been imported.')

        return render(request, self.template, self.get_context(request, journal_id, journal_form=journal_access_form))