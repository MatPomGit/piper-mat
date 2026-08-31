# Bazowe punkty kontrolne

Punkty kontrolne treningu są dużymi artefaktami i nie powinny być traktowane jak zwykłe pliki źródłowe.

## Aktywny punkt kontrolny

Aktywny `base.ckpt` został jednoznacznie zidentyfikowany jako publiczny punkt kontrolny **en_US-lessac-medium**, `epoch=2164-step=1355540.ckpt`, z repozytorium `rhasspy/piper-checkpoints`.

Zweryfikowane parametry:

- SHA-256: `ab7e5b8dab40f834b7cc58ae4ad7b7009c954b901e4ddbb784bbe11ce379a1cd`,
- rozmiar: `845898328` bajtów,
- rewizja źródłowa: `19ca249c3d7c490dbbefbaf775f74df10681d9a4`.

Dane te są zapisane w `checkpoints/manifest.json`.

## Pobieranie

Punkt kontrolny można pobrać bezpośrednio na podstawie manifestu:

```bash
python scripts/download_checkpoint.py base.ckpt
```

Skrypt zapisuje dane najpierw do pliku tymczasowego, a następnie weryfikuje zarówno rozmiar, jak i SHA-256. Plik docelowy jest podmieniany dopiero po poprawnej weryfikacji.

## Weryfikacja istniejącego pliku

```bash
python scripts/verify_checkpoint.py checkpoints/base.ckpt
```

Skrypt rozpoznaje zarówno rzeczywisty plik punktu kontrolnego, jak i wskaźnik Git LFS.

## Pozostałe warianty

`base_clean.ckpt`, `base_fixed.ckpt` i `base_win.ckpt` powstały w toku lokalnych prac nad kompatybilnością. Nie należy traktować ich jako niezależnych źródeł bazowych bez udokumentowania transformacji i celu.

Po potwierdzeniu, że aktywny `base.ckpt` wystarcza do powtarzalnego treningu, warianty nieużywane należy usunąć z bieżącego drzewa repozytorium i Git LFS. Pełne czyszczenie historycznych obiektów LFS jest osobną, bardziej inwazyjną operacją i nie jest wymagane do poprawnego działania projektu.
