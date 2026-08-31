# 🗣️ Głosy

[Posłuchaj próbek głosów](https://rhasspy.github.io/piper-samples)

[Pobierz głosy](https://huggingface.co/rhasspy/piper-voices/tree/main)

Obsługiwane języki:

* <span dir="rtl">العربية</span>, Jordania (arabski, ar_JO)
* Català, Hiszpania (kataloński, ca_ES)
* Čeština, Czechy (czeski, cs_CZ)
* Cymraeg, Wielka Brytania (walijski, cy_GB)
* Dansk, Dania (duński, da_DK)
* Deutsch, Niemcy (niemiecki, de_DE)
* Ελληνικά, Grecja (grecki, el_GR)
* English, Wielka Brytania (angielski, en_GB)
* English, Stany Zjednoczone (angielski, en_US)
* Español, Argentyna (hiszpański, es_AR)
* Español, Hiszpania (hiszpański, es_ES)
* Español, Meksyk (hiszpański, es_MX)
* <span dir="rtl">فارسی</span>, Iran (perski, fa_IR)
* Suomi, Finlandia (fiński, fi_FI)
* Français, Francja (francuski, fr_FR)
* Magyar, Węgry (węgierski, hu_HU)
* íslenska, Islandia (islandzki, is_IS)
* Bahasa Indonesia, Indonezja (indonezyjski, id_ID)
* Italiano, Włochy (włoski, it_IT)
* ქართული ენა, Gruzja (gruziński, ka_GE)
* қазақша, Kazachstan (kazachski, kk_KZ)
* Lëtzebuergesch, Luksemburg (luksemburski, lb_LU)
* Latviešu, Łotwa (łotewski, lv_LV)
* മലയാളം, Indie (malajalam, ml_IN)
* हिंदी, Indie (hindi, hi_IN)
* नेपाली, Nepal (nepalski, ne_NP)
* Nederlands, Belgia (niderlandzki, nl_BE)
* Nederlands, Holandia (niderlandzki, nl_NL)
* Norsk, Norwegia (norweski, no_NO)
* Polski, Polska (polski, pl_PL)
* Português, Brazylia (portugalski, pt_BR)
* Português, Portugalia (portugalski, pt_PT)
* Română, Rumunia (rumuński, ro_RO)
* Русский, Rosja (rosyjski, ru_RU)
* Slovenčina, Słowacja (słowacki, sk_SK)
* Slovenščina, Słowenia (słoweński, sl_SI)
* srpski, Serbia (serbski, sr_RS)
* Svenska, Szwecja (szwedzki, sv_SE)
* Kiswahili, Demokratyczna Republika Konga (suahili, sw_CD)
* తెలుగు, Indie (telugu, te_IN)
* Türkçe, Turcja (turecki, tr_TR)
* украї́нська мо́ва, Ukraina (ukraiński, uk_UA)
* Tiếng Việt, Wietnam (wietnamski, vi_VN)
* 简体中文, Chiny (chiński, zh_CN)

## Modele

Głosy są trenowane za pomocą [VITS](https://github.com/jaywalnut310/vits/) i eksportowane do [onnxruntime](https://onnxruntime.ai/).
Dla każdego głosu potrzebne są dwa pliki:

1. Plik modelu `.onnx`, na przykład [`en_US-lessac-medium.onnx`](https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx)
2. Plik konfiguracji `.onnx.json`, na przykład [`en_US-lessac-medium.onnx.json`](https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json)

Plik `MODEL_CARD` każdego głosu zawiera ważne informacje licencyjne. Piper jest przeznaczony wyłącznie do użytku osobistego i badań nad syntezą mowy; nie nakładamy żadnych dodatkowych ograniczeń na modele głosów. Niektóre głosy mogą jednak podlegać restrykcyjnym licencjom, dlatego należy je uważnie sprawdzić!
