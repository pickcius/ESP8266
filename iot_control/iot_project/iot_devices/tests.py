from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import CommandDevice, SensorDevice


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

    def test_get_sensor_values_returns_empty_list_for_user_without_sensors(self):
        user = User.objects.create_user(username='emptyuser', password='1234')
        self.client.login(username='emptyuser', password='1234')

        response = self.client.get(reverse('get_sensor_values'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])


class CommandDeviceAccessTests(TestCase):
    def test_control_command_device_requires_ownership(self):
        owner = User.objects.create_user(username='owner', password='1234')
        other_user = User.objects.create_user(username='other', password='1234')
        device = CommandDevice.objects.create(
            name='Lâmpada',
            topic='casa/lampada',
            user=owner,
        )

        self.client.login(username='other', password='1234')
        response = self.client.get(
            reverse('control_command_device', args=[device.id]),
            {'action': 'on'},
        )

        self.assertEqual(response.status_code, 404)
