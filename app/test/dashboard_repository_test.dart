import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/animals/data/animal_repository.dart';
import 'package:livestock_os/features/animals/data/models/animal.dart';
import 'package:livestock_os/features/dashboard/data/dashboard_repository.dart';

void main() {
  test('mock dashboard reflects live herd counts from animals', () async {
    final animalRepo = AnimalRepository.inMemory();
    final herd = animalRepo.computeHerdStats();
    final data =
        await DashboardRepository(animalRepo).fetchDashboard();

    expect(data.summary.totalAnimals, herd.total);
    expect(data.summary.healthyCount, herd.healthyCount);
    expect(data.summary.warningsCount, herd.warningsCount);
    expect(data.summary.criticalCount, herd.criticalCount);
    expect(data.summary.notMonitoredCount, herd.notMonitoredCount);
    expect(data.summary.sensorsOnline, herd.sensorsOnline);
    expect(data.summary.sensorsTotal, herd.sensorsTotal);
    expect(data.metrics.length, 6);
    expect(data.quickActions.length, 4);
    expect(data.weeklyTrend.length, 7);
    expect(data.animalsNeedingAttention.isNotEmpty, isTrue);
    expect(data.recentActivity.length, 4);
  });

  test('newly added animal increases total but not healthy count', () async {
    final animalRepo = AnimalRepository.inMemory();
    final before = animalRepo.computeHerdStats();

    await animalRepo.addAnimal(
      name: 'Dashboard Test',
      tagId: 'TAG-DASH',
      breed: 'Gir',
      age: 2,
      gender: AnimalGender.female,
      weight: 300,
    );

    final after = animalRepo.computeHerdStats();
    final data =
        await DashboardRepository(animalRepo).fetchDashboard();

    expect(after.total, before.total + 1);
    expect(after.healthyCount, before.healthyCount);
    expect(data.summary.notMonitoredCount, before.notMonitoredCount + 1);
    expect(after.sensorsOnline, before.sensorsOnline);
    expect(after.sensorsTotal, before.sensorsTotal + 1);
    expect(data.summary.sensorsOnline, after.sensorsOnline);
    expect(data.summary.sensorsTotal, after.sensorsTotal);
  });

  test('seed herd has expected sensors online ratio', () {
    final herd = AnimalRepository.inMemory().computeHerdStats();
    expect(herd.total, 14);
    expect(herd.sensorsOnline, 11);
    expect(herd.sensorsTotal, 14);
  });
}
