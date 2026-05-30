import 'package:flutter_test/flutter_test.dart';
import 'package:livestock_os/features/animals/data/animal_repository.dart';
import 'package:livestock_os/features/animals/data/models/animal.dart';
import 'package:livestock_os/features/qr/data/animal_qr_codec.dart';
import 'package:livestock_os/features/qr/data/animal_qr_lookup.dart';
import 'package:livestock_os/features/qr/data/models/animal_qr_payload.dart';

void main() {
  test('QR payload encodes and decodes round trip', () {
    final payload = AnimalQrPayload(
      animalId: 'animal-001',
      tagId: 'TAG-1001',
      animalName: 'Gauri',
      generatedAt: DateTime(2026, 5, 21, 10),
    );

    final decoded = AnimalQrPayload.tryDecode(payload.encode());
    expect(decoded?.animalId, 'animal-001');
    expect(decoded?.tagId, 'TAG-1001');
    expect(decoded?.animalName, 'Gauri');
  });

  test('lookup resolves by tag id, animal id, and encoded payload', () async {
    final repo = AnimalRepository.inMemory();

    expect(AnimalQrLookup.resolve(repo, 'TAG-1001')?.name, 'Gauri');
    expect(AnimalQrLookup.resolve(repo, 'animal-002')?.name, 'Nandi');

    final encoded = AnimalQrCodec.encode(repo.animals.first);
    expect(AnimalQrLookup.resolve(repo, encoded)?.id, repo.animals.first.id);

    expect(AnimalQrLookup.resolve(repo, 'INVALID'), isNull);
  });

  test('newly added animal can generate QR without sensor data', () async {
    final repo = AnimalRepository.inMemory();
    final added = await repo.addAnimal(
      name: 'QR Cow',
      tagId: 'TAG-QR-NEW',
      breed: 'Gir',
      age: 2,
      gender: AnimalGender.female,
      weight: 300,
    );

    final encoded = AnimalQrCodec.encode(added);
    expect(encoded.contains(added.id), isTrue);
    expect(AnimalQrLookup.resolve(repo, encoded)?.id, added.id);
    expect(added.hasHealthData, isFalse);
    expect(added.sensorStatus, AnimalSensorStatus.notPaired);
  });
}
