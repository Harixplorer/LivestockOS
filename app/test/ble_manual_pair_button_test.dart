import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/ble/data/ble_repository.dart';
import 'package:livestock_os/features/ble/data/models/ble_manual_sensor_lookup.dart';
import 'package:livestock_os/features/ble/presentation/utils/ble_manual_pair_input_state.dart';

void main() {
  late BleRepository repo;

  setUp(() {
    repo = BleRepository(forceMock: true);
  });

  tearDown(() async {
    await repo.dispose();
  });

  BleManualPairInputState evaluate(String text) {
    return BleManualPairInputState.evaluate(
      sensorIdText: text,
      lookup: repo.lookupManualSensor(text),
    );
  }

  test('empty manual ID disables button', () {
    final state = evaluate('');
    expect(state.canPair, isFalse);
    expect(state.device, isNull);
  });

  test('known available ID enables button', () {
    final state = evaluate('LOS-1001');
    expect(state.canPair, isTrue);
    expect(state.device?.id, 'LOS-1001');
    expect(state.errorMessage, isNull);
  });

  test('known available ID sets selected sensor device', () {
    final state = evaluate('LOS-1002');
    expect(state.device?.isSelectable, isTrue);
    expect(state.canPair, isTrue);
  });

  test('unknown ID rejects and does not enable pairing', () {
    final state = evaluate('LOS-1234');
    expect(state.canPair, isFalse);
    expect(state.errorMessage, isNotNull);
    expect(state.device, isNull);
  });

  test('already paired ID blocks pairing', () {
    final lookup = repo.lookupManualSensor('LOS-0981');
    expect(lookup.kind, BleManualSensorLookupKind.unavailable);
    final state = BleManualPairInputState.evaluate(
      sensorIdText: 'LOS-0981',
      lookup: lookup,
    );
    expect(state.canPair, isFalse);
    expect(state.errorMessage, isNotNull);
  });

  test('invalid format disables pairing', () {
    final state = evaluate('BAD-ID');
    expect(state.canPair, isFalse);
    expect(state.errorMessage, isNotNull);
  });
}
