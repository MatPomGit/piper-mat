# Checkpointy bazowe

Checkpointy treningowe są dużymi artefaktami i nie powinny być traktowane jak zwykłe pliki źródłowe.

## Manifest

Plik `checkpoints/manifest.json` zapisuje nazwę, rozmiar i SHA-256 znanych checkpointów. Dla aktualnego `base.ckpt` identyfikator Git LFS wskazuje SHA-256:

`ab7e5b8dab40f834b7cc58ae4ad7b7009c954b901e4ddbb784bbe11ce379a1cd`

oraz rozmiar 845898328 bajtów.

Integralność można sprawdzić poleceniem:

```bash
python scripts/verify_checkpoint.py checkpoints/base.ckpt
```

Skrypt rozpoznaje zarówno rzeczywisty plik checkpointu, jak i wskaźnik Git LFS.

## Dalsze porządkowanie

Przed usunięciem checkpointów z Git LFS należy:

1. ustalić ich pierwotne źródło,
2. wpisać stabilny URL do `checkpoints/manifest.json`,
3. zweryfikować SHA-256 pobranego pliku,
4. potwierdzić, który checkpoint jest rzeczywiście używany do treningu produkcyjnego,
5. usunąć niepotrzebne warianty `base_clean`, `base_fixed` i `base_win`, jeśli nie są już wymagane.

Nie należy wpisywać URL źródłowego na podstawie przypuszczenia. Manifest ma odzwierciedlać zweryfikowane pochodzenie artefaktu.
