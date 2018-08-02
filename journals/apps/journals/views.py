"""
Views for journals app
"""
import logging

from django.conf import settings
from django.contrib import admin, messages
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import View

from journals.apps.core.models import User
from journals.apps.journals.forms import UsersJournalAccessForm
from journals.apps.journals.models import Journal, JournalAccess
from journals.apps.journals.utils import get_default_expiration_date, parse_csv

log = logging.getLogger(__name__)


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
