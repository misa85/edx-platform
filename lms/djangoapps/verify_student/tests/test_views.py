# encoding: utf-8
"""


verify_student/start?course_id=MITx/6.002x/2013_Spring # create
              /upload_face?course_id=MITx/6.002x/2013_Spring
              /upload_photo_id
              /confirm # mark_ready()

 ---> To Payment

"""
import json
import mock
import urllib
from mock import patch, Mock
import pytz
from datetime import timedelta, datetime

from django.test.client import Client
from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from course_modes.models import CourseMode
from verify_student.views import render_to_response
from verify_student.models import SoftwareSecurePhotoVerification
from reverification.tests.factories import MidcourseReverificationWindowFactory



def mock_render_to_response(*args, **kwargs):
    return render_to_response(*args, **kwargs)

render_mock = Mock(side_effect=mock_render_to_response)


class StartView(TestCase):

    def start_url(self, course_id=""):
        return "/verify_student/{0}".format(urllib.quote(course_id))

    def test_start_new_verification(self):
        """
        Test the case where the user has no pending `PhotoVerficiationAttempts`,
        but is just starting their first.
        """
        user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")

    def must_be_logged_in(self):
        self.assertHttpForbidden(self.client.get(self.start_url()))


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestVerifyView(TestCase):
    def setUp(self):
        self.user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")
        self.course_id = 'Robot/999/Test_Course'
        CourseFactory.create(org='Robot', number='999', display_name='Test Course')
        verified_mode = CourseMode(course_id=self.course_id,
                                   mode_slug="verified",
                                   mode_display_name="Verified Certificate",
                                   min_price=50)
        verified_mode.save()

    def test_invalid_course(self):
        fake_course_id = "Robot/999/Fake_Course"
        url = reverse('verify_student_verify',
                      kwargs={"course_id": fake_course_id})
        response = self.client.get(url)

        self.assertEquals(response.status_code, 302)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestReverifyView(TestCase):
    """
    Tests for the reverification views

    """
    def setUp(self):
        self.user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")
        self.course_id = "MITx/999/Robot_Super_Course"
        self.course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')

    @patch('verify_student.views.render_to_response', render_mock)
    def test_reverify_get(self):
        url = reverse('verify_student_reverify')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        ((_template, context), _kwargs) = render_mock.call_args
        self.assertFalse(context['error'])

    @patch('verify_student.views.render_to_response', render_mock)
    def test_reverify_post_failure(self):
        url = reverse('verify_student_reverify')
        response = self.client.post(url, {'face_image': '',
                                          'photo_id_image': ''})
        self.assertEquals(response.status_code, 200)
        ((template, context), _kwargs) = render_mock.call_args
        self.assertIn('photo_reverification', template)
        self.assertTrue(context['error'])

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_reverify_post_success(self):
        url = reverse('verify_student_reverify')
        response = self.client.post(url, {'face_image': ',',
                                          'photo_id_image': ','})
        self.assertEquals(response.status_code, 302)
        try:
            verification_attempt = SoftwareSecurePhotoVerification.objects.get(user=self.user)
            self.assertIsNotNone(verification_attempt)
        except ObjectDoesNotExist:
            self.fail('No verification object generated')
        ((template, context), _kwargs) = render_mock.call_args
        self.assertIn('photo_reverification', template)
        self.assertTrue(context['error'])


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestPhotoVerificationResultsCallback(TestCase):
    """
    Tests for the results_callback view.
    """
    def setUp(self):
        self.course_id = 'Robot/999/Test_Course'
        CourseFactory.create(org='Robot', number='999', display_name='Test Course')
        self.user = UserFactory.create()
        self.attempt = SoftwareSecurePhotoVerification(
            status="submitted",
            user=self.user
        )
        self.attempt.save()
        self.receipt_id = self.attempt.receipt_id
        self.client = Client()

    def mocked_has_valid_signature(method, headers_dict, body_dict, access_key, secret_key):
        return True

    def test_invalid_json(self):
        """
        Test for invalid json being posted by software secure.
        """
        data = {"Testing invalid"}
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB: testing',
            HTTP_DATE='testdate'
        )
        self.assertIn('Invalid JSON', response.content)
        self.assertEqual(response.status_code, 400)

    def test_invalid_dict(self):
        """
        Test for invalid dictionary being posted by software secure.
        """
        data = '"\\"Test\\tTesting"'
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        self.assertIn('JSON should be dict', response.content)
        self.assertEqual(response.status_code, 400)

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_invalid_access_key(self):
        """
        Test for invalid access key.
        """
        data = {
            "EdX-ID": self.receipt_id,
            "Result": "Testing",
            "Reason": "Testing",
            "MessageType": "Testing"
        }
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test testing:testing',
            HTTP_DATE='testdate'
        )
        self.assertIn('Access key invalid', response.content)
        self.assertEqual(response.status_code, 400)

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_wrong_edx_id(self):
        """
        Test for wrong id of Software secure verification attempt.
        """
        data = {
            "EdX-ID": "Invalid-Id",
            "Result": "Testing",
            "Reason": "Testing",
            "MessageType": "Testing"
        }
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        self.assertIn('edX ID Invalid-Id not found', response.content)
        self.assertEqual(response.status_code, 400)

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_pass_result(self):
        """
        Test for verification passed.
        """
        data = {
            "EdX-ID": self.receipt_id,
            "Result": "PASS",
            "Reason": "",
            "MessageType": "You have been verified."
        }
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'), data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        attempt = SoftwareSecurePhotoVerification.objects.get(receipt_id=self.receipt_id)
        self.assertEqual(attempt.status, u'approved')
        self.assertEquals(response.content, 'OK!')

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_fail_result(self):
        """
        Test for failed verification.
        """
        data = {
            "EdX-ID": self.receipt_id,
            "Result": 'FAIL',
            "Reason": 'Invalid photo',
            "MessageType": 'Your photo doesn\'t meet standards.'
        }
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        attempt = SoftwareSecurePhotoVerification.objects.get(receipt_id=self.receipt_id)
        self.assertEqual(attempt.status, u'denied')
        self.assertEqual(attempt.error_code, u'Your photo doesn\'t meet standards.')
        self.assertEqual(attempt.error_msg, u'"Invalid photo"')
        self.assertEquals(response.content, 'OK!')

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_system_fail_result(self):
        """
        Test for software secure result system failure.
        """
        data = {"EdX-ID": self.receipt_id,
                "Result": 'SYSTEM FAIL',
                "Reason": 'Memory overflow',
                "MessageType": 'You must retry the verification.'}
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        attempt = SoftwareSecurePhotoVerification.objects.get(receipt_id=self.receipt_id)
        self.assertEqual(attempt.status, u'must_retry')
        self.assertEqual(attempt.error_code, u'You must retry the verification.')
        self.assertEqual(attempt.error_msg, u'"Memory overflow"')
        self.assertEquals(response.content, 'OK!')

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_unknown_result(self):
        """
        test for unknown software secure result
        """
        data = {
            "EdX-ID": self.receipt_id,
            "Result": 'Unknown',
            "Reason": 'Unknown reason',
            "MessageType": 'Unknown message'
        }
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        self.assertIn('Result Unknown not understood', response.content)

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_reverification(self):
        """
         Test software secure result for reverification window.
        """
        data = {
            "EdX-ID": self.receipt_id,
            "Result": "PASS",
            "Reason": "",
            "MessageType": "You have been verified."
        }
        window = MidcourseReverificationWindowFactory(course_id=self.course_id)
        self.attempt.window = window
        self.attempt.save()
        json_data = json.dumps(data)
        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id).count(), 0)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        self.assertEquals(response.content, 'OK!')
        self.assertIsNotNone(CourseEnrollment.objects.get(course_id=self.course_id))


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestMidCourseReverifyView(TestCase):
    """ Tests for the midcourse reverification views """
    def setUp(self):
        self.user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")
        self.course_id = 'Robot/999/Test_Course'
        CourseFactory.create(org='Robot', number='999', display_name='Test Course')

        patcher = patch('student.models.tracker')
        self.mock_tracker = patcher.start()
        self.addCleanup(patcher.stop)

    @patch('verify_student.views.render_to_response', render_mock)
    def test_midcourse_reverify_get(self):
        url = reverse('verify_student_midcourse_reverify',
                      kwargs={"course_id": self.course_id})
        response = self.client.get(url)

        # Check that user entering the reverify flow was logged
        self.mock_tracker.emit.assert_called_once_with(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.reverify.started',
            {
                'user_id': self.user.id,
                'course_id': self.course_id,
                'mode': "verified",
            }
        )
        self.mock_tracker.emit.reset_mock()  # pylint: disable=maybe-no-member

        self.assertEquals(response.status_code, 200)
        ((_template, context), _kwargs) = render_mock.call_args
        self.assertFalse(context['error'])

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_midcourse_reverify_post_success(self):
        window = MidcourseReverificationWindowFactory(course_id=self.course_id)
        url = reverse('verify_student_midcourse_reverify', kwargs={'course_id': self.course_id})

        response = self.client.post(url, {'face_image': ','})

        # Check that submission event was logged
        self.mock_tracker.emit.assert_called_once_with(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.reverify.submitted',
            {
                'user_id': self.user.id,
                'course_id': self.course_id,
                'mode': "verified",
            }
        )
        self.mock_tracker.emit.reset_mock()  # pylint: disable=maybe-no-member

        self.assertEquals(response.status_code, 302)
        try:
            verification_attempt = SoftwareSecurePhotoVerification.objects.get(user=self.user, window=window)
            self.assertIsNotNone(verification_attempt)
        except ObjectDoesNotExist:
            self.fail('No verification object generated')

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_midcourse_reverify_post_failure_expired_window(self):
        window = MidcourseReverificationWindowFactory(
            course_id=self.course_id,
            start_date=datetime.now(pytz.UTC) - timedelta(days=100),
            end_date=datetime.now(pytz.UTC) - timedelta(days=50),
        )
        url = reverse('verify_student_midcourse_reverify', kwargs={'course_id': self.course_id})
        response = self.client.post(url, {'face_image': ','})
        self.assertEquals(response.status_code, 302)
        with self.assertRaises(ObjectDoesNotExist):
            SoftwareSecurePhotoVerification.objects.get(user=self.user, window=window)

    @patch('verify_student.views.render_to_response', render_mock)
    def test_midcourse_reverify_dash(self):
        url = reverse('verify_student_midcourse_reverify_dash')
        response = self.client.get(url)
        # not enrolled in any courses
        self.assertEquals(response.status_code, 200)

        enrollment = CourseEnrollment.get_or_create_enrollment(self.user, self.course_id)
        enrollment.update_enrollment(mode="verified", is_active=True)
        MidcourseReverificationWindowFactory(course_id=self.course_id)
        response = self.client.get(url)
        # enrolled in a verified course, and the window is open
        self.assertEquals(response.status_code, 200)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestReverificationBanner(TestCase):
    """ Tests for the midcourse reverification  failed toggle banner off """

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def setUp(self):
        self.user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")
        self.course_id = 'Robot/999/Test_Course'
        CourseFactory.create(org='Robot', number='999', display_name=u'Test Course é')
        self.window = MidcourseReverificationWindowFactory(course_id=self.course_id)
        url = reverse('verify_student_midcourse_reverify', kwargs={'course_id': self.course_id})
        self.client.post(url, {'face_image': ','})
        photo_verification = SoftwareSecurePhotoVerification.objects.get(user=self.user, window=self.window)
        photo_verification.status = 'denied'
        photo_verification.save()

    def test_banner_display_off(self):
        self.client.post(reverse('verify_student_toggle_failed_banner_off'))
        photo_verification = SoftwareSecurePhotoVerification.objects.get(user=self.user, window=self.window)
        self.assertFalse(photo_verification.display)
