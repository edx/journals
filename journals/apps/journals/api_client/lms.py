import json
import requests

from django.conf import settings


class JwtLmsApiClient(object):

    def get_access_token(self):
        url = settings.LMS_BASE_INTERNAL_URL + "/oauth2/access_token"
        payload = {
            'grant_type': 'client_credentials',
            'client_id': settings.LMS_CLIENT_ID,
            'client_secret': settings.LMS_CLIENT_SECRET,
            'token_type': 'jwt',
        }
        response = requests.post(url, data=payload)
        return response.json().get('access_token')

    def get_course_blocks(self, course_id):
        query_string = "?course_id={course_id}&depth=all&all_blocks=true&block_types_filter=video&student_view_data=video".format(
            course_id=course_id
        )
        url = settings.LMS_BASE_INTERNAL_URL + settings.LMS_BLOCK_API_PATH + query_string
        headers = {
            "Authorization": "JWT {access_token}".format(access_token=self.get_access_token())
        }
        response = requests.get(url, headers=headers)
        return response.json().get('blocks')

    def get_video_transcript(self, transcript_url):
        headers = {
            "Authorization": "JWT {access_token}".format(access_token=self.get_access_token())
        }
        response = requests.get(transcript_url, headers=headers)
        return response.content
