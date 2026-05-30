import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/alerts/data/alert_repository.dart';
import 'package:livestock_os/features/analytics/data/analytics_repository.dart';
import 'package:livestock_os/features/analytics/data/models/animal_comparison_data.dart';
import 'package:livestock_os/features/animals/data/animal_repository.dart';
import 'package:livestock_os/features/animals/data/models/animal.dart';
import 'package:livestock_os/features/ble/data/mock_ble_data.dart';

void main() {
  late AnimalRepository animalRepo;
  late AlertRepository alertRepo;
  late AnalyticsRepository analyticsRepo;

  setUp(() {
    animalRepo = AnimalRepository.inMemory();
    alertRepo = AlertRepository.inMemory(animalRepo);
    analyticsRepo = AnalyticsRepository(animalRepo, alertRepo);
  });

  test('analytics summary reflects herd stats and active alerts', () async {
    final herd = animalRepo.computeHerdStats();
    final summary = await analyticsRepo.fetchSummary();
    final alerts = await alertRepo.fetchAlerts();
    final activeAlerts = alerts.where((a) => !a.isResolved).length;

    expect(summary.totalAnimals, herd.total);
    expect(summary.averageHealthScore, herd.averageHealthScore);
    expect(summary.sensorsOnline, herd.sensorsOnline);
    expect(summary.activeAlerts, activeAlerts);
    expect(
      summary.animalsNeedingAttention,
      herd.warningsCount + herd.criticalCount,
    );
  });

  test('health distribution includes pending not monitored animals', () async {
    await animalRepo.addAnimal(
      name: 'Pending Analytics Cow',
      tagId: 'TAG-AN-PEND',
      breed: 'Gir',
      age: 2,
      gender: AnimalGender.female,
      weight: 300,
    );

    final distribution = await analyticsRepo.fetchHerdHealthDistribution();
    final herd = animalRepo.computeHerdStats();

    expect(distribution.total, herd.total);
    expect(distribution.pending, herd.notMonitoredCount);
    expect(
      distribution.healthy +
          distribution.warning +
          distribution.critical +
          distribution.pending,
      distribution.total,
    );
  });

  test('sensor coverage updates after pair and unpair', () async {
    final before = await analyticsRepo.fetchSensorCoverage();
    final added = await animalRepo.addAnimal(
      name: 'Sensor Analytics Cow',
      tagId: 'TAG-AN-SENS',
      breed: 'Gir',
      age: 2,
      gender: AnimalGender.female,
      weight: 300,
    );

    final afterAdd = await analyticsRepo.fetchSensorCoverage();
    expect(afterAdd.notPaired, before.notPaired + 1);
    expect(afterAdd.totalAnimals, before.totalAnimals + 1);

    await animalRepo.pairSensorToAnimal(
      added.id,
      sensorId: MockBleData.demoSensor.id,
      sensorName: MockBleData.demoSensor.name,
    );
    final afterPair = await analyticsRepo.fetchSensorCoverage();
    expect(afterPair.pairedSensors, before.pairedSensors + 1);
    expect(afterPair.onlineSensors, before.onlineSensors + 1);

    await animalRepo.unpairSensorFromAnimal(added.id);
    final afterUnpair = await analyticsRepo.fetchSensorCoverage();
    expect(afterUnpair.pairedSensors, before.pairedSensors);
    expect(afterUnpair.notPaired, afterAdd.notPaired);
  });

  test('attention animals exclude healthy animals', () async {
    final insights = await analyticsRepo.fetchAttentionAnimals(limit: 20);
    expect(
      insights.every(
        (i) =>
            i.severity == AnimalHealthStatus.warning ||
            i.severity == AnimalHealthStatus.critical,
      ),
      isTrue,
    );
  });

  test('newly added animal without sensor has no comparison data', () async {
    final pending = await animalRepo.addAnimal(
      name: 'Compare Pending',
      tagId: 'TAG-CMP-PEND',
      breed: 'Gir',
      age: 2,
      gender: AnimalGender.female,
      weight: 300,
    );

    final comparison = await analyticsRepo.fetchAnimalComparison([pending.id]);
    final data = comparison.single;

    expect(data.hasMonitoringData, isFalse);
    expect(data.hasPairedSensor, isFalse);
    expect(data.noDataReason, AnimalComparisonNoDataReason.notPaired);
    expect(data.healthScore, isNull);
    expect(data.temperature, isNull);
    expect(data.activityLevel, isNull);
    expect(data.rumination, isNull);
    expect(data.trendPoints, isEmpty);
  });

  test('pending not paired animal does not produce trend points', () async {
    final pending = await animalRepo.addAnimal(
      name: 'No Trends',
      tagId: 'TAG-NO-TREND',
      breed: 'Gir',
      age: 2,
      gender: AnimalGender.female,
      weight: 300,
    );

    final comparison = await analyticsRepo.fetchAnimalComparison([pending.id]);
    expect(comparison.single.trendPoints, isEmpty);
    expect(comparison.single.hasMonitoringData, isFalse);
  });

  test('paired but no readings animal has no fake comparison data', () async {
    final added = await animalRepo.addAnimal(
      name: 'Pair Compare',
      tagId: 'TAG-CMP-PAIR',
      breed: 'Gir',
      age: 2,
      gender: AnimalGender.female,
      weight: 300,
    );
    await animalRepo.pairSensorToAnimal(
      added.id,
      sensorId: 'LOS-1001',
      sensorName: 'LivestockOS_Sensor',
    );

    final comparison =
        await analyticsRepo.fetchAnimalComparison([added.id]);
    final data = comparison.single;

    expect(data.hasMonitoringData, isFalse);
    expect(data.hasPairedSensor, isTrue);
    expect(data.noDataReason, AnimalComparisonNoDataReason.awaitingReadings);
    expect(data.healthScore, isNull);
    expect(data.temperature, isNull);
    expect(data.activityLevel, isNull);
    expect(data.rumination, isNull);
    expect(data.trendPoints, isEmpty);
  });

  test('seed monitored animal still produces comparison data', () async {
    final monitored = animalRepo.animals.firstWhere((a) => a.hasHealthData);

    final comparison =
        await analyticsRepo.fetchAnimalComparison([monitored.id]);
    final data = comparison.single;

    expect(data.hasMonitoringData, isTrue);
    expect(data.healthScore, isNotNull);
    expect(data.trendPoints, isNotEmpty);
  });

  test('mixed comparison shows data only for monitored animals', () async {
    final pending = await animalRepo.addAnimal(
      name: 'Mixed Pending',
      tagId: 'TAG-MIX-PEND',
      breed: 'Gir',
      age: 2,
      gender: AnimalGender.female,
      weight: 300,
    );
    final monitored = animalRepo.animals.firstWhere((a) => a.hasHealthData);

    final comparison = await analyticsRepo.fetchAnimalComparison(
      [pending.id, monitored.id],
    );

    final pendingData =
        comparison.firstWhere((c) => c.animalId == pending.id);
    final monitoredData =
        comparison.firstWhere((c) => c.animalId == monitored.id);

    expect(pendingData.hasMonitoringData, isFalse);
    expect(pendingData.healthScore, isNull);
    expect(pendingData.trendPoints, isEmpty);
    expect(monitoredData.hasMonitoringData, isTrue);
    expect(monitoredData.healthScore, isNotNull);
    expect(monitoredData.trendPoints, isNotEmpty);
  });

  test('alert trend derives from alerts repository', () async {
    final alerts = await alertRepo.fetchAlerts();
    final trend = await analyticsRepo.fetchAlertTrend();
    final totalFromAlerts = alerts.length;

    expect(trend.length, 7);
    expect(
      trend.fold<int>(0, (sum, p) => sum + p.total),
      lessThanOrEqualTo(totalFromAlerts),
    );
  });
}
