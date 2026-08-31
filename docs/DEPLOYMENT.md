# Wdrożenie modelu

Ten rozdział opisuje docelową ścieżkę instalacji `pl_PL-mateusz-medium` po przygotowaniu finalnej pary ONNX/JSON.

## Artefakty

Wymagane są co najmniej:

```text
pl_PL-mateusz-medium.onnx
pl_PL-mateusz-medium.onnx.json
```

Przed instalacją należy zweryfikować sumy SHA-256 z paczki wydania i uruchomić `scripts/smoke_test_voice.py`.

## Piper CLI

Model można uruchomić bezpośrednio:

```bash
piper \
  --model pl_PL-mateusz-medium.onnx \
  --output_file test.wav \
  -- "To jest test polskiego głosu."
```

Plik JSON musi znajdować się obok ONNX i mieć nazwę `pl_PL-mateusz-medium.onnx.json`.

## Wyoming Piper

W kontenerowym wdrożeniu Wyoming Piper należy zamontować katalog zawierający model i konfigurację jako wolumin tylko do odczytu. Nazwa i dokładne argumenty uruchomieniowe zależą od używanej wersji obrazu, dlatego przed wdrożeniem należy sprawdzić `--help` konkretnej wersji.

Przykładowy układ danych:

```text
/srv/piper/voices/
├── pl_PL-mateusz-medium.onnx
└── pl_PL-mateusz-medium.onnx.json
```

Po restarcie usługi należy wykonać lokalny test syntezy przed podłączeniem Home Assistant.

## Home Assistant

Home Assistant powinien korzystać z usługi Piper przez integrację Wyoming. Sekrety i tokeny Home Assistant nie powinny być przechowywane w tym repozytorium.

Po dodaniu usługi należy sprawdzić kolejno:

1. czy Home Assistant widzi usługę Wyoming Piper,
2. czy głos `pl_PL-mateusz-medium` jest dostępny,
3. czy synteza pojedynczego zdania kończy się poprawnie,
4. czy wygenerowany dźwięk może zostać odtworzony na docelowym odtwarzaczu multimedialnym,
5. czy początek wypowiedzi nie jest obcinany przez urządzenie odtwarzające.

## Aktualizacja modelu

Nowe wydanie należy wdrażać jako komplet ONNX + JSON. Nie należy mieszać pliku modelu z jednej wersji z konfiguracją z innej wersji.

Zalecana procedura:

1. pobrać nową paczkę wydania,
2. zweryfikować `checksums.txt`,
3. wykonać test poprawności lokalnie,
4. zachować poprzednią wersję do szybkiego wycofania,
5. podmienić komplet artefaktów,
6. zrestartować usługę Piper,
7. wykonać test odsłuchowy i pomiar RTF,
8. usunąć poprzednią wersję dopiero po potwierdzeniu stabilności.

## Wycofanie wersji

Jeżeli nowy model powoduje regresję wymowy, jakości lub wydajności, należy przywrócić poprzednią kompletną parę ONNX/JSON i odnotować problem w wynikach ewaluacji. Dzięki temu wdrożenie modelu pozostaje odwracalne i niezależne od procesu treningowego.
