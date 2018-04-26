from django.conf import settings
from django.core.management.base import BaseCommand
from edx_rest_api_client.client import EdxRestApiClient
from urllib.parse import urlsplit, urlunsplit
from wagtail.wagtailcore.models import Site

from journals.apps.journals.models import Video

import itertools

class Command(BaseCommand):
    help = 'Gathers all videos from relevant courses'

    def rewrite_url_for_external_use(self, url, site):
        '''Updates domain of URLs to use external host in declared in settings'''
        if not site.siteconfiguration.lms_public_url_root_override:
            # Return url if it's not being overwritten
            return url

        split_input_url = urlsplit(url)
        split_override_url = urlsplit(site.siteconfiguration.lms_public_url_root_override)

        final_url = urlunsplit((
            split_override_url.scheme,
            split_override_url.netloc,
            split_input_url.path,
            split_input_url.query,
            split_input_url.fragment,
        ))
        return final_url

    def get_video_course_runs_per_org(self, org):
        """
        Retrieves all video course runs connected to an organization

        Returns an iterable containing all course runs
        """
        journals = org.journal_set.all()
        course_runs = itertools.chain.from_iterable(
            [journal.video_course_ids['course_runs'] for journal in journals]
        )
        return course_runs

    def get_video_course_runs_for_site(self, site):
        orgs = site.organization_set.all()
        course_runs = itertools.chain.from_iterable(
            [self.get_video_course_runs_per_org(org) for org in orgs]
        )
        return course_runs

    def get_videos_for_site(self, site):
        if not hasattr(site, 'siteconfiguration'):
            self.stderr.write("Missing site config for site {}".format(site))
            return []
        client = site.siteconfiguration.lms_courses_api_client
        course_runs = self.get_video_course_runs_for_site(site)
        blocks = []
        for course_run in course_runs:
            try:
                block_response = client.blocks.get(
                    course_id=course_run,
                    depth='all',
                    all_blocks='true',
                    block_types_filter='video',
                    student_view_data='video',
                )
            except Exception as e:
                self.stderr.write("Unable to retrieves blocks from course run {}".format(course_run))
                continue
            blocks.append({
                'site': site,
                'course_run': course_run,
                'blocks': block_response.get('blocks')
            })
        return blocks if blocks else []

    def handle(self, *args, **options):
        """ Collect all videos in courses """

        # Contains a list of dicts that contain a course run and all
        # the blocks in that course run.
        block_collections = itertools.chain.from_iterable(
            [self.get_videos_for_site(site) for site in Site.objects.all()]
        )
        for block_collection in block_collections:
            site = block_collection.get('site')
            course_run = block_collection.get('course_run')
            blocks = block_collection.get('blocks')

            for block in blocks:
                block_id = blocks[block].get('block_id')
                display_name = blocks[block].get('display_name')
                view_url = blocks[block].get('student_view_url')
                transcript_url = blocks[block].get('student_view_data', {}).get('transcripts', {}).get('en')

                view_url = self.rewrite_url_for_external_use(view_url, site)
                self.stdout.write("Creating/updating video block {}".format(block_id))
                Video.objects.update_or_create(
                    block_id=block_id,
                    defaults={
                        'block_id': block_id,
                        'display_name': display_name,
                        'view_url': view_url,
                        'transcript_url': transcript_url,
                        'source_course_run': course_run
                    }
                )
