# Próbki głosu

Katalog przeznaczony jest na krótkie próbki referencyjne i syntetyczne używane do jakościowego porównywania wersji głosu.

Docelowa struktura:

```text
samples/
└── pl_PL-mateusz-medium/
    ├── README.md
    ├── sample_01.wav
    ├── sample_02.wav
    └── sample_03.wav
```

Próbki powinny używać stałego zestawu zdań obejmującego typową polszczyznę, liczby, daty, skróty, nazwy własne i trudniejsze zbitki fonetyczne. Ten sam zestaw należy zachowywać między wydaniami, aby ułatwić odsłuchowe porównanie modeli.

Nie należy przechowywać w Git dużej liczby wygenerowanych plików audio. Pełne zestawy porównawcze powinny być dołączane do wydań.
