import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/core/router/app_routes.dart';
import 'package:livestock_os/core/router/auth_redirect.dart';
import 'package:livestock_os/features/auth/data/models/auth_state.dart';
import 'package:livestock_os/features/auth/domain/auth_status.dart';

void main() {
  test('unauthenticated users are sent to login from dashboard', () {
    const auth = AuthState(
      status: AuthStatus.unauthenticated,
      onboardingComplete: true,
    );

    expect(
      AuthRedirect.resolve(auth: auth, location: AppRoutes.dashboard),
      AppRoutes.login,
    );
  });

  test('authenticated users are sent to dashboard from login', () {
    const auth = AuthState(
      status: AuthStatus.authenticated,
      onboardingComplete: true,
    );

    expect(
      AuthRedirect.resolve(auth: auth, location: AppRoutes.login),
      AppRoutes.dashboard,
    );
  });

  test('logged-out users are sent to login from profile', () {
    const auth = AuthState(
      status: AuthStatus.unauthenticated,
      onboardingComplete: true,
    );

    expect(
      AuthRedirect.resolve(auth: auth, location: AppRoutes.profile),
      AppRoutes.login,
    );
  });

  test('users without onboarding are sent to onboarding', () {
    const auth = AuthState(
      status: AuthStatus.unauthenticated,
      onboardingComplete: false,
    );

    expect(
      AuthRedirect.resolve(auth: auth, location: AppRoutes.login),
      AppRoutes.onboarding,
    );
  });
}
