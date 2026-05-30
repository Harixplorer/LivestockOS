import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/ble/data/mock_ble_data.dart';
import 'package:livestock_os/features/ble/data/models/ble_sensor_device.dart';
import 'package:livestock_os/features/ble/providers/ble_providers.dart';

void main() {
  test('selecting mock sensor updates provider state', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    final device = MockBleData.nearbySensors.first;
    container.read(bleSelectionProvider).selectSensor(device);

    expect(container.read(bleSelectedDeviceProvider), device);
    expect(container.read(bleSelectionProvider).selected, device);
  });

  test('selected sensor and animalId persist in pairing flow state', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    final device = MockBleData.nearbySensors[1];
    final selection = container.read(bleSelectionProvider);
    selection.selectSensor(device);
    selection.setAnimalId('animal-001');

    expect(container.read(bleSelectedDeviceProvider)?.id, device.id);
    expect(container.read(blePairingAnimalIdProvider), 'animal-001');
  });

  test('clear removes selected sensor', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    container.read(bleSelectionProvider).selectSensor(
          MockBleData.nearbySensors.first,
        );
    container.read(bleSelectionProvider).clear();

    expect(container.read(bleSelectedDeviceProvider), isNull);
  });

  test('no selected sensor returns null from provider', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    expect(container.read(bleSelectedDeviceProvider), isNull);
    expect(container.read(bleSelectionProvider).selected, isNull);
  });

  test('mock and real sensors use same BleSensorDevice model', () {
    const mockDevice = BleSensorDevice(
      id: 'LOS-1001',
      name: 'LivestockOS_Sensor',
      rssi: -60,
      batteryPercent: 80,
      availability: BleSensorAvailability.available,
    );
    const realDevice = BleSensorDevice(
      id: 'LOS-2048',
      name: 'LivestockOS_Sensor',
      rssi: -55,
      batteryPercent: 90,
      availability: BleSensorAvailability.available,
      remoteId: 'AA:BB:CC:DD:EE:FF',
    );

    final container = ProviderContainer();
    addTearDown(container.dispose);

    container.read(bleSelectionProvider).selectSensor(mockDevice);
    expect(container.read(bleSelectedDeviceProvider)?.remoteId, isNull);

    container.read(bleSelectionProvider).selectSensor(realDevice);
    expect(
      container.read(bleSelectedDeviceProvider)?.remoteId,
      'AA:BB:CC:DD:EE:FF',
    );
  });
}
