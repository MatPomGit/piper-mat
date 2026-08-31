# Bazowe punkty kontrolne

Punkty kontrolne treningu są dużymi artefaktami i nie powinny być traktowane jak zwykłe pliki źródłowe.

## Manifest

Plik `checkpoints/manifest.json` zapisuje nazwę, rozmiar i SHA-256 znanych punktów kontrolnych. Dla aktualnego `base.ckpt` identyfikator Git LFS wskazuje SHA-256:

`ab7e5b8dab40f834b7cc58ae4ad7b7009c954b901e4ddbb784bbe11ce379a1cd`

oraz rozmiar 845898328 bajtów.

Integralność można sprawdzić poleceniem:

```bash
python scripts/verify_checkpoint.py checkpoints/base.ckpt
```

Skrypt rozpoznaje zarówno rzeczywisty plik punktu kontrolnego, jak i wskaźnik Git LFS.

## Dalsze porządkowanie

Przed usunięciem punktów kontrolnych z Git LFS należy:

1. ustalić ich pierwotne źródło,
2. wpisać stabilny adres URL do `checkpoints/manifest.json`,
3. zweryfikować SHA-256 pobranego pliku,
4. potwierdzić, który punkt kontrolny jest rzeczywiście używany do treningu produkcyjnego,
5. usunąć niepotrzebne warianty `base_clean`, `base_fixed` i `base_win`, jeśli nie są już wymagane.

Nie należy wpisywać adresu URL źródłowego na podstawie przypuszczenia. Manifest ma odzwierciedlać zweryfikowane pochodzenie artefaktu.
