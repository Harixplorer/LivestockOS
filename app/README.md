# LivestockOS

AI-powered livestock monitoring frontend built with Flutter. LivestockOS helps farmers register animals, pair BLE sensors, scan QR codes, monitor health readings, manage alerts, and explore herd analytics — all with local persistence and account-scoped data for demo-ready offline use.

## Features

- **Authentication** — Onboarding, phone OTP login, farmer registration, profile restore by phone
- **Dashboard** — Personalized greeting, herd summary, quick actions, health charts
- **Animals** — Add, edit, search, filter; pending/paired sensor states; seed demo animals
- **QR codes** — Generate animal QR, scan via camera (with manual entry and Demo QR fallback)
- **BLE pairing** — Mock sensor pairing on all platforms; real BLE on Android physical devices
- **Live monitor** — Real-time mock readings; disconnect without unpairing
- **Health analytics** — Health score, reading history, trends per animal
- **Alerts** — Filter, search, sort, resolve/reopen, navigate to animal
- **Analytics** — Dashboard charts, trends, comparison, sensor coverage (no fake data for pending animals)
- **Profile & settings** — Edit profile, theme (light/dark), notifications, farm info, units, data & sync
- **Persistence** — Account-scoped local storage via SharedPreferences

## Setup

### Prerequisites

- [Flutter SDK](https://docs.flutter.dev/get-started/install) (SDK ^3.11.5)
- Android Studio / Xcode (for mobile builds)
- Chrome (for web demo)

### Install

```bash
git clone <repository-url>
cd mycode
flutter pub get
```

## Run

```bash
# Chrome (recommended for demo)
flutter run -d chrome

# Android emulator or device
flutter run -d android

# List available devices
flutter devices
```

## Test & analyze

```bash
flutter analyze
flutter test
```

## Build

```bash
# Debug APK (Android)
flutter build apk --debug

# Web release
flutter build web
```

## Android permissions

Declared in `android/app/src/main/AndroidManifest.xml`:

| Permission | Purpose |
|------------|---------|
| `CAMERA` | QR code scanning |
| `BLUETOOTH`, `BLUETOOTH_ADMIN` (API ≤ 30) | Legacy BLE |
| `BLUETOOTH_SCAN`, `BLUETOOTH_CONNECT` | BLE scan and connect (API 31+) |
| `ACCESS_FINE_LOCATION` (API ≤ 30) | Required for legacy BLE scanning |

Real BLE pairing and live readings require a **physical Android device** with Bluetooth enabled. Emulators and web use mock BLE.

## BLE device details

Pair with sensors advertising this GATT profile:

| Field | Value |
|-------|-------|
| **Device name** | `LivestockOS_Sensor` |
| **Service UUID** | `4fafc201-1fb5-459e-8fcc-c5c9c331914b` |

### Characteristics

| Reading | UUID | Format |
|---------|------|--------|
| Temperature | `beb5483e-36e1-4688-b7f5-ea07361b26a8` | float32 little-endian, °C |
| Activity | `beb5483e-36e1-4688-b7f5-ea07361b26a9` | int32 little-endian, 0–100 |
| Behaviour | `beb5483e-36e1-4688-b7f5-ea07361b26aa` | UTF-8 string |
| Rumination | `beb5483e-36e1-4688-b7f5-ea07361b26ab` | int32 little-endian, minutes/hour |

### Mock sensor IDs (demo)

Use manual sensor entry or mock BLE scan. Example available sensors include `LOS-1001`, `LOS-1002`, `LOS-1003`. Invalid IDs such as `LOS-1234` show a not-found error.

## Demo flow

1. **Register** a new farmer (name appears on dashboard greeting)
2. **Logout** and **login** with the same phone — profile restores
3. **Add animal** — shows pending / no sensor
4. **Generate QR** from animal detail
5. **Scan QR** — use **Demo QR** or manual entry if camera is unavailable
6. **Pair mock sensor** via BLE (manual ID `LOS-1001` or mock scan)
7. **View Live Monitor** — disconnect session; animal stays paired
8. **Unpair sensor** — animal returns to not paired
9. Open a **seed animal** — health score, readings, trends, comparison
10. **Resolve an alert** — filter/search alerts, open detail
11. **Analytics** — dashboard, trends, comparison, sensor coverage
12. **Edit profile/settings** — theme, notifications, Data & Sync
13. **Restart app** — data persists; account isolation holds

See [docs/FINAL_QA.md](docs/FINAL_QA.md) for the full demo script and QA notes.

## Known limitations

- **QR camera** may be unreliable on Chrome (pause/resume); use manual QR entry or Demo QR
- **Real BLE** only on Android physical devices; web/emulator use mock BLE
- **Backend** not integrated — all data is local
- **AI/ML predictions** are simulated/mock
- **Local persistence only** — no cloud sync
- **Push notifications** are placeholder UI
- **Language settings** are placeholder UI

## Project structure

```
lib/
├── core/           # Router, theme, persistence, shared widgets
├── features/       # auth, animals, ble, qr, alerts, analytics, profile, settings
├── shell/          # App shell and route content mapping
└── app.dart        # Root widget
```

## License

Private demo project — not published to pub.dev.
