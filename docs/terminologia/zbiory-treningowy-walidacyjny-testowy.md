# Zbiory treningowy, walidacyjny i testowy

## Definicja

Zbiór treningowy (training set) aktualizuje parametry, zbiór walidacyjny (validation set) pomaga wybierać ustawienia i punkt kontrolny, a zbiór testowy (test set) służy do końcowej oceny.

## Znaczenie w `piper-mat`

Rozdzielenie ról ogranicza ryzyko, że model zostanie oceniony na wypowiedziach, które wcześniej wykorzystano do jego ulepszania.

## Co zmienia w praktyce

Przykładowy podział 1000 wypowiedzi może obejmować 800 treningowych, 100 walidacyjnych i 100 testowych. Stosuje się też proporcje `90/5/5` lub `80/10/10`; właściwy wybór zależy od wielkości danych. Raz ustalony podział porównań należy zamrozić.

## Przykład z repozytorium

`python scripts/create_splits.py --metadata dataset/metadata.csv --output dataset/splits.json --seed 20260831` tworzy podział projektu.

## Typowe błędy interpretacyjne

Zbiór walidacyjny nie jest dodatkowym zbiorem treningowym. Wielokrotne wybieranie według testu powoduje, że przestaje on być niezależną oceną.

## Powiązane artykuły i procedury

[Podział zbioru](podzial-zbioru-danych.md), [zbiór danych](zbior-danych.md), [procedura danych](../DATASET.md).
