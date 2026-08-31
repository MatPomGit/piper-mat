# Model głosu

Kanoniczna karta modelu znajduje się w `models/pl_PL-mateusz-medium/MODEL_CARD.md`.

## Warunki uznania modelu za gotowy

Finalny model powinien mieć:

- parę `pl_PL-mateusz-medium.onnx` i `pl_PL-mateusz-medium.onnx.json`,
- pozytywny smoke test syntezy,
- wyniki WER i CER na zamrożonym korpusie,
- wynik speaker similarity,
- co najmniej podstawową ocenę odsłuchową MOS lub CMOS,
- benchmark RTF, latencji i zużycia pamięci,
- jednoznacznie opisaną licencję i pochodzenie danych,
- SHA-256 każdego publikowanego artefaktu.

Do momentu wykonania pomiarów pola wynikowe w `MODEL_CARD.md` powinny pozostać oznaczone jako `TODO`, zamiast zawierać wartości szacunkowe.
