import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/core/router/app_routes.dart';
import 'package:livestock_os/core/router/auth_redirect.dart';
import 'package:livestock_os/features/auth/data/models/auth_state.dart';
import 'package:livestock_os/features/auth/domain/auth_status.dart';

void main() {
  group('route paths', () {
    const authenticated = AuthState(
      status: AuthStatus.authenticated,
      onboardingComplete: true,
    );

    const loggedOut = AuthState(
      status: AuthStatus.unauthenticated,
      onboardingComplete: true,
    );

    final protectedDemoPaths = [
      AppRoutes.dashboard,
      AppRoutes.animals,
      AppRoutes.animalsAdd,
      AppRoutes.animalDetail('animal-001'),
      AppRoutes.animalEdit('animal-001'),
      AppRoutes.animalHealthScore('animal-001'),
      AppRoutes.animalHistory('animal-001'),
      AppRoutes.animalTrends('animal-001'),
      AppRoutes.animalQr('animal-001'),
      AppRoutes.scanQr,
      AppRoutes.alerts,
      AppRoutes.alertDetail('alert-001'),
      AppRoutes.ble,
      AppRoutes.bleScanPath,
      AppRoutes.bleManualPath,
      AppRoutes.bleConfirmPath,
      AppRoutes.bleSuccessPath,
      AppRoutes.bleMonitorPath,
      AppRoutes.bleSelectAnimalPath,
      AppRoutes.analytics,
      AppRoutes.analyticsTrends,
      AppRoutes.analyticsComparison,
      AppRoutes.analyticsSensors,
      AppRoutes.profile,
      AppRoutes.profileEdit,
      AppRoutes.settings,
      AppRoutes.settingsNotifications,
      AppRoutes.settingsFarm,
      AppRoutes.settingsUnits,
      AppRoutes.settingsLanguage,
      AppRoutes.settingsDataSync,
      AppRoutes.settingsAbout,
    ];

    test('auth flow routes are public', () {
      for (final route in AppRoutes.authFlowRoutes) {
        expect(AppRoutes.isAuthFlow(route), isTrue);
        expect(
          AuthRedirect.resolve(auth: loggedOut, location: route),
          isNull,
          reason: '$route should be reachable when logged out',
        );
      }
    });

    test('protected demo routes require authentication', () {
      for (final path in protectedDemoPaths) {
        expect(
          AuthRedirect.resolve(auth: loggedOut, location: path),
          AppRoutes.login,
          reason: '$path should redirect to login when logged out',
        );
        expect(
          AuthRedirect.resolve(auth: authenticated, location: path),
          isNull,
          reason: '$path should be reachable when authenticated',
        );
      }
    });

    test('shell routes are listed for navigation', () {
      expect(AppRoutes.shellRoutes, contains(AppRoutes.dashboard));
      expect(AppRoutes.shellRoutes, contains(AppRoutes.animals));
      expect(AppRoutes.shellRoutes, contains(AppRoutes.alerts));
      expect(AppRoutes.shellRoutes, contains(AppRoutes.analytics));
      expect(AppRoutes.shellRoutes, contains(AppRoutes.profile));
    });

    test('BLE helper routes preserve query parameters', () {
      expect(
        AppRoutes.bleSuccess(animalId: 'a1', sensorId: 'LOS-1001'),
        '/ble/success?animalId=a1&sensorId=LOS-1001',
      );
      expect(
        AppRoutes.bleScan(animalId: 'a1', mock: true),
        '/ble/scan?animalId=a1&mock=true',
      );
    });
  });
}
