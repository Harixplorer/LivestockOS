import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:livestock_os/core/persistence/local_storage_service.dart';
import 'package:livestock_os/core/persistence/persistence_providers.dart';

/// Creates an in-memory SharedPreferences instance for tests.
Future<LocalStorageService> createTestLocalStorage([
  Map<String, Object> initialValues = const {},
]) async {
  SharedPreferences.setMockInitialValues(initialValues);
  final prefs = await SharedPreferences.getInstance();
  return LocalStorageService(prefs);
}

/// Riverpod container with mock SharedPreferences for widget/integration tests.
Future<ProviderContainer> createTestProviderContainer({
  List<Override> overrides = const [],
  Map<String, Object> initialValues = const {},
}) async {
  SharedPreferences.setMockInitialValues(initialValues);
  final prefs = await SharedPreferences.getInstance();

  return ProviderContainer(
    overrides: [
      sharedPreferencesProvider.overrideWithValue(prefs),
      ...overrides,
    ],
  );
}

/// SharedPreferences override list for manual ProviderScope / ProviderContainer setup.
Future<List<Override>> sharedPreferencesOverrides([
  Map<String, Object> initialValues = const {},
]) async {
  SharedPreferences.setMockInitialValues(initialValues);
  final prefs = await SharedPreferences.getInstance();
  return [sharedPreferencesProvider.overrideWithValue(prefs)];
}
