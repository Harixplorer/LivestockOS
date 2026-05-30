import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/core/persistence/local_storage_service.dart';
import 'package:livestock_os/features/alerts/data/alert_repository.dart';
import 'package:livestock_os/features/analytics/data/analytics_repository.dart';
import 'package:livestock_os/features/animals/data/animal_repository.dart';
import 'package:livestock_os/features/animals/data/models/animal.dart';
import 'package:livestock_os/features/auth/data/auth_repository.dart';
import 'package:livestock_os/features/auth/data/models/farmer_registration.dart';
import 'package:livestock_os/features/dashboard/data/dashboard_repository.dart';

import 'persistence_test_helpers.dart';

const _accountA = '9876543210';
const _accountB = '9999999999';

FarmerRegistration _profile({
  required String fullName,
  required String phone,
}) {
  return FarmerRegistration(
    fullName: fullName,
    phoneNumber: phone,
    farmName: 'Farm',
    village: 'Village',
    district: 'District',
    state: 'State',
  );
}

Future<void> _login(AuthRepository auth, String phone) async {
  await auth.completeOnboarding();
  await auth.requestOtp(phone);
  await auth.verifyOtp(AuthRepository.mockValidOtp);
}

AnimalRepository _animalRepo(LocalStorageService storage, String accountKey) {
  return AnimalRepository(storage, accountKey: accountKey);
}

AlertRepository _alertRepo(
  LocalStorageService storage,
  AnimalRepository animals,
  String accountKey,
) {
  return AlertRepository(animals, storage, accountKey: accountKey);
}

