import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:livestock_os/core/router/app_routes.dart';
import 'package:livestock_os/core/router/auth_redirect.dart';
import 'package:livestock_os/core/widgets/layout/app_screen_header.dart';
import 'package:livestock_os/features/animals/presentation/widgets/animal_screen_header.dart';
import 'package:livestock_os/features/auth/data/auth_repository.dart';
import 'package:livestock_os/features/auth/data/models/auth_state.dart';
import 'package:livestock_os/features/auth/data/models/farmer_registration.dart';
import 'package:livestock_os/features/auth/domain/auth_status.dart';
import 'package:livestock_os/features/auth/providers/auth_providers.dart';
import 'package:livestock_os/features/dashboard/providers/dashboard_providers.dart';
import 'package:livestock_os/features/profile/data/profile_constants.dart';
import 'package:livestock_os/features/profile/data/profile_display_data.dart';
import 'package:livestock_os/features/profile/providers/profile_providers.dart';
import 'package:livestock_os/features/settings/data/settings_constants.dart';
import 'package:livestock_os/features/settings/data/models/user_settings.dart';
import 'package:livestock_os/features/settings/data/settings_repository.dart';
import 'package:livestock_os/features/settings/providers/settings_providers.dart';
import 'package:livestock_os/core/persistence/persistence_providers.dart';
import 'package:livestock_os/providers/theme_mode_provider.dart';

