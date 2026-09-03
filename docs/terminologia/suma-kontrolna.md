# Suma kontrolna

## Definicja

Suma kontrolna (checksum) jest krótką wartością obliczoną z zawartości pliku, używaną do wykrywania zmian lub uszkodzeń.

## Znaczenie w `piper-mat`

Projekt zapisuje SHA-256 punktów kontrolnych, metadanych, podziałów i modeli. Dwa identyczne skróty pozwalają z dużą pewnością stwierdzić, że użyto tych samych bajtów.

## Co zmienia w praktyce

SHA-256 ma 64 znaki szesnastkowe. Zmiana jednego bajtu daje inną wartość. Suma potwierdza integralność, lecz sama nie potwierdza jakości, pochodzenia ani bezpieczeństwa pliku.

## Przykład z repozytorium

`python scripts/verify_checkpoint.py checkpoints/base.ckpt` porównuje plik z manifestem projektu.

## Typowe błędy interpretacyjne

Nazwa iwanie SHA-256 szyfrowaniem lub podpisem cyfrowym jest błędem. Zgodna nazwa pliku nie zastępuje zgodnej sumy.

## Powiązane artykuły i procedury

[Punkt kontrolny](punkt-kontrolny.md), [wydanie](wydanie.md), [punkty kontrolne](../CHECKPOINTS.md).