void main() {
  group('account-scoped persistence', () {
    test('Account A added animal is not visible to Account B', () async {
      final storage = await createTestLocalStorage();
      final auth = AuthRepository(storage);

      await auth.registerAccount(_profile(fullName: 'Account A', phone: _accountA));
      final repoA = _animalRepo(storage, _accountA);
      await repoA.addAnimal(
        name: 'Account A Cow',
        tagId: 'TAG-A',
        breed: 'Gir',
        age: 2,
        gender: AnimalGender.female,
        weight: 300,
      );

      await auth.signOut();
      await _login(auth, _accountB);

      final repoB = _animalRepo(storage, _accountB);
      expect(repoB.animals.any((a) => a.tagId == 'TAG-A'), isFalse);
      expect(repoB.animals.length, AnimalRepository.seedAnimals.length);
    });

    test('Account A added animal reappears when Account A logs back in', () async {
      final storage = await createTestLocalStorage();
      final auth = AuthRepository(storage);

      await auth.registerAccount(_profile(fullName: 'Account A', phone: _accountA));
      final repoA = _animalRepo(storage, _accountA);
      await repoA.addAnimal(
        name: 'Return Cow',
        tagId: 'TAG-RETURN',
        breed: 'Gir',
        age: 3,
        gender: AnimalGender.male,
        weight: 400,
      );

      await auth.signOut();
      await _login(auth, _accountB);
      await auth.signOut();
      await _login(auth, _accountA);

      final restored = _animalRepo(storage, _accountA);
      expect(restored.animals.any((a) => a.tagId == 'TAG-RETURN'), isTrue);
    });

    test('edited seed animal override does not leak to Account B', () async {
      final storage = await createTestLocalStorage();
      final auth = AuthRepository(storage);

      await auth.registerAccount(_profile(fullName: 'Account A', phone: _accountA));
      final repoA = _animalRepo(storage, _accountA);
      final seed = repoA.animals.first;
      await repoA.updateAnimal(seed.copyWith(name: 'A Only Edit'));

      await auth.signOut();
      await _login(auth, _accountB);

      final repoB = _animalRepo(storage, _accountB);
      expect(repoB.findAnimalById(seed.id)?.name, isNot('A Only Edit'));
    });

    test('pairing sensor in Account A does not appear in Account B', () async {
      final storage = await createTestLocalStorage();
      final auth = AuthRepository(storage);

      await auth.registerAccount(_profile(fullName: 'Account A', phone: _accountA));
      final repoA = _animalRepo(storage, _accountA);
      final added = await repoA.addAnimal(
        name: 'Pair Cow',
        tagId: 'TAG-PAIR-A',
        breed: 'Gir',
        age: 2,
        gender: AnimalGender.female,
        weight: 320,
      );
      await repoA.pairSensorToAnimal(
        added.id,
        sensorId: 'sensor-a',
        sensorName: 'Collar A',
      );

      await auth.signOut();
      await _login(auth, _accountB);

      final repoB = _animalRepo(storage, _accountB);
      expect(repoB.findAnimalByTagId('TAG-PAIR-A'), isNull);
    });

    test('alert resolved in Account A does not resolve in Account B', () async {
      final storage = await createTestLocalStorage();
      final auth = AuthRepository(storage);

      await auth.registerAccount(_profile(fullName: 'Account A', phone: _accountA));
      final animalsA = _animalRepo(storage, _accountA);
      final alertsA = _alertRepo(storage, animalsA, _accountA);

      final target =
          (await alertsA.fetchAlerts()).firstWhere((a) => !a.isResolved);
      await alertsA.setResolved(id: target.id, isResolved: true);

      await auth.signOut();
      await _login(auth, _accountB);

      final animalsB = _animalRepo(storage, _accountB);
      final alertsB = _alertRepo(storage, animalsB, _accountB);
      final alertForB = await alertsB.fetchAlertById(target.id);

      expect(alertForB?.isResolved, isFalse);
    });

    test('dashboard counts differ per account', () async {
      final storage = await createTestLocalStorage();
      final auth = AuthRepository(storage);

      await auth.registerAccount(_profile(fullName: 'Account A', phone: _accountA));
      final repoA = _animalRepo(storage, _accountA);
      await repoA.addAnimal(
        name: 'Dash Cow',
        tagId: 'TAG-DASH',
        breed: 'Gir',
        age: 2,
        gender: AnimalGender.female,
        weight: 280,
      );
      final dashA = DashboardRepository(repoA);
      final statsA = (await dashA.fetchDashboard()).summary;

      await auth.signOut();
      await _login(auth, _accountB);

      final repoB = _animalRepo(storage, _accountB);
      final dashB = DashboardRepository(repoB);
      final statsB = (await dashB.fetchDashboard()).summary;

      expect(statsA.totalAnimals, statsB.totalAnimals + 1);
      expect(statsA.notMonitoredCount, statsB.notMonitoredCount + 1);
    });

    test('analytics uses only current account animals', () async {
      final storage = await createTestLocalStorage();
      final auth = AuthRepository(storage);

      await auth.registerAccount(_profile(fullName: 'Account A', phone: _accountA));
      final repoA = _animalRepo(storage, _accountA);
      await repoA.addAnimal(
        name: 'Analytics Cow',
        tagId: 'TAG-AN',
        breed: 'Gir',
        age: 2,
        gender: AnimalGender.female,
        weight: 290,
      );
      final analyticsA = AnalyticsRepository(
        repoA,
        _alertRepo(storage, repoA, _accountA),
      );

      await auth.signOut();
      await _login(auth, _accountB);

      final repoB = _animalRepo(storage, _accountB);
      final analyticsB = AnalyticsRepository(
        repoB,
        _alertRepo(storage, repoB, _accountB),
      );

      final summaryA = await analyticsA.fetchSummary();
      final summaryB = await analyticsB.fetchSummary();

      expect(summaryA.totalAnimals, summaryB.totalAnimals + 1);
    });

    test('unknown OTP-only account starts with seed data only', () async {
      final storage = await createTestLocalStorage();
      final auth = AuthRepository(storage);

      await _login(auth, _accountB);

      final repo = _animalRepo(storage, _accountB);
      expect(repo.animals.length, AnimalRepository.seedAnimals.length);
    });

    test('clear local data removes all account-scoped animal data', () async {
      final storage = await createTestLocalStorage();
      final auth = AuthRepository(storage);

      await auth.registerAccount(_profile(fullName: 'Account A', phone: _accountA));
      final repoA = _animalRepo(storage, _accountA);
      await repoA.addAnimal(
        name: 'Clear Cow',
        tagId: 'TAG-CLR',
        breed: 'Gir',
        age: 2,
        gender: AnimalGender.female,
        weight: 300,
      );

      await storage.clearAllUserData();

      final restored = _animalRepo(storage, _accountA);
      expect(restored.animals.length, AnimalRepository.seedAnimals.length);
      expect(restored.animals.any((a) => a.tagId == 'TAG-CLR'), isFalse);
    });
  });
}
