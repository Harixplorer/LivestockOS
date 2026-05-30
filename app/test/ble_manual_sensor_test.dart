import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/ble/data/ble_repository.dart';
import 'package:livestock_os/features/ble/data/models/ble_scan_state.dart';
import 'package:livestock_os/features/ble/data/mock_ble_data.dart';
import 'package:livestock_os/features/ble/data/models/ble_manual_sensor_lookup.dart';

void main() {
  late BleRepository repo;

  setUp(() {
    repo = BleRepository(forceMock: true);
  });

  tearDown(() async {
    await repo.dispose();
  });

  test('rejects unknown sensor ID LOS-1234', () {
    final lookup = repo.lookupManualSensor('LOS-1234');
    expect(lookup.kind, BleManualSensorLookupKind.notFound);
  });

  test('rejects invalid format', () {
    final lookup = repo.lookupManualSensor('BAD-ID');
    expect(lookup.kind, BleManualSensorLookupKind.invalidFormat);
  });

  test('accepts known available mock sensor LOS-1001', () {
    final lookup = repo.lookupManualSensor('LOS-1001');
    expect(lookup.isFound, isTrue);
    expect(lookup.device?.id, 'LOS-1001');
    expect(lookup.device?.isSelectable, isTrue);
  });

  test('accepts known available mock sensor LOS-1002', () {
    final lookup = repo.lookupManualSensor('los-1002');
    expect(lookup.isFound, isTrue);
    expect(lookup.device?.id, 'LOS-1002');
  });

  test('rejects low battery mock sensor LOS-0998', () {
    final lookup = repo.lookupManualSensor('LOS-0998');
    expect(lookup.kind, BleManualSensorLookupKind.unavailable);
  });

  test('rejects already paired mock sensor LOS-0981', () {
    final lookup = repo.lookupManualSensor('LOS-0981');
    expect(lookup.kind, BleManualSensorLookupKind.unavailable);
  });

  test('MockBleData does not synthesize unknown IDs', () {
    expect(MockBleData.findBySensorId('LOS-1234'), isNull);
    expect(MockBleData.findBySensorId('LOS-1001'), isNotNull);
  });

  test('registers devices from scan for manual lookup', () async {
    final completer = Completer<void>();
    late final StreamSubscription<BleScanState> sub;
    sub = repo.scanSensors().listen((state) {
      if (state.devices.isNotEmpty) {
        final lookup = repo.lookupManualSensor(state.devices.first.id);
        expect(lookup.isFound, isTrue);
        sub.cancel();
        if (!completer.isCompleted) completer.complete();
      }
    });
    await completer.future.timeout(const Duration(seconds: 5));
  });
}
