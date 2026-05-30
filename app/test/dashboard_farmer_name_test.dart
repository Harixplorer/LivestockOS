import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/auth/data/auth_repository.dart';
import 'package:livestock_os/features/auth/data/models/farmer_registration.dart';
import 'package:livestock_os/features/auth/providers/auth_providers.dart';
import 'package:livestock_os/features/dashboard/data/dashboard_constants.dart';
import 'package:livestock_os/features/dashboard/providers/dashboard_providers.dart';

void main() {
  test('dashboard uses registered farmer name from auth profile', () async {
    final repository = AuthRepository.inMemory();
    await repository.registerAccount(
      const FarmerRegistration(
        fullName: 'Sreenath',
        phoneNumber: '9876543210',
        farmName: 'Test Farm',
        village: 'Village',
        district: 'District',
        state: 'State',
      ),
    );

    final container = ProviderContainer(
      overrides: [authRepositoryProvider.overrideWithValue(repository)],
    );
    addTearDown(container.dispose);

    expect(container.read(dashboardFarmerNameProvider), 'Sreenath');
  });

  test('dashboard falls back when auth profile has no name', () async {
    final repository = AuthRepository.inMemory();
    await repository.completeOnboarding();
    await repository.requestOtp('9876543210');
    await repository.verifyOtp(AuthRepository.mockValidOtp);

    final container = ProviderContainer(
      overrides: [authRepositoryProvider.overrideWithValue(repository)],
    );
    addTearDown(container.dispose);

    expect(
      container.read(dashboardFarmerNameProvider),
      DashboardConstants.defaultFarmerDisplayName,
    );
  });

  test('logout clears farmer name from auth profile', () async {
    final repository = AuthRepository.inMemory();
    await repository.registerAccount(
      const FarmerRegistration(
        fullName: 'Sreenath',
        phoneNumber: '9876543210',
        farmName: 'Test Farm',
        village: 'Village',
        district: 'District',
        state: 'State',
      ),
    );
    await repository.signOut();

    expect(repository.currentState.farmerName, isNull);
  });

  test('login after logout restores farmer name on dashboard', () async {
    final repository = AuthRepository.inMemory();
    await repository.registerAccount(
      const FarmerRegistration(
        fullName: 'Sreenath',
        phoneNumber: '9876543210',
        farmName: 'Test Farm',
        village: 'Village',
        district: 'District',
        state: 'State',
      ),
    );
    await repository.signOut();
    await repository.requestOtp('9876543210');
    await repository.verifyOtp(AuthRepository.mockValidOtp);

    final container = ProviderContainer(
      overrides: [authRepositoryProvider.overrideWithValue(repository)],
    );
    addTearDown(container.dispose);

    expect(container.read(dashboardFarmerNameProvider), 'Sreenath');
  });
}
