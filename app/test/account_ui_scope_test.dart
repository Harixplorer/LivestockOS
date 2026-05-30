import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:livestock_os/core/persistence/account_ui_scope_provider.dart';
import 'package:livestock_os/core/persistence/persistence_providers.dart';
import 'package:livestock_os/features/alerts/data/models/alerts_list_query.dart';
import 'package:livestock_os/features/alerts/providers/alert_providers.dart';
import 'package:livestock_os/features/animals/providers/animal_providers.dart';
import 'package:livestock_os/features/analytics/providers/analytics_providers.dart';
import 'package:livestock_os/features/auth/data/auth_repository.dart';
import 'package:livestock_os/features/auth/data/models/farmer_registration.dart';
import 'package:livestock_os/features/auth/providers/auth_providers.dart';
import 'package:livestock_os/features/ble/providers/ble_providers.dart';
import 'package:livestock_os/providers/theme_mode_provider.dart';

FarmerRegistration _profile(String phone, String name) {
  return FarmerRegistration(
    fullName: name,
    phoneNumber: phone,
    farmName: 'Farm',
    village: 'Village',
    district: 'District',
    state: 'State',
  );
}

void main() {
  group('account UI scope', () {
    test('alerts filter resets when account changes', () async {
      final authRepo = AuthRepository.inMemory();
      await authRepo.registerAccount(_profile('9876543210', 'Account A'));
      await authRepo.signOut();
      await authRepo.registerAccount(_profile('9999999999', 'Account B'));
      await authRepo.signOut();

      final container = ProviderContainer(
        overrides: [authRepositoryProvider.overrideWithValue(authRepo)],
      );
      addTearDown(container.dispose);

      container.listen(accountUiScopeProvider, (previous, next) {});
      await container.read(authStateProvider.notifier).requestOtp('9876543210');
      await container.read(authStateProvider.notifier).verifyOtp(
            AuthRepository.mockValidOtp,
          );

      container
          .read(alertsListQueryProvider.notifier)
          .setFilter(AlertSeverityFilter.resolved);
      expect(
        container.read(alertsListQueryProvider).severityFilter,
        AlertSeverityFilter.resolved,
      );

      await container.read(authStateProvider.notifier).signOut();
      expect(
        container.read(alertsListQueryProvider).severityFilter,
        AlertSeverityFilter.all,
      );

      await container.read(authStateProvider.notifier).requestOtp('9999999999');
      await container.read(authStateProvider.notifier).verifyOtp(
            AuthRepository.mockValidOtp,
          );
      expect(
        container.read(alertsListQueryProvider).severityFilter,
        AlertSeverityFilter.all,
      );
    });

    test('animals search filter resets when account changes', () async {
      final authRepo = AuthRepository.inMemory();
      await authRepo.registerAccount(_profile('9876543210', 'Account A'));
      await authRepo.signOut();
      await authRepo.registerAccount(_profile('9999999999', 'Account B'));
      await authRepo.signOut();

      final container = ProviderContainer(
        overrides: [authRepositoryProvider.overrideWithValue(authRepo)],
      );
      addTearDown(container.dispose);

      container.listen(accountUiScopeProvider, (previous, next) {});
      await container.read(authStateProvider.notifier).requestOtp('9876543210');
      await container.read(authStateProvider.notifier).verifyOtp(
            AuthRepository.mockValidOtp,
          );

      container.read(animalsListQueryProvider.notifier).setSearch('gauri');
      expect(container.read(animalsListQueryProvider).search, 'gauri');

      await container.read(authStateProvider.notifier).signOut();
      expect(container.read(animalsListQueryProvider).search, isEmpty);
    });

    test('analytics comparison selection resets when account changes', () async {
      final authRepo = AuthRepository.inMemory();
      await authRepo.registerAccount(_profile('9876543210', 'Account A'));
      await authRepo.signOut();
      await authRepo.registerAccount(_profile('9999999999', 'Account B'));
      await authRepo.signOut();

      final container = ProviderContainer(
        overrides: [authRepositoryProvider.overrideWithValue(authRepo)],
      );
      addTearDown(container.dispose);

      container.listen(accountUiScopeProvider, (previous, next) {});
      await container.read(authStateProvider.notifier).requestOtp('9876543210');
      await container.read(authStateProvider.notifier).verifyOtp(
            AuthRepository.mockValidOtp,
          );

      container.read(animalComparisonSelectionProvider.notifier).state =
          const ['animal-001'];
      expect(container.read(animalComparisonSelectionProvider), isNotEmpty);

      await container.read(authStateProvider.notifier).signOut();
      expect(container.read(animalComparisonSelectionProvider), isEmpty);
    });

    test('BLE session clears when account changes', () async {
      final authRepo = AuthRepository.inMemory();
      await authRepo.registerAccount(_profile('9876543210', 'Account A'));
      await authRepo.signOut();
      await authRepo.registerAccount(_profile('9999999999', 'Account B'));
      await authRepo.signOut();

      final container = ProviderContainer(
        overrides: [authRepositoryProvider.overrideWithValue(authRepo)],
      );
      addTearDown(container.dispose);

      container.listen(accountUiScopeProvider, (previous, next) {});
      await container.read(authStateProvider.notifier).requestOtp('9876543210');
      await container.read(authStateProvider.notifier).verifyOtp(
            AuthRepository.mockValidOtp,
          );

      container.read(bleSelectionProvider).setAnimalId('animal-001');

      await container.read(authStateProvider.notifier).signOut();
      expect(container.read(blePairingAnimalIdProvider), isNull);
    });

    test('theme mode is not reset on account change', () async {
      SharedPreferences.setMockInitialValues({});
      final prefs = await SharedPreferences.getInstance();
      final authRepo = AuthRepository.inMemory();
      await authRepo.registerAccount(_profile('9876543210', 'Account A'));

      final container = ProviderContainer(
        overrides: [
          authRepositoryProvider.overrideWithValue(authRepo),
          sharedPreferencesProvider.overrideWithValue(prefs),
        ],
      );
      addTearDown(container.dispose);

      container.listen(accountUiScopeProvider, (previous, next) {});
      await container.read(themeModeProvider.notifier).setThemeMode(
            ThemeMode.dark,
          );

      await container.read(authStateProvider.notifier).signOut();
      expect(container.read(themeModeProvider), ThemeMode.dark);
    });
  });
}
