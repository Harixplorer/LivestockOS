import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/app.dart';
import 'persistence_test_helpers.dart';

void main() {
  testWidgets('LivestockOS launches on splash screen', (tester) async {
    final overrides = await sharedPreferencesOverrides();
    await tester.pumpWidget(
      ProviderScope(
        overrides: overrides,
        child: const LivestockApp(),
      ),
    );
    await tester.pump();

    expect(find.text('LivestockOS'), findsOneWidget);
    expect(find.text('Smart Livestock Health Monitoring'), findsOneWidget);

    await tester.pump(const Duration(seconds: 3));
    await tester.pump(const Duration(milliseconds: 700));
  });
}
