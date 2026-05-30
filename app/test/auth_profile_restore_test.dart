import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/auth/data/auth_repository.dart';
import 'package:livestock_os/features/auth/data/models/farmer_registration.dart';
import 'package:livestock_os/features/auth/providers/auth_providers.dart';
import 'package:livestock_os/features/dashboard/data/dashboard_constants.dart';
import 'package:livestock_os/features/dashboard/providers/dashboard_providers.dart';
import 'package:livestock_os/features/profile/data/profile_display_data.dart';
import 'package:livestock_os/features/profile/providers/profile_providers.dart';

import 'persistence_test_helpers.dart';

FarmerRegistration _registration({
  required String fullName,
  String phoneNumber = '9876543210',
}) {
  return FarmerRegistration(
    fullName: fullName,
    phoneNumber: phoneNumber,
    farmName: 'Green Pastures',
    village: 'Rampur',
    district: 'Meerut',
    state: 'UP',
  );
}

ProviderContainer _containerFor(AuthRepository repository) {
  return ProviderContainer(
    overrides: [authRepositoryProvider.overrideWithValue(repository)],
  );
}

void main() {
  group('registered profile restore by phone', () {
    test('register profile persists by phone', () async {
      final storage = await createTestLocalStorage();
      final repo = AuthRepository(storage);

      await repo.registerAccount(_registration(fullName: 'Sreenath'));

      final reloaded = AuthRepository(storage);
      expect(
        reloaded.savedProfileForPhone('9876543210')?.fullName,
        'Sreenath',
      );
    });

    test('logout does not delete saved profile', () async {
      final repo = AuthRepository.inMemory();
      await repo.registerAccount(_registration(fullName: 'Sreenath'));
      await repo.signOut();

      expect(repo.currentState.profile, isNull);
      expect(repo.currentState.isAuthenticated, isFalse);
      expect(repo.savedProfileForPhone('9876543210')?.fullName, 'Sreenath');
    });

    test('OTP login with same phone restores saved profile', () async {
      final repo = AuthRepository.inMemory();
      await repo.registerAccount(_registration(fullName: 'Sreenath'));
      await repo.signOut();

      await repo.requestOtp('9876543210');
      await repo.verifyOtp(AuthRepository.mockValidOtp);

      expect(repo.currentState.profile?.fullName, 'Sreenath');
      expect(repo.currentState.isAuthenticated, isTrue);
    });

    test('OTP login with formatted phone restores saved profile', () async {
      final repo = AuthRepository.inMemory();
      await repo.registerAccount(
        _registration(fullName: 'Sreenath', phoneNumber: '9876543210'),
      );
      await repo.signOut();

      await repo.requestOtp('98765 43210');
      await repo.verifyOtp(AuthRepository.mockValidOtp);

      expect(repo.currentState.profile?.fullName, 'Sreenath');
    });

    test('dashboard greeting uses restored profile name', () async {
      final repo = AuthRepository.inMemory();
      await repo.registerAccount(_registration(fullName: 'Sreenath'));
      await repo.signOut();
      await repo.requestOtp('9876543210');
      await repo.verifyOtp(AuthRepository.mockValidOtp);

      final container = _containerFor(repo);
      addTearDown(container.dispose);

      expect(container.read(dashboardFarmerNameProvider), 'Sreenath');
    });

    test('profile screen shows complete profile after restored login', () async {
      final repo = AuthRepository.inMemory();
      await repo.registerAccount(_registration(fullName: 'Sreenath'));
      await repo.signOut();
      await repo.requestOtp('9876543210');
      await repo.verifyOtp(AuthRepository.mockValidOtp);

      final container = _containerFor(repo);
      addTearDown(container.dispose);

      final display = container.read(profileDisplayProvider);
      expect(display.kind, ProfileDisplayKind.complete);
      expect(display.registration?.fullName, 'Sreenath');
      expect(display.registration?.farmName, 'Green Pastures');
    });

    test('edit profile updates saved profile record', () async {
      final storage = await createTestLocalStorage();
      final repo = AuthRepository(storage);

      await repo.registerAccount(_registration(fullName: 'Sreenath'));
      await repo.updateProfile(_registration(fullName: 'Sreenath Updated'));

      final reloaded = AuthRepository(storage);
      expect(
        reloaded.savedProfileForPhone('9876543210')?.fullName,
        'Sreenath Updated',
      );

      await reloaded.signOut();
      await reloaded.requestOtp('9876543210');
      await reloaded.verifyOtp(AuthRepository.mockValidOtp);

      expect(reloaded.currentState.profile?.fullName, 'Sreenath Updated');
    });

    test('OTP login with unknown phone remains partial', () async {
      final repo = AuthRepository.inMemory();
      await repo.completeOnboarding();
      await repo.requestOtp('9000000000');
      await repo.verifyOtp(AuthRepository.mockValidOtp);

      final container = _containerFor(repo);
      addTearDown(container.dispose);

      expect(repo.currentState.profile, isNull);
      expect(
        container.read(dashboardFarmerNameProvider),
        DashboardConstants.defaultFarmerDisplayName,
      );
      expect(
        container.read(profileDisplayProvider).kind,
        ProfileDisplayKind.partial,
      );
    });

    test('clear local data removes saved profile records', () async {
      final storage = await createTestLocalStorage();
      final repo = AuthRepository(storage);

      await repo.registerAccount(_registration(fullName: 'Sreenath'));
      await storage.clearAllUserData();

      final reloaded = AuthRepository(storage);
      expect(reloaded.savedProfileForPhone('9876543210'), isNull);

      await reloaded.completeOnboarding();
      await reloaded.requestOtp('9876543210');
      await reloaded.verifyOtp(AuthRepository.mockValidOtp);

      expect(reloaded.currentState.profile, isNull);
    });
  });
}
