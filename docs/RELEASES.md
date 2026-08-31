# Wydawanie modelu

Finalny głos nie powinien być publikowany jako przypadkowy plik ONNX w głównym katalogu repozytorium. Wydanie powinno być jednoznacznie identyfikowalne i weryfikowalne.

## Zawartość wydania

Minimalny pakiet zawiera:

- `pl_PL-mateusz-medium.onnx`,
- `pl_PL-mateusz-medium.onnx.json`,
- `MODEL_CARD.md`,
- `release-manifest.json`,
- `checksums.txt`,
- opcjonalny katalog `samples/` z próbkami WAV.

Pakiet przygotowuje skrypt:

```bash
python scripts/package_release.py \
  --model output/pl_PL-mateusz-medium.onnx \
  --config output/pl_PL-mateusz-medium.onnx.json \
  --samples samples/pl_PL-mateusz-medium \
  --output dist/pl_PL-mateusz-medium
```

Każdy plik otrzymuje rozmiar oraz SHA-256. Katalog `dist/` pozostaje lokalnym artefaktem budowania i nie powinien być wersjonowany.

## Publikacja

Docelowo paczkę należy publikować w GitHub Releases lub Hugging Face. Przed publikacją należy uruchomić smoke test ONNX oraz uzupełnić Model Card o faktyczne wyniki ewaluacji.
