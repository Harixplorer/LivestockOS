import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/qr/presentation/qr_scan_platform.dart';

void main() {
  test('web enables camera scanner', () {
    if (!kIsWeb) return;
    expect(isQrCameraPlatformSupported, isTrue);
  });

  test('desktop native platforms disable camera scanner', () {
    if (kIsWeb) return;
    switch (defaultTargetPlatform) {
      case TargetPlatform.windows:
      case TargetPlatform.linux:
      case TargetPlatform.macOS:
        expect(isQrCameraPlatformSupported, isFalse);
      case TargetPlatform.android:
      case TargetPlatform.iOS:
        expect(isQrCameraPlatformSupported, isTrue);
      case TargetPlatform.fuchsia:
        expect(isQrCameraPlatformSupported, isFalse);
    }
  });
}
