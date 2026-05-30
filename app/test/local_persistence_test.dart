import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/core/persistence/local_storage_service.dart';
import 'package:livestock_os/features/alerts/data/alert_repository.dart';
import 'package:livestock_os/features/animals/data/animal_repository.dart';
import 'package:livestock_os/features/animals/data/models/animal.dart';
import 'package:livestock_os/features/auth/data/auth_repository.dart';
import 'package:livestock_os/features/auth/data/models/farmer_registration.dart';
import 'package:livestock_os/features/settings/data/models/user_settings.dart';
import 'package:livestock_os/features/settings/data/settings_repository.dart';

import 'persistence_test_helpers.dart';

const _testAccountA = '9876543210';

Future<AnimalRepository> _reloadAnimalRepo(
  LocalStorageService storage, {
  String? accountKey,
}) async {
  return AnimalRepository(storage, accountKey: accountKey);
}

Future<AlertRepository> _reloadAlertRepo(
  LocalStorageService storage,
  AnimalRepository animals, {
  String? accountKey,
}) async {
  return AlertRepository(animals, storage, accountKey: accountKey);
}

void main() {
  group('local persistence', () {
    test('added animal persists after repository reload', () async {
      final storage = await createTestLocalStorage();
      final repo = await _reloadAnimalRepo(storage, accountKey: _testAccountA);
      final before = repo.animals.length;

      final added = await repo.addAnimal(
        name: 'Persist Cow',
        tagId: 'TAG-PERSIST',
        breed: 'Gir',
        age: 2,
        gender: AnimalGender.female,
        weight: 320,
      );

      final reloaded = await _reloadAnimalRepo(storage, accountKey: _testAccountA);
      expect(reloaded.animals.length, before + 1);
      expect(reloaded.findAnimalById(added.id)?.name, 'Persist Cow');
    });

    test('edited animal persists after reload', () async {
      final storage = await createTestLocalStorage();
      final repo = await _reloadAnimalRepo(storage, accountKey: _testAccountA);
      final original = repo.animals.first;

      await repo.updateAnimal(original.copyWith(name: 'Edited Seed Name'));

      final reloaded = await _reloadAnimalRepo(storage, accountKey: _testAccountA);
      expect(
        reloaded.findAnimalById(original.id)?.name,
        'Edited Seed Name',
      );
    });

    test('paired sensor state persists after reload', () async {
      final storage = await createTestLocalStorage();
      final repo = await _reloadAnimalRepo(storage, accountKey: _testAccountA);
      final added = await repo.addAnimal(
        name: 'Pair Target',
        tagId: 'TAG-PAIR',
        breed: 'Gir',
        age: 3,
        gender: AnimalGender.male,
        weight: 400,
      );

      await repo.pairSensorToAnimal(
        added.id,
        sensorId: 'sensor-99',
        sensorName: 'Collar 99',
        hasLiveConnection: true,
      );

      final reloaded = await _reloadAnimalRepo(storage, accountKey: _testAccountA);
      final restored = reloaded.findAnimalById(added.id)!;

      expect(restored.pairedSensorId, 'sensor-99');
      expect(restored.pairedSensorName, 'Collar 99');
      expect(restored.sensorPairedAt, isNotNull);
      expect(restored.hasPairedSensor, isTrue);
      expect(restored.hasLiveSensorConnection, isFalse);
    });

    test('unpair persists after reload', () async {
      final storage = await createTestLocalStorage();
      final repo = await _reloadAnimalRepo(storage, accountKey: _testAccountA);
      final added = await repo.addAnimal(
        name: 'Unpair Target',
        tagId: 'TAG-UNPAIR',
        breed: 'Gir',
        age: 2,
        gender: AnimalGender.female,
        weight: 300,
      );

      await repo.pairSensorToAnimal(
        added.id,
        sensorId: 'sensor-1',
        sensorName: 'Collar 1',
      );
      await repo.unpairSensorFromAnimal(added.id);

      final reloaded = await _reloadAnimalRepo(storage, accountKey: _testAccountA);
      final restored = reloaded.findAnimalById(added.id)!;

      expect(restored.pairedSensorId, isNull);
      expect(restored.pairedSensorName, isNull);
      expect(restored.sensorStatus, AnimalSensorStatus.notPaired);
    });

    test('resolved alert state persists after reload', () async {
      final storage = await createTestLocalStorage();
      final animals = await _reloadAnimalRepo(storage, accountKey: _testAccountA);
      final alerts = await _reloadAlertRepo(
        storage,
        animals,
        accountKey: _testAccountA,
      );

      final target = (await alerts.fetchAlerts()).firstWhere((a) => !a.isResolved);
      await alerts.setResolved(id: target.id, isResolved: true);

      final reloadedAnimals = await _reloadAnimalRepo(storage, accountKey: _testAccountA);
      final reloadedAlerts = await _reloadAlertRepo(
        storage,
        reloadedAnimals,
        accountKey: _testAccountA,
      );
      final restored = await reloadedAlerts.fetchAlertById(target.id);

      expect(restored?.isResolved, isTrue);
    });

    test('theme mode persists after reload', () async {
      final storage = await createTestLocalStorage();
      await storage.saveThemeMode(ThemeMode.dark);

      expect(storage.loadThemeMode(), ThemeMode.dark);
    });

    test('notification settings persist after reload', () async {
      final storage = await createTestLocalStorage();
      final settingsRepo = SettingsRepository(storage, accountKey: _testAccountA);

      await settingsRepo.updateNotifications(
        const NotificationPreferences(dailySummary: true, pushNotifications: true),
      );

      final reloaded = SettingsRepository(storage, accountKey: _testAccountA);
      final settings = await reloaded.fetchSettings();

      expect(settings.notifications.dailySummary, isTrue);
      expect(settings.notifications.pushNotifications, isTrue);
    });

    test('profile edit persists after reload', () async {
      final storage = await createTestLocalStorage();
      final authRepo = AuthRepository(storage);

      await authRepo.registerAccount(
        const FarmerRegistration(
          fullName: 'Persist Farmer',
          phoneNumber: '9876543210',
          farmName: 'Persist Farm',
          village: 'Village',
          district: 'District',
          state: 'State',
        ),
      );

      await authRepo.updateProfile(
        const FarmerRegistration(
          fullName: 'Updated Farmer',
          phoneNumber: '9876543210',
          farmName: 'Updated Farm',
          village: 'New Village',
          district: 'District',
          state: 'State',
        ),
      );

      final reloaded = AuthRepository(storage);
      expect(reloaded.currentState.profile?.fullName, 'Updated Farmer');
      expect(reloaded.currentState.profile?.farmName, 'Updated Farm');
    });

    test('pending animal still has no fake readings after reload', () async {
      final storage = await createTestLocalStorage();
      final repo = await _reloadAnimalRepo(storage, accountKey: _testAccountA);

      final added = await repo.addAnimal(
        name: 'Pending Reload',
        tagId: 'TAG-PENDING',
        breed: 'Gir',
        age: 1,
        gender: AnimalGender.female,
        weight: 250,
      );

      final reloaded = await _reloadAnimalRepo(storage, accountKey: _testAccountA);
      final restored = reloaded.findAnimalById(added.id)!;
      final readings = await reloaded.fetchRecentReadings(added.id);
      final trends = await reloaded.fetchTrends(added.id);

      expect(restored.hasHealthData, isFalse);
      expect(restored.status, AnimalHealthStatus.notMonitored);
      expect(readings, isEmpty);
      expect(trends.hasData, isFalse);
    });

    test('paired-but-waiting animal still has no fake comparison data after reload',
        () async {
      final storage = await createTestLocalStorage();
      final repo = await _reloadAnimalRepo(storage, accountKey: _testAccountA);

      final added = await repo.addAnimal(
        name: 'Waiting Reload',
        tagId: 'TAG-WAIT',
        breed: 'Gir',
        age: 2,
        gender: AnimalGender.male,
        weight: 310,
      );

      await repo.pairSensorToAnimal(
        added.id,
        sensorId: 'sensor-wait',
        sensorName: 'Collar Wait',
      );

      final reloaded = await _reloadAnimalRepo(storage, accountKey: _testAccountA);
      final restored = reloaded.findAnimalById(added.id)!;
      final readings = await reloaded.fetchRecentReadings(added.id);
      final trends = await reloaded.fetchTrends(added.id);

      expect(restored.isAwaitingSensorReadings, isTrue);
      expect(readings, isEmpty);
      expect(trends.hasData, isFalse);
    });

    test('clear local data resets user data and reloads seed data', () async {
      final storage = await createTestLocalStorage();
      final repo = await _reloadAnimalRepo(storage, accountKey: _testAccountA);
      final seedCount = AnimalRepository.seedAnimals.length;

      await repo.addAnimal(
        name: 'Temporary',
        tagId: 'TAG-TEMP',
        breed: 'Gir',
        age: 2,
        gender: AnimalGender.female,
        weight: 300,
      );
      await repo.updateAnimal(
        repo.animals.first.copyWith(name: 'Should Reset'),
      );

      final authRepo = AuthRepository(storage);
      await authRepo.registerAccount(
        const FarmerRegistration(
          fullName: 'Temp Farmer',
          phoneNumber: '9999999999',
          farmName: 'Temp Farm',
          village: 'V',
          district: 'D',
          state: 'S',
        ),
      );

      await storage.clearAllUserData();

      final reloadedAnimals = await _reloadAnimalRepo(storage, accountKey: _testAccountA);
      final reloadedAuth = AuthRepository(storage);

      expect(reloadedAnimals.animals.length, seedCount);
      expect(reloadedAnimals.animals.first.name, isNot('Should Reset'));
      expect(reloadedAuth.currentState.profile, isNull);
      expect(reloadedAuth.currentState.isAuthenticated, isFalse);
    });
  });
}
