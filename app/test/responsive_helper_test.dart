import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/core/constants/app_spacing.dart';
import 'package:livestock_os/core/utils/responsive_helper.dart';
import 'package:livestock_os/core/widgets/charts/app_chart_style.dart';

void main() {
  group('ResponsiveHelper', () {
    Future<void> pumpWithSize(
      WidgetTester tester, {
      required Size size,
      required Widget Function(BuildContext context) builder,
    }) {
      return tester.pumpWidget(
        MaterialApp(
          home: MediaQuery(
            data: MediaQueryData(size: size),
            child: Builder(builder: builder),
          ),
        ),
      );
    }

    testWidgets('classifies mobile, tablet, and desktop widths', (tester) async {
      await pumpWithSize(
        tester,
        size: const Size(400, 800),
        builder: (context) => Text(
          '${ResponsiveHelper.isMobile(context)}'
          '${ResponsiveHelper.isTablet(context)}'
          '${ResponsiveHelper.isDesktop(context)}',
        ),
      );
      expect(find.text('truefalsefalse'), findsOneWidget);

      await pumpWithSize(
        tester,
        size: const Size(800, 800),
        builder: (context) => Text(
          '${ResponsiveHelper.isMobile(context)}'
          '${ResponsiveHelper.isTablet(context)}'
          '${ResponsiveHelper.isDesktop(context)}',
        ),
      );
      expect(find.text('falsetruefalse'), findsOneWidget);

      await pumpWithSize(
        tester,
        size: const Size(1200, 800),
        builder: (context) => Text(
          '${ResponsiveHelper.isMobile(context)}'
          '${ResponsiveHelper.isTablet(context)}'
          '${ResponsiveHelper.isDesktop(context)}',
        ),
      );
      expect(find.text('falsefalsetrue'), findsOneWidget);
    });

    testWidgets('scrollBottomPadding increases on larger screens', (tester) async {
      await pumpWithSize(
        tester,
        size: const Size(400, 800),
        builder: (context) => Text(
          ResponsiveHelper.scrollBottomPadding(context).toString(),
        ),
      );
      expect(find.text(AppSpacing.lg.toString()), findsOneWidget);

      await pumpWithSize(
        tester,
        size: const Size(1200, 800),
        builder: (context) => Text(
          ResponsiveHelper.scrollBottomPadding(context).toString(),
        ),
      );
      expect(find.text(AppSpacing.xl.toString()), findsOneWidget);
    });

    testWidgets('bottomLabelInterval thins labels on mobile for long series',
        (tester) async {
      late double mobileInterval;
      late double desktopInterval;

      await pumpWithSize(
        tester,
        size: const Size(400, 800),
        builder: (context) {
          mobileInterval = AppChartStyle.bottomLabelInterval(16, context);
          return const SizedBox.shrink();
        },
      );
      expect(mobileInterval, 4);

      await pumpWithSize(
        tester,
        size: const Size(1200, 800),
        builder: (context) {
          desktopInterval = AppChartStyle.bottomLabelInterval(16, context);
          return const SizedBox.shrink();
        },
      );
      expect(desktopInterval, 3);
    });
  });
}
