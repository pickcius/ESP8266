from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserChangeForm
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .models import CommandDevice, SensorDevice
from .mqtt_client import publish_message

@login_required
def device_list(request):
    command_devices = CommandDevice.objects.filter(user=request.user)
    sensor_devices = SensorDevice.objects.filter(user=request.user)
    return render(request, 'iot_devices/device_list.html', {
        'command_devices': command_devices,
        'sensor_devices': sensor_devices
    })

@login_required
def add_device(request):
    if request.method == "POST":
        device_type = request.POST.get('type')
        name = request.POST.get('name', '').strip()
        topic = request.POST.get('topic', '').strip()

        if not topic:
            messages.error(request, 'O tópico MQTT não pode ficar vazio.')
            return render(request, 'iot_devices/add_device.html')

        try:
            if device_type == 'command':
                CommandDevice.objects.create(name=name, topic=topic, user=request.user)
            elif device_type == 'sensor':
                SensorDevice.objects.create(name=name, topic=topic, user=request.user)
            else:
                messages.error(request, 'Tipo de dispositivo inválido.')
                return render(request, 'iot_devices/add_device.html')
        except IntegrityError:
            messages.error(request, 'Este tópico MQTT já está em uso por outro dispositivo.')
            return render(request, 'iot_devices/add_device.html')

        return redirect('device_list')
    return render(request, 'iot_devices/add_device.html')

@login_required
def control_command_device(request, device_id):
    device = get_object_or_404(CommandDevice, id=device_id, user=request.user)
    action = request.GET.get('action')  # 'on' ou 'off'
    if action in ['on', 'off']:
        publish_message(device.topic, action)
    return redirect('device_list')

@login_required
def edit_device(request, device_id):
    print("Editing device with ID:", device_id)
    pk = device_id

    # Tenta obter o dispositivo como CommandDevice ou SensorDevice
    try:
        device = CommandDevice.objects.get(id=pk, user=request.user)
    except CommandDevice.DoesNotExist:
        try:
            device = SensorDevice.objects.get(id=pk, user=request.user)
        except SensorDevice.DoesNotExist:
            # Nenhum dos dispositivos foi encontrado
            return redirect('device_list')  # Ou raise 404

    if request.method == "POST":
        device.name = request.POST.get('name')
        new_topic = request.POST.get('topic', '').strip()

        if not new_topic:
            messages.error(request, 'O tópico MQTT não pode ficar vazio.')
            return render(request, 'iot_devices/edit_device.html', {'device': device})

        if SensorDevice.objects.filter(topic=new_topic).exclude(pk=device.pk).exists() or CommandDevice.objects.filter(topic=new_topic).exclude(pk=device.pk).exists():
            messages.error(request, 'Este tópico MQTT já está em uso por outro dispositivo.')
            return render(request, 'iot_devices/edit_device.html', {'device': device})

        device.topic = new_topic
        device.save()
        return redirect('device_list')
    return render(request, 'iot_devices/edit_device.html', {'device': device})

@login_required
def delete_device(request, device_id):
    pk = device_id
    
    # Tenta obter o dispositivo como CommandDevice ou SensorDevice
    try:
        device = CommandDevice.objects.get(id=pk, user=request.user)
    except CommandDevice.DoesNotExist:
        try:
            device = SensorDevice.objects.get(id=pk, user=request.user)
        except SensorDevice.DoesNotExist:
            # Nenhum dos dispositivos foi encontrado
            return redirect('device_list')  # Ou raise 404
    
    print("Deleting device with ID:", device_id)

    if request.method == "POST":
        device.delete()
        return redirect('device_list')
    return render(request, 'iot_devices/delete_device.html', {'device': device})

@csrf_exempt##Cuidado ao utilizar o csrf_exempt, pois pode abrir brechas de segurança e permite requisições de qualquer origem
def update_sensor_value(request, sensor_topic):
    print("Updating sensor value for topic:", sensor_topic)

    if request.method == "POST":
        value = request.POST.get("value")
        try:
            sensor = get_object_or_404(SensorDevice, topic=sensor_topic)
            sensor.current_value = float(value)
            sensor.save()
        except ValueError:
            pass  # Trate se o valor não for numérico
    return redirect('device_list')

@login_required #corrigir atualização via ajax, que não pode estar autenticado.
#@csrf_exempt ##corrigir atualização via ajax, que não pode estar autenticado.
def get_sensor_values(request):
    sensors = SensorDevice.objects.filter(user=request.user)
    data = [
        {
            'id': sensor.id,
            'name': sensor.name,
            'topic': sensor.topic,
            'current_value': sensor.current_value if sensor.current_value is not None else "N/D",
            'unit': sensor.unit
        }
        for sensor in sensors
    ]
    return JsonResponse(data, safe=False)


@login_required
def profile(request):
    return render(request, 'registration/profile.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserChangeForm(instance=request.user)
    return render(request, 'registration/edit_profile.html', {'form': form})