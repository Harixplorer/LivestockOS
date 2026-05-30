import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/ble/providers/ble_providers.dart';

void main() {
  test('setAnimalId stores id and skips redundant writes', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    final selection = container.read(bleSelectionProvider);
    selection.setAnimalId('animal-001');
    selection.setAnimalId('animal-001');

    expect(container.read(blePairingAnimalIdProvider), 'animal-001');
  });

  test('setAnimalId ignores null and empty values', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    container.read(bleSelectionProvider).setAnimalId('animal-002');
    container.read(bleSelectionProvider).setAnimalId(null);
    container.read(bleSelectionProvider).setAnimalId('');

    expect(container.read(blePairingAnimalIdProvider), 'animal-002');
  });

  test('pair sensor flow sets animalId before route would be read', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    const animalId = 'animal-003';
    container.read(bleSelectionProvider).setAnimalId(animalId);

    expect(container.read(blePairingAnimalIdProvider), animalId);
    expect(container.read(bleSelectionProvider).animalId, animalId);
  });

  test('dashboard BLE entry works without animalId', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    expect(container.read(blePairingAnimalIdProvider), isNull);
    container.read(bleSelectionProvider).setAnimalId(null);
    expect(container.read(blePairingAnimalIdProvider), isNull);
  });

  test('clearSession removes animal and sensor selection', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    final selection = container.read(bleSelectionProvider);
    selection.setAnimalId('animal-001');
    selection.selectSensor(
      container.read(bleRepositoryProvider).lookupManualSensor('LOS-1001').device!,
    );

    expect(container.read(blePairingAnimalIdProvider), 'animal-001');
    expect(container.read(bleSelectedDeviceProvider), isNotNull);

    selection.clearSession();

    expect(container.read(blePairingAnimalIdProvider), isNull);
    expect(container.read(bleSelectedDeviceProvider), isNull);
  });
}
