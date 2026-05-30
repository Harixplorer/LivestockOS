import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/animals/data/animal_repository.dart';
import 'package:livestock_os/features/animals/data/models/animal.dart';
import 'package:livestock_os/features/animals/data/models/health_score_breakdown.dart';
import 'package:livestock_os/features/animals/data/models/reading_history_period.dart';

void main() {
  test('monitored seed animal has health summary and readings', () async {
    final repo = AnimalRepository.inMemory();
    const id = 'animal-001';

    final summary = await repo.fetchHealthSummary(id);
    final readings = await repo.fetchRecentReadings(id);
    final breakdown = await repo.fetchHealthBreakdown(id);
    final trends = await repo.fetchTrends(id);

    expect(summary.hasData, isTrue);
    expect(summary.healthScore, isNotNull);
    expect(readings.length, greaterThan(0));
    expect(breakdown.isPending, isFalse);
    expect(breakdown.components.length, 5);
    expect(trends.hasData, isTrue);
    expect(trends.points.length, 24);
  });

  test('newly added animal has no mock readings', () async {
    final repo = AnimalRepository.inMemory();
    final added = await repo.addAnimal(
      name: 'No Sensor',
      tagId: 'TAG-NS',
      breed: 'Gir',
      age: 2,
      gender: AnimalGender.female,
      weight: 300,
    );

    final summary = await repo.fetchHealthSummary(added.id);
    final readings = await repo.fetchRecentReadings(added.id);
    final breakdown = await repo.fetchHealthBreakdown(added.id);
    final trends = await repo.fetchTrends(added.id);

    expect(summary.isPending, isTrue);
    expect(readings, isEmpty);
    expect(breakdown.category, HealthScoreCategory.pending);
    expect(trends.hasData, isFalse);
  });

  test('critical animal breakdown reflects elevated risk', () async {
    final repo = AnimalRepository.inMemory();
    final breakdown = await repo.fetchHealthBreakdown('animal-005');

    expect(breakdown.category, HealthScoreCategory.critical);
    expect(breakdown.overallScore, lessThan(70));
  });

  test('reading history period filter returns subset', () async {
    final repo = AnimalRepository.inMemory();
    const id = 'animal-001';

    final today = await repo.fetchReadingsForPeriod(
      id,
      ReadingHistoryPeriod.today,
    );
    final week = await repo.fetchReadingsForPeriod(
      id,
      ReadingHistoryPeriod.last7Days,
    );

    expect(week.isNotEmpty, isTrue);
    expect(today.length, lessThanOrEqualTo(week.length));
  });
}
