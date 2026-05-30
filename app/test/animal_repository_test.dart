import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/animals/data/animal_repository.dart';
import 'package:livestock_os/features/animals/data/models/animal.dart';
import 'package:livestock_os/features/animals/data/models/animal_list_query.dart';

void main() {
  test('mock repository seeds at least 12 animals', () {
    final repo = AnimalRepository.inMemory();
    expect(repo.animals.length, greaterThanOrEqualTo(12));
  });

  test('search filters by name tag or breed', () async {
    final repo = AnimalRepository.inMemory();
    final results = await repo.fetchAnimals(
      query: const AnimalListQuery(search: 'gauri'),
    );

    expect(results.length, 1);
    expect(results.first.name, 'Gauri');
  });

  test('status filter returns only matching animals', () async {
    final repo = AnimalRepository.inMemory();
    final critical = await repo.fetchAnimals(
      query: const AnimalListQuery(
        statusFilter: AnimalStatusFilter.critical,
      ),
    );

    expect(critical.isNotEmpty, isTrue);
    expect(
      critical.every((a) => a.status == AnimalHealthStatus.critical),
      isTrue,
    );
  });

  test('pending filter returns not monitored animals', () async {
    final repo = AnimalRepository.inMemory();
    final added = await repo.addAnimal(
      name: 'Pending Cow',
      tagId: 'TAG-PEND',
      breed: 'Gir',
      age: 2,
      gender: AnimalGender.female,
      weight: 300,
    );

    final pending = await repo.fetchAnimals(
      query: const AnimalListQuery(
        statusFilter: AnimalStatusFilter.pending,
      ),
    );

    expect(pending.any((a) => a.id == added.id), isTrue);
    expect(added.status, AnimalHealthStatus.notMonitored);
  });

  test('add animal has no fake sensor health data', () async {
    final repo = AnimalRepository.inMemory();
    final before = repo.animals.length;

    final added = await repo.addAnimal(
      name: 'Test Cow',
      tagId: 'TAG-9999',
      breed: 'Gir',
      age: 3,
      gender: AnimalGender.female,
      weight: 350,
    );

    expect(repo.animals.length, before + 1);
    expect(added.name, 'Test Cow');
    expect(added.healthScore, isNull);
    expect(added.temperature, isNull);
    expect(added.activityLevel, isNull);
    expect(added.rumination, isNull);
    expect(added.lastUpdated, isNull);
    expect(added.status, AnimalHealthStatus.notMonitored);
    expect(added.sensorStatus, AnimalSensorStatus.notPaired);
    expect(added.hasHealthData, isFalse);
  });

  test('add animal does not increase healthy herd count', () async {
    final repo = AnimalRepository.inMemory();
    final before = repo.computeHerdStats();

    await repo.addAnimal(
      name: 'New Pending',
      tagId: 'TAG-NEW',
      breed: 'Gir',
      age: 1,
      gender: AnimalGender.male,
      weight: 200,
    );

    final after = repo.computeHerdStats();
    expect(after.total, before.total + 1);
    expect(after.notMonitoredCount, before.notMonitoredCount + 1);
    expect(after.healthyCount, before.healthyCount);
  });

  test('update animal changes stored record', () async {
    final repo = AnimalRepository.inMemory();
    final original = repo.animals.first;

    final updated = await repo.updateAnimal(
      original.copyWith(name: 'Updated Name'),
    );

    expect(updated.name, 'Updated Name');
    expect(repo.animals.firstWhere((a) => a.id == original.id).name,
        'Updated Name');
  });

  test('sort by gender orders female before male then by name', () async {
    final repo = AnimalRepository.inMemory();
    final results = await repo.fetchAnimals(
      query: const AnimalListQuery(sort: AnimalSortOption.gender),
    );

    expect(results.length, greaterThanOrEqualTo(2));

    for (var i = 0; i < results.length - 1; i++) {
      final current = results[i];
      final next = results[i + 1];
      final currentOrder =
          current.gender == AnimalGender.female ? 0 : 1;
      final nextOrder = next.gender == AnimalGender.female ? 0 : 1;

      expect(
        currentOrder <= nextOrder,
        isTrue,
        reason: '${current.name} should not come after ${next.name} by gender',
      );
      if (currentOrder == nextOrder) {
        expect(
          current.name.compareTo(next.name) <= 0,
          isTrue,
          reason: 'Same gender group should be sorted by name',
        );
      }
    }

    final females = results.where((a) => a.gender == AnimalGender.female);
    final males = results.where((a) => a.gender == AnimalGender.male);
    expect(females.length + males.length, results.length);
    if (females.isNotEmpty && males.isNotEmpty) {
      final lastFemaleIndex = results.lastIndexWhere(
        (a) => a.gender == AnimalGender.female,
      );
      final firstMaleIndex = results.indexWhere(
        (a) => a.gender == AnimalGender.male,
      );
      expect(lastFemaleIndex < firstMaleIndex, isTrue);
    }
  });

  test('sort by gender works with search filter', () async {
    final repo = AnimalRepository.inMemory();
    final results = await repo.fetchAnimals(
      query: const AnimalListQuery(
        search: 'gir',
        sort: AnimalSortOption.gender,
      ),
    );

    expect(results.isNotEmpty, isTrue);
    expect(results.every((a) => a.breed.toLowerCase().contains('gir')), isTrue);
    for (var i = 0; i < results.length - 1; i++) {
      final order = _genderOrder(results[i].gender)
          .compareTo(_genderOrder(results[i + 1].gender));
      expect(order <= 0, isTrue);
      if (order == 0) {
        expect(
          results[i].name.compareTo(results[i + 1].name) <= 0,
          isTrue,
        );
      }
    }
  });

  test('update pending animal does not set last synced time', () async {
    final repo = AnimalRepository.inMemory();
    final added = await repo.addAnimal(
      name: 'Pending',
      tagId: 'TAG-X',
      breed: 'Gir',
      age: 2,
      gender: AnimalGender.female,
      weight: 280,
    );

    final updated = await repo.updateAnimal(
      added.copyWith(name: 'Pending Renamed'),
    );

    expect(updated.lastUpdated, isNull);
    expect(updated.hasHealthData, isFalse);
  });
}

int _genderOrder(AnimalGender gender) {
  return gender == AnimalGender.female ? 0 : 1;
}
