import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/animals/data/animal_repository.dart';
import 'package:livestock_os/features/animals/data/models/animal.dart';
import 'package:livestock_os/features/animals/providers/animal_providers.dart';
import 'package:livestock_os/features/ble/data/ble_select_animal_next.dart';
import 'package:livestock_os/features/ble/data/models/ble_sensor_device.dart';
import 'package:livestock_os/features/ble/providers/ble_providers.dart';

void main() {
  test('hasAnimalContext is false without animalId', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    expect(
      container.read(bleSelectionProvider).hasAnimalContext(),
      isFalse,
    );
  });

  test('setAnimalId before navigation enables animal context', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    container.read(bleSelectionProvider).setAnimalId('animal-001');

    expect(container.read(bleSelectionProvider).hasAnimalContext(), isTrue);
    expect(
      container.read(bleSelectionProvider).resolveAnimalId(),
      'animal-001',
    );
  });

  test('route animalId takes precedence over provider', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    container.read(bleSelectionProvider).setAnimalId('animal-001');

    expect(
      container.read(bleSelectionProvider).resolveAnimalId(
            routeAnimalId: 'animal-002',
          ),
      'animal-002',
    );
  });

  test('pending animals are prioritized in picker list', () async {
    final container = ProviderContainer(
      overrides: [
        animalRepositoryProvider.overrideWithValue(AnimalRepository.inMemory()),
      ],
    );
    addTearDown(container.dispose);

    final animals = await container.read(bleAnimalPickerListProvider.future);
    expect(animals, isNotEmpty);

    final firstPending = animals.indexWhere(
      (a) => !a.hasHealthData || a.sensorStatus == AnimalSensorStatus.notPaired,
    );
    final firstMonitored = animals.indexWhere((a) => a.hasHealthData);
    if (firstPending >= 0 && firstMonitored >= 0) {
      expect(firstPending, lessThan(firstMonitored));
    }
  });

  test('picker list includes seed and newly added animals', () async {
    final container = ProviderContainer(
      overrides: [
        animalRepositoryProvider.overrideWithValue(AnimalRepository.inMemory()),
      ],
    );
    addTearDown(container.dispose);

    final repo = container.read(animalRepositoryProvider);
    await repo.addAnimal(
      name: 'Picker Cow',
      tagId: 'TAG-PICK-NEW',
      breed: 'Gir',
      age: 2,
      gender: AnimalGender.female,
      weight: 300,
    );

    final animals = await container.read(bleAnimalPickerListProvider.future);
    expect(animals.any((a) => a.tagId == 'TAG-PICK-NEW'), isTrue);
  });

  test('BleSelectAnimalNext parses query values', () {
    expect(
      BleSelectAnimalNext.fromQuery('scan'),
      BleSelectAnimalNext.scan,
    );
    expect(
      BleSelectAnimalNext.fromQuery('mock'),
      BleSelectAnimalNext.mockScan,
    );
    expect(
      BleSelectAnimalNext.fromQuery('manual'),
      BleSelectAnimalNext.manual,
    );
  });

  test('pairing confirm requires animal and sensor in selection state', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    expect(container.read(bleSelectedDeviceProvider), isNull);
    expect(container.read(bleSelectionProvider).hasAnimalContext(), isFalse);

    container.read(bleSelectionProvider).setAnimalId('animal-001');
    container.read(bleSelectionProvider).selectSensor(
          const BleSensorDevice(
            id: 'LOS-1001',
            name: 'LivestockOS_Sensor',
            rssi: -60,
            batteryPercent: 80,
            availability: BleSensorAvailability.available,
          ),
        );

    expect(container.read(bleSelectionProvider).hasAnimalContext(), isTrue);
    expect(container.read(bleSelectedDeviceProvider), isNotNull);
  });
}
