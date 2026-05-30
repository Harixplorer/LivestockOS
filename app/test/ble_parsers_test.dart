import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/ble/data/ble_parsers.dart';

void main() {
  test('parseTemperature reads float32 little-endian Celsius', () {
    final bytes = ByteData(4)..setFloat32(0, 38.5, Endian.little);
    final value = bytes.buffer.asUint8List().toList();
    expect(BleParsers.parseTemperature(value), closeTo(38.5, 0.001));
  });

  test('parseActivity reads int32 little-endian percent', () {
    final bytes = ByteData(4)..setInt32(0, 72, Endian.little);
    final value = bytes.buffer.asUint8List().toList();
    expect(BleParsers.parseActivity(value), 72);
  });

  test('parseBehaviour decodes utf8 string', () {
    final value = utf8.encode('Grazing');
    expect(BleParsers.parseBehaviour(value), 'Grazing');
  });

  test('parseRumination reads int32 little-endian minutes per hour', () {
    final bytes = ByteData(4)..setInt32(0, 6, Endian.little);
    final value = bytes.buffer.asUint8List().toList();
    expect(BleParsers.parseRumination(value), 6);
  });

  test('parseActivity clamps to 0-100', () {
    final bytes = ByteData(4)..setInt32(0, 150, Endian.little);
    final value = bytes.buffer.asUint8List().toList();
    expect(BleParsers.parseActivity(value), 100);
  });
}
