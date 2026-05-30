import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/alerts/data/alert_repository.dart';
import 'package:livestock_os/features/alerts/data/models/alerts_list_query.dart';
import 'package:livestock_os/features/alerts/data/models/farm_alert.dart';
import 'package:livestock_os/features/animals/data/animal_repository.dart';

void main() {
  AlertRepository buildRepo() =>
      AlertRepository.inMemory(AnimalRepository.inMemory());

  test('mock alerts repository seeds at least 12 alerts', () async {
    final alerts = await buildRepo().fetchAlerts();
    expect(alerts.length, greaterThanOrEqualTo(12));
  });

  test('filter by critical returns only critical active alerts', () async {
    final alerts = await buildRepo().fetchAlerts(
      query: const AlertsListQuery(severityFilter: AlertSeverityFilter.critical),
    );
    expect(alerts.isNotEmpty, isTrue);
    expect(
      alerts.every((a) => a.severity == AlertSeverity.critical),
      isTrue,
    );
  });

  test('filter by resolved returns only resolved alerts', () async {
    final alerts = await buildRepo().fetchAlerts(
      query: const AlertsListQuery(severityFilter: AlertSeverityFilter.resolved),
    );
    expect(alerts.isNotEmpty, isTrue);
    expect(alerts.every((a) => a.isResolved), isTrue);
  });

  test('search matches animal name tag and type text', () async {
    final repo = buildRepo();
    final byAnimal = await repo.fetchAlerts(
      query: const AlertsListQuery(search: 'Meera'),
    );
    final byTag = await repo.fetchAlerts(
      query: const AlertsListQuery(search: 'TAG-1008'),
    );
    final byType = await repo.fetchAlerts(
      query: const AlertsListQuery(search: 'sensor offline'),
    );

    expect(byAnimal.isNotEmpty, isTrue);
    expect(byTag.isNotEmpty, isTrue);
    expect(byType.isNotEmpty, isTrue);
  });

  test('sort by animal name orders alphabetically', () async {
    final alerts = await buildRepo().fetchAlerts(
      query: const AlertsListQuery(sort: AlertSortOption.animalName),
    );
    for (var i = 0; i < alerts.length - 1; i++) {
      expect(
        alerts[i].animalName.compareTo(alerts[i + 1].animalName) <= 0,
        isTrue,
      );
    }
  });

  test('resolve and reopen alert mutates status', () async {
    final repo = buildRepo();
    final first = (await repo.fetchAlerts()).firstWhere((a) => !a.isResolved);

    final resolved = await repo.setResolved(id: first.id, isResolved: true);
    expect(resolved.isResolved, isTrue);

    final reopened = await repo.setResolved(id: first.id, isResolved: false);
    expect(reopened.isResolved, isFalse);
  });
}
