from django.conf import settings
from django.core.management.base import BaseCommand
from urllib.parse import urlsplit, urlunsplit

from journals.apps.journals.models import Video
from journals.apps.journals.api_client.lms import JwtLmsApiClient


class Command(BaseCommand):
    help = 'Gathers all videos from course into DB'

    def add_arguments(self, parser):
        parser.add_argument('--course')
    
    def rewrite_url_for_external_use(self, url):
        '''Updates domain of URLs to use external host in declared in settings'''
        split_url = urlsplit(url)
        new_url = urlunsplit((
            split_url.scheme, 
            settings.LMS_EXTERNAL_DOMAIN, 
            split_url.path,
            split_url.query,
            split_url.fragment,
        ))
        return new_url

    def handle(self, *args, **options):
        course_id = options.get('course') or settings.DEFAULT_VIDEO_COURSE_RUN_ID
        blocks = JwtLmsApiClient().get_course_blocks(course_id)
        if blocks:
            for block in blocks:
                block_id = blocks[block].get('block_id')
                display_name = blocks[block].get('display_name')
                view_url = blocks[block].get('student_view_url')
                transcript_url = blocks[block].get('student_view_data', {}).get('transcripts', {}).get('en')

                view_url = self.rewrite_url_for_external_use(view_url)

                Video.objects.update_or_create(
                    block_id=block_id,
                    defaults={
                        'block_id': block_id,
                        'display_name': display_name,
                        'view_url': view_url,
                        'transcript_url': transcript_url,
                    },
                )
