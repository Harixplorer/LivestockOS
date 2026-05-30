import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/animals/data/animal_repository.dart';
import 'package:livestock_os/features/animals/data/models/animal.dart';
import 'package:livestock_os/features/animals/providers/animal_providers.dart';
import 'package:livestock_os/features/ble/data/mock_ble_data.dart';
import 'package:livestock_os/features/ble/data/mock_ble_service.dart';
import 'package:livestock_os/features/ble/data/models/ble_sensor_device.dart';
import 'package:livestock_os/features/ble/data/models/live_sensor_reading.dart';
import 'package:livestock_os/features/ble/providers/ble_providers.dart';

void main() {
  test('mock disconnect emits disconnected reading and stops updates', () async {
    final service = MockBleService();
    final device = MockBleData.nearbySensors.first;

    await service.connect(device);

    final readings = <LiveSensorReading>[];
    final sub = service.liveReadings().listen(readings.add);

    await Future<void>.delayed(const Duration(milliseconds: 50));

    await service.disconnect();
    await Future<void>.delayed(const Duration(milliseconds: 50));

    expect(readings, isNotEmpty);
    expect(readings.last.isConnected, isFalse);
    expect(service.lastReading?.isConnected, isFalse);

    final disconnectedAt = readings.length;
    await Future<void>.delayed(const Duration(seconds: 4));
    final afterDisconnect =
        readings.skip(disconnectedAt).where((r) => r.isConnected);
    expect(afterDisconnect, isEmpty);

    await sub.cancel();
  });

  test('BleLiveMonitorNotifier disconnect updates state to disconnected', () async {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    final device = MockBleData.nearbySensors.first;
    container.read(bleSelectionProvider).selectSensor(device);
    container.read(blePairingActionsProvider).enableMockMode();

    await container.read(bleRepositoryProvider).pairSensor(
          device: device,
          animalId: 'animal-001',
        );

    final notifier = container.read(bleLiveMonitorProvider.notifier);
    await Future<void>.delayed(const Duration(milliseconds: 100));
    expect(container.read(bleLiveMonitorProvider).isConnected, isTrue);

    await notifier.disconnect();

    expect(container.read(bleLiveMonitorProvider).isConnected, isFalse);
    expect(container.read(bleSelectedDeviceProvider), device);
  });

  test('disconnect does not unpair animal pairing fields', () async {
    final animalRepo = AnimalRepository.inMemory();
    final container = ProviderContainer(
      overrides: [
        animalRepositoryProvider.overrideWithValue(animalRepo),
      ],
    );
    addTearDown(container.dispose);
    final added = await animalRepo.addAnimal(
      name: 'Disconnect Test',
      tagId: 'TAG-DIS',
      breed: 'Gir',
      age: 2,
      gender: AnimalGender.female,
      weight: 300,
    );
    await animalRepo.pairSensorToAnimal(
      added.id,
      sensorId: 'LOS-1001',
      sensorName: 'LivestockOS_Sensor',
      hasLiveConnection: true,
    );

    container.read(blePairingAnimalIdProvider.notifier).state = added.id;
    container.read(blePairingActionsProvider).enableMockMode();
    final device = MockBleData.demoSensor;
    container.read(bleSelectionProvider).selectSensor(device);
    await container.read(bleRepositoryProvider).pairSensor(
          device: device,
          animalId: added.id,
        );
    await container.read(bleLiveMonitorProvider.notifier).disconnect();

    final animal = animalRepo.animals.firstWhere((a) => a.id == added.id);
    expect(animal.pairedSensorId, 'LOS-1001');
    expect(animal.hasPairedSensor, isTrue);
  });

  test('disconnect does not clear selected sensor', () async {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    const device = BleSensorDevice(
      id: 'LOS-1001',
      name: 'LivestockOS_Sensor',
      rssi: -60,
      batteryPercent: 80,
      availability: BleSensorAvailability.available,
    );

    container.read(bleSelectionProvider).selectSensor(device);
    container.read(blePairingActionsProvider).enableMockMode();
    await container.read(bleRepositoryProvider).connect(device);
    await container.read(bleLiveMonitorProvider.notifier).disconnect();

    expect(container.read(bleSelectedDeviceProvider), device);
  });
}
