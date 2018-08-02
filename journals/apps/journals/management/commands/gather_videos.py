"""
Management command to gather all videos from relavant courses.
Possible ways to run this command
To gather videos for all course runs in all sites
`./manage.py gather_videos

To gather videos for course runs in single journal having id 101
`./manage.py gather_videos --journal_ids 101`

To gather videos for course runs in multiple journals having ids 101, 102, 103
`./manage.py gather_videos --journal_ids 101 102 103`
"""
import itertools
from urllib.parse import urlsplit, urlunsplit

from django.core.management.base import BaseCommand
from wagtail.wagtailcore.models import Collection, Site

from journals.apps.journals.models import Journal, Video


class Command(BaseCommand):
    '''Management command to gather course videos'''
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
        """get videos for course runs"""
        orgs = site.organization_set.all()
        course_runs = itertools.chain.from_iterable(
            [self.get_video_course_runs_per_org(org) for org in orgs]
        )
        return course_runs

    def get_collection_for_site(self, site):
        """
        Args:
            site: site object

        Returns: Collection associated with given site
        """
        site_collection_name = site.site_name
        collection = Collection.objects.filter(name=site_collection_name).first()
        if not collection:
            collection = Collection(name=site_collection_name)
            root_collection = Collection.get_first_root_node()
            root_collection.add_child(instance=collection)

        return collection

    def get_videos_for_journal(self, journal_id, course_runs=None):
        """
        Args:
            journal_id:

        Returns: Video blocks for given journal

        """
        video_blocks = []
        try:
            journal = Journal.objects.get(pk=journal_id)
        except Journal.DoesNotExist:
            self.stderr.write('Journal with id %s does not exist' % journal_id)
            return video_blocks

        try:
            journal_site = journal.organization.site
        except Exception:  # pylint: disable=broad-except
            self.stderr.write('Unable to find site for journal with id %s' % journal_id)
            return video_blocks

        if not journal.video_course_ids:
            self.stderr.write('Journal with id %s has empty value in Video Source Course IDs' % journal_id)
            return video_blocks

        if 'course_runs' not in journal.video_course_ids:
            self.stderr.write(
                'Journal with id %s doest not have "course_runs" in Video Source Course IDs' % journal_id
            )
            return video_blocks

        course_runs = course_runs if course_runs else journal.video_course_ids['course_runs']
        return self.get_vidoes_for_course_run(journal_site, course_runs)

    def delete_unused_videos_for_course_run(self, course_run, studio_video_blocks):
        """
        Args:
            course_run: course run
            studio_video_blocks: videos available in given course run

        Deletes unused videos which are deleted from studio but still exists in journals for a course run
        Prints message in stderr for videos which are delete from studio but still in use in journals
        """
        used_journal_videos, unused_journal_videos = [], []
        journal_videos = Video.objects.filter(source_course_run=course_run)
        for video in journal_videos:
            if video.get_usage().count() > 0:
                used_journal_videos.append(video)
            else:
                unused_journal_videos.append(video)

        used_deleted_videos = [video for video in used_journal_videos if video.block_id not in studio_video_blocks]
        for video in used_deleted_videos:
            self.stderr.write(
                "Video '%s' is deleted from '%s' in studio but it is being used in journal"
                % (video.display_name, course_run)
            )

        unused_deleted_videos = [video for video in unused_journal_videos if video.block_id not in studio_video_blocks]
        for video in unused_deleted_videos:
            video.delete()
            self.stdout.write(
                "Video '%s' from '%s' is deleted since it is no longer available in studio"
                % (video.display_name, course_run)
            )

    def get_vidoes_for_course_run(self, site, course_runs):
        """
        Args:
            site: site a journal belong to
            course_runs: course runs where to find videos

        Returns: List of video blocks for given course runs

        """
        blocks = []
        client = site.siteconfiguration.lms_courses_api_client
        for course_run in course_runs:
            try:
                block_response = client.blocks.get(
                    course_id=course_run,
                    depth='all',
                    all_blocks='true',
                    block_types_filter='video',
                    student_view_data='video',
                )
            except Exception:  # pylint: disable=broad-except
                self.stderr.write("Unable to retrieves blocks from course run {}".format(course_run))
                continue
            blocks.append({
                'site': site,
                'course_run': course_run,
                'blocks': block_response.get('blocks')
            })
        return blocks if blocks else []

    def get_videos_for_site(self, site):
        '''get_videos for given site'''
        if not hasattr(site, 'siteconfiguration'):
            self.stderr.write("Missing site config for site {}".format(site))
            return []

        course_runs = self.get_video_course_runs_for_site(site)
        return self.get_vidoes_for_course_run(site, course_runs)

    def add_arguments(self, parser):
        parser.add_argument('--journal_ids', dest='journal_ids', nargs='+', type=int)
        parser.add_argument('--course_runs', dest='course_runs', nargs='+')
        parser.add_argument(
            '--collection_id', dest='collection_id', type=int, help='Collection id to import videos into'
        )

    def handle(self, *args, **options):
        """ Collect all videos in courses """
        collection_id = options['collection_id']
        video_collection = None
        total_video_imported = 0
        if collection_id:
            try:
                video_collection = Collection.objects.get(pk=collection_id)
            except Collection.DoesNotExist:
                self.stderr.write('Collection with id %s does not exist' % collection_id)
                return

        if options['journal_ids']:
            block_collections = itertools.chain.from_iterable(
                [
                    self.get_videos_for_journal(journal_id, options['course_runs'])
                    for journal_id in options['journal_ids']
                ]
            )
        else:
            # Contains a list of dicts that contain a course run and all
            # the blocks in that course run.
            block_collections = itertools.chain.from_iterable(
                [self.get_videos_for_site(site) for site in Site.objects.all()]
            )

        for block_collection in block_collections:
            site = block_collection.get('site')
            collection = video_collection if video_collection else self.get_collection_for_site(site)
            course_run = block_collection.get('course_run')
            blocks = block_collection.get('blocks')
            block_ids = []

            for block in blocks:
                block_id = blocks[block].get('block_id')
                display_name = blocks[block].get('display_name')
                view_url = blocks[block].get('student_view_url')
                transcript_url = blocks[block].get('student_view_data', {}).get('transcripts', {}).get('en')
                view_url = self.rewrite_url_for_external_use(view_url, site)
                block_ids.append(block_id)

                Video.objects.update_or_create(
                    block_id=block_id,
                    defaults={
                        'block_id': block_id,
                        'display_name': display_name,
                        'view_url': view_url,
                        'transcript_url': transcript_url,
                        'source_course_run': course_run,
                        'collection': collection
                    }
                )
                total_video_imported += 1
                self.stdout.write("Imported '%s' from '%s'" % (display_name, course_run))

            self.delete_unused_videos_for_course_run(course_run, block_ids)
        return "Completed, %s videos imported" % total_video_imported
