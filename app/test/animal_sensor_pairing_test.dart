import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/animals/data/animal_constants.dart';
import 'package:livestock_os/features/animals/data/animal_repository.dart';
import 'package:livestock_os/features/animals/data/models/animal.dart';
import 'package:livestock_os/features/animals/presentation/utils/animal_ui_helpers.dart';
import 'package:livestock_os/features/ble/data/mock_ble_data.dart';

void main() {
  group('AnimalRepository sensor pairing', () {
    late AnimalRepository repo;

    setUp(() {
      repo = AnimalRepository.inMemory();
    });

    Future<Animal> addPendingAnimal() {
      return repo.addAnimal(
        name: 'Pair Test Cow',
        tagId: 'TAG-PAIR-TEST',
        breed: 'Gir',
        age: 2,
        gender: AnimalGender.female,
        weight: 300,
      );
    }

    test('pairing does not generate fake health score or readings', () async {
      final added = await addPendingAnimal();
      final paired = await repo.pairSensorToAnimal(
        added.id,
        sensorId: MockBleData.demoSensor.id,
        sensorName: MockBleData.demoSensor.name,
      );

      expect(paired.healthScore, isNull);
      expect(paired.temperature, isNull);
      expect(paired.activityLevel, isNull);
      expect(paired.rumination, isNull);
      expect(paired.hasHealthData, isFalse);
      expect(paired.pairedSensorId, MockBleData.demoSensor.id);
      expect(paired.sensorStatus, AnimalSensorStatus.online);
    });

    test('unpair clears paired sensor fields', () async {
      final added = await addPendingAnimal();
      await repo.pairSensorToAnimal(
        added.id,
        sensorId: 'LOS-1001',
        sensorName: 'LivestockOS_Sensor',
      );

      final unpaired = await repo.unpairSensorFromAnimal(added.id);
      expect(unpaired.pairedSensorId, isNull);
      expect(unpaired.pairedSensorName, isNull);
      expect(unpaired.sensorPairedAt, isNull);
      expect(unpaired.hasLiveSensorConnection, isFalse);
      expect(unpaired.sensorStatus, AnimalSensorStatus.notPaired);
    });

    test('unpair does not delete animal', () async {
      final beforeCount = repo.animals.length;
      final added = await addPendingAnimal();
      await repo.pairSensorToAnimal(
        added.id,
        sensorId: 'LOS-1001',
        sensorName: 'LivestockOS_Sensor',
      );
      await repo.unpairSensorFromAnimal(added.id);

      expect(repo.animals.length, beforeCount + 1);
      expect(repo.animals.any((a) => a.id == added.id), isTrue);
    });

    test('unpair decreases dashboard sensors online count', () async {
      final before = repo.computeHerdStats();
      final added = await addPendingAnimal();
      await repo.pairSensorToAnimal(
        added.id,
        sensorId: 'LOS-1001',
        sensorName: 'LivestockOS_Sensor',
      );
      final afterPair = repo.computeHerdStats();
      expect(afterPair.sensorsOnline, before.sensorsOnline + 1);

      await repo.unpairSensorFromAnimal(added.id);
      final afterUnpair = repo.computeHerdStats();
      expect(afterUnpair.sensorsOnline, before.sensorsOnline);
    });

    test('disconnect live session does not unpair animal', () async {
      final added = await addPendingAnimal();
      await repo.pairSensorToAnimal(
        added.id,
        sensorId: 'LOS-1001',
        sensorName: 'LivestockOS_Sensor',
        hasLiveConnection: true,
      );

      final disconnected = await repo.updateLiveConnectionStatus(
        added.id,
        connected: false,
      );

      expect(disconnected.hasPairedSensor, isTrue);
      expect(disconnected.pairedSensorId, 'LOS-1001');
      expect(disconnected.hasLiveSensorConnection, isFalse);
      expect(disconnected.sensorStatus, AnimalSensorStatus.offline);
    });
  });

  group('Animal detail sensor UI helpers', () {
    test('paired pending animal uses waiting label not connect sensor copy', () async {
      final repo = AnimalRepository.inMemory();
      final added = await repo.addAnimal(
        name: 'UI Pair Cow',
        tagId: 'TAG-UI-PAIR',
        breed: 'Gir',
        age: 2,
        gender: AnimalGender.female,
        weight: 300,
      );
      final paired = await repo.pairSensorToAnimal(
        added.id,
        sensorId: 'LOS-1001',
        sensorName: 'LivestockOS_Sensor',
      );

      expect(paired.hasPairedSensor, isTrue);
      expect(paired.isAwaitingSensorReadings, isTrue);
      expect(detailSensorLabelFor(paired), contains('Waiting for readings'));

      final summary = await repo.fetchHealthSummary(paired.id);
      expect(summary.isPending, isTrue);
      expect(summary.statusMessage, AnimalConstants.waitingForSensorReadings);
      expect(AnimalConstants.pairSensorCta, isNot('Connect Sensor'));
    });

    test('unpaired animal is not paired and uses not paired label', () async {
      final repo = AnimalRepository.inMemory();
      final added = await repo.addAnimal(
        name: 'UI Unpaired Cow',
        tagId: 'TAG-UI-UNP',
        breed: 'Gir',
        age: 2,
        gender: AnimalGender.female,
        weight: 300,
      );

      expect(added.hasPairedSensor, isFalse);
      expect(detailSensorLabelFor(added), 'Not paired');
    });
  });
}
