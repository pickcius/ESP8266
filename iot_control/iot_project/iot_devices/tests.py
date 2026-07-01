from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import SensorDevice


class UpdateSensorValueByTopicTests(TestCase):
    def test_update_sensor_value_uses_topic_to_find_sensor(self):
        user = User.objects.create_user(username='tester', password='1234')
        sensor = SensorDevice.objects.create(
            name='Temperatura',
            topic='casa/sala/temperatura',
            user=user,
            current_value=10.0,
        )

        response = self.client.post(
            reverse('update_sensor_value', args=[sensor.topic]),
            {'value': '24.7'},
        )

        sensor.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(sensor.current_value, 24.7)