void main() {
  group('profile and auth', () {
    test('profile displays registered farmer name via dashboard provider', () async {
      final repository = AuthRepository.inMemory();
      await repository.registerAccount(
        const FarmerRegistration(
          fullName: 'Ravi Kumar',
          phoneNumber: '9876543210',
          farmName: 'Green Pastures',
          village: 'Village',
          district: 'District',
          state: 'State',
        ),
      );

      final container = ProviderContainer(
        overrides: [authRepositoryProvider.overrideWithValue(repository)],
      );
      addTearDown(container.dispose);

      expect(container.read(dashboardFarmerNameProvider), 'Ravi Kumar');
    });

    test('profile display is complete for registered farmer', () async {
      final repository = AuthRepository.inMemory();
      await repository.registerAccount(
        const FarmerRegistration(
          fullName: 'Ravi Kumar',
          phoneNumber: '9876543210',
          farmName: 'Green Pastures',
          village: 'Village',
          district: 'District',
          state: 'State',
        ),
      );

      final container = ProviderContainer(
        overrides: [authRepositoryProvider.overrideWithValue(repository)],
      );
      addTearDown(container.dispose);

      final display = container.read(profileDisplayProvider);
      expect(display.kind, ProfileDisplayKind.complete);
      expect(display.registration?.fullName, 'Ravi Kumar');
      expect(display.registration?.farmName, 'Green Pastures');
    });

    test('profile display is partial for OTP-only login', () async {
      final repository = AuthRepository.inMemory();
      await repository.requestOtp('9876543210');
      await repository.verifyOtp(AuthRepository.mockValidOtp);

      final container = ProviderContainer(
        overrides: [authRepositoryProvider.overrideWithValue(repository)],
      );
      addTearDown(container.dispose);

      final display = container.read(profileDisplayProvider);
      expect(display.kind, ProfileDisplayKind.partial);
      expect(display.phoneNumber, '9876543210');
      expect(display.registration, isNull);
    });

    test('registered profile does not use incomplete message kind', () async {
      final repository = AuthRepository.inMemory();
      await repository.registerAccount(
        const FarmerRegistration(
          fullName: 'Registered Farmer',
          phoneNumber: '9876543210',
          farmName: 'Farm',
          village: 'V',
          district: 'D',
          state: 'S',
        ),
      );

      final container = ProviderContainer(
        overrides: [authRepositoryProvider.overrideWithValue(repository)],
      );
      addTearDown(container.dispose);

      expect(
        container.read(profileDisplayProvider).kind,
        isNot(ProfileDisplayKind.partial),
      );
    });

    test('edit profile updates auth state and dashboard greeting', () async {
      final repository = AuthRepository.inMemory();
      await repository.registerAccount(
        const FarmerRegistration(
          fullName: 'Before Edit',
          phoneNumber: '9876543210',
          farmName: 'Farm',
          village: 'V',
          district: 'D',
          state: 'S',
        ),
      );

      final container = ProviderContainer(
        overrides: [authRepositoryProvider.overrideWithValue(repository)],
      );
      addTearDown(container.dispose);

      await container.read(authStateProvider.notifier).updateProfile(
            const FarmerRegistration(
              fullName: 'After Edit',
              phoneNumber: '9876543210',
              farmName: 'Farm',
              village: 'V',
              district: 'D',
              state: 'S',
            ),
          );

      expect(container.read(authStateProvider).farmerName, 'After Edit');
      expect(container.read(dashboardFarmerNameProvider), 'After Edit');
    });

    test('logout clears auth state', () async {
      final repository = AuthRepository.inMemory();
      await repository.registerAccount(
        const FarmerRegistration(
          fullName: 'Logout User',
          phoneNumber: '9876543210',
          farmName: 'Farm',
          village: 'V',
          district: 'D',
          state: 'S',
        ),
      );
      await repository.signOut();

      expect(repository.currentState.isAuthenticated, isFalse);
      expect(repository.currentState.profile, isNull);
    });

    test('protected route redirects after logout', () {
      const auth = AuthState(
        status: AuthStatus.unauthenticated,
        onboardingComplete: true,
      );

      expect(
        AuthRedirect.resolve(auth: auth, location: AppRoutes.settings),
        AppRoutes.login,
      );
      expect(
        AuthRedirect.resolve(auth: auth, location: AppRoutes.profileEdit),
        AppRoutes.login,
      );
      expect(
        AuthRedirect.resolve(auth: auth, location: AppRoutes.settingsUnits),
        AppRoutes.login,
      );
    });
  });

  group('settings', () {
    test('theme selector updates theme mode', () async {
      SharedPreferences.setMockInitialValues({});
      final prefs = await SharedPreferences.getInstance();
      final container = ProviderContainer(
        overrides: [
          sharedPreferencesProvider.overrideWithValue(prefs),
        ],
      );
      addTearDown(container.dispose);

      expect(container.read(themeModeProvider), ThemeMode.system);

      await container.read(themeModeProvider.notifier).setThemeMode(ThemeMode.dark);
      expect(container.read(themeModeProvider), ThemeMode.dark);

      await container.read(themeModeProvider.notifier).setThemeMode(ThemeMode.light);
      expect(container.read(themeModeProvider), ThemeMode.light);
    });

    test('notification settings update mock state', () async {
      final settingsRepo = SettingsRepository.inMemory();
      final container = ProviderContainer(
        overrides: [
          settingsRepositoryProvider.overrideWithValue(settingsRepo),
          currentAccountKeyProvider.overrideWith((ref) => null),
        ],
      );
      addTearDown(container.dispose);

      await container.read(userSettingsProvider.future);

      await container.read(userSettingsProvider.notifier).updateNotifications(
            const NotificationPreferences(dailySummary: true),
          );

      expect(
        container.read(notificationPreferencesProvider).dailySummary,
        isTrue,
      );
    });

    test('farm settings save updates auth profile farm fields', () async {
      final authRepo = AuthRepository.inMemory();
      await authRepo.requestOtp('9876543210');
      await authRepo.verifyOtp(AuthRepository.mockValidOtp);

      final settingsRepo = SettingsRepository.inMemory();
      final container = ProviderContainer(
        overrides: [
          authRepositoryProvider.overrideWithValue(authRepo),
          settingsRepositoryProvider.overrideWithValue(settingsRepo),
          currentAccountKeyProvider.overrideWith((ref) => '9876543210'),
        ],
      );
      addTearDown(container.dispose);

      await container.read(userSettingsProvider.future);

      await container.read(authStateProvider.notifier).updateProfile(
            const FarmerRegistration(
              fullName: '',
              phoneNumber: '9876543210',
              farmName: 'Sunrise Dairy',
              village: 'Rampur',
              district: 'Meerut',
              state: 'UP',
            ),
          );

      final profile = container.read(authStateProvider).profile!;
      expect(profile.farmName, 'Sunrise Dairy');
      expect(profile.village, 'Rampur');

      final display = container.read(profileDisplayProvider);
      expect(display.registration?.farmName, 'Sunrise Dairy');
    });

    testWidgets('app screen header pops when navigation stack allows', (
      tester,
    ) async {
      final router = GoRouter(
        routes: [
          GoRoute(
            path: '/',
            builder: (context, state) => const Scaffold(
              body: Center(child: Text('Home')),
            ),
            routes: [
              GoRoute(
                path: 'detail',
                builder: (context, state) => const Scaffold(
                  body: AppScreenHeader(
                    title: 'Detail',
                    fallbackRoute: AppRoutes.settings,
                  ),
                ),
              ),
            ],
          ),
        ],
      );
      addTearDown(router.dispose);

      router.go('/detail');
      await tester.pumpWidget(MaterialApp.router(routerConfig: router));
      await tester.pumpAndSettle();

      expect(find.text('Detail'), findsOneWidget);
      await tester.tap(find.byIcon(Icons.arrow_back));
      await tester.pumpAndSettle();

      expect(find.text('Home'), findsOneWidget);
    });

    testWidgets('app screen header uses fallback when cannot pop', (
      tester,
    ) async {
      final router = GoRouter(
        routes: [
          GoRoute(
            path: '/',
            builder: (context, state) => const AppScreenHeader(
              title: 'Test',
              fallbackRoute: AppRoutes.settings,
            ),
          ),
          GoRoute(
            path: AppRoutes.settings,
            builder: (context, state) =>
                const Scaffold(body: Text('Settings hub')),
          ),
        ],
      );
      addTearDown(router.dispose);

      await tester.pumpWidget(MaterialApp.router(routerConfig: router));
      await tester.pumpAndSettle();

      await tester.tap(find.byIcon(Icons.arrow_back));
      await tester.pumpAndSettle();

      expect(find.text('Settings hub'), findsOneWidget);
    });

    testWidgets('app screen header defaults to dashboard fallback', (
      tester,
    ) async {
      final router = GoRouter(
        routes: [
          GoRoute(
            path: '/',
            builder: (context, state) =>
                const AppScreenHeader(title: 'No fallback'),
          ),
          GoRoute(
            path: AppRoutes.dashboard,
            builder: (context, state) =>
                const Scaffold(body: Text('Dashboard')),
          ),
        ],
      );
      addTearDown(router.dispose);

      await tester.pumpWidget(MaterialApp.router(routerConfig: router));
      await tester.pumpAndSettle();

      await tester.tap(find.byIcon(Icons.arrow_back));
      await tester.pumpAndSettle();

      expect(find.text('Dashboard'), findsOneWidget);
    });

    testWidgets('animal screen header delegates to app screen header', (
      tester,
    ) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: AnimalScreenHeader(
              title: SettingsConstants.notificationsTitle,
              fallbackRoute: AppRoutes.settings,
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.arrow_back), findsOneWidget);
      expect(find.text(SettingsConstants.notificationsTitle), findsOneWidget);
    });

    testWidgets('settings detail titles render pinned back headers', (
      tester,
    ) async {
      const detailTitles = [
        SettingsConstants.settingsTitle,
        SettingsConstants.notificationsTitle,
        SettingsConstants.farmTitle,
        SettingsConstants.aboutTitle,
        SettingsConstants.unitsTitle,
        SettingsConstants.languageTitle,
        SettingsConstants.dataSyncTitle,
        ProfileConstants.editTitle,
      ];

      for (final title in detailTitles) {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: AppScreenHeader(
                title: title,
                fallbackRoute: AppRoutes.settings,
              ),
            ),
          ),
        );
        expect(find.byIcon(Icons.arrow_back), findsOneWidget);
        expect(find.text(title), findsOneWidget);
      }
    });
  });

  group('profile UI copy', () {
    test('partial profile uses incomplete message not registration prompt', () {
      expect(
        ProfileConstants.incompleteProfileMessage,
        isNot(contains('Complete registration')),
      );
      expect(ProfileConstants.completeProfile, 'Complete profile');
    });
  });
}
