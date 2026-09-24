"""Pinyin-based phonemization for Chinese using g2pW.

Partially written by ChatGPT (December 2025).

This code is Apache 2.0 licensed.
"""

import hashlib
import logging
import os
import posixpath
import re
import shutil
import tarfile
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Optional, Union
from urllib.request import urlopen

from unicode_rbnf import RbnfEngine

from .const import BOS, EOS, PAD
from .g2pw_onnx import G2PWOnnxConverter
from .phoneme_ids import DEFAULT_PHONEME_ID_MAP

_LOGGER = logging.getLogger(__name__)

# NOTE: Must be sorted longest to shortest
PINYIN_INITIALS = [
    "zh",
    "ch",
    "sh",
    "b",
    "p",
    "m",
    "f",
    "d",
    "t",
    "n",
    "l",
    "g",
    "k",
    "h",
    "j",
    "q",
    "x",
    "r",
    "z",
    "c",
    "s",
    "y",
    "w",
]

PHONEME_TO_ID: dict[str, list[int]] = {
    PAD: DEFAULT_PHONEME_ID_MAP[PAD],
    BOS: DEFAULT_PHONEME_ID_MAP[BOS],
    EOS: DEFAULT_PHONEME_ID_MAP[EOS],
    # --------------------
    # Initials (24)
    # --------------------
    "Ø": [3],  # zero initial
    "b": [4],
    "p": [5],
    "m": [6],
    "f": [7],
    "d": [8],
    "t": [9],
    "n": [10],
    "l": [11],
    "g": [12],
    "k": [13],
    "h": [14],
    "j": [15],
    "q": [16],
    "x": [17],
    "zh": [18],
    "ch": [19],
    "sh": [20],
    "r": [21],
    "z": [22],
    "c": [23],
    "s": [24],
    "y": [25],
    "w": [26],
    # --------------------
    # Finals (35)
    # --------------------
    "a": [27],
    "o": [28],
    "e": [29],
    "ai": [30],
    "ei": [31],
    "ao": [32],
    "ou": [33],
    "an": [34],
    "en": [35],
    "ang": [36],
    "eng": [37],
    "ong": [38],
    # i-family
    "i": [39],
    "ia": [40],
    "ie": [41],
    "iao": [42],
    "iu": [43],
    "ian": [44],
    "in": [45],
    "iang": [46],
    "ing": [47],
    "iong": [48],
    # u-family
    "u": [49],
    "ua": [50],
    "uo": [51],
    "uai": [52],
    "ui": [53],
    "uan": [54],
    "un": [55],
    "uang": [56],
    "ueng": [57],
    # ü-family (ASCII-friendly ü → v)
    "v": [58],  # ü
    "ve": [59],  # üe
    "van": [60],  # üan
    "vn": [61],  # ün
    # “er” syllable final
    "er": [62],
    # extra non-erhua final
    "ue": [63],
    # --------------------
    # Tones (5)
    # --------------------
    "1": [64],
    "2": [65],
    "3": [66],
    "4": [67],
    "5": [68],  # neutral tone
    # --------------------
    # Long pauses
    # --------------------
    "。": [69],  # different ids for intonation
    ".": [69],
    "？": [70],
    "?": [70],
    "！": [71],
    "!": [71],
    # --------------------
    # Short pauses
    # --------------------
    "—": [72],  # same id
    "…": [72],
    "、": [72],
    "，": [72],
    ",": [72],
    "：": [72],
    ":": [72],
    "；": [72],
    ";": [72],
    # space
    " ": [72],
}

GROUP_END_PHONEMES = {
    # tones
    "1",
    "2",
    "3",
    "4",
    "5",
    # full-width long pauses
    "。",
    "？",
    "！",
    # half-width long pauses
    ".",
    "?",
    "!",
    # full-width short pauses
    "—",
    "…",
    "、",
    "，",
    "：",
    "；",
    # half-width short pauses
    ",",
    ":",
    ";",
    # space
    " ",
}

G2PW_URL = "https://huggingface.co/datasets/rhasspy/piper-checkpoints/resolve/main/zh/zh_CN/_resources/g2pw.tar.gz?download=true"
G2PW_SHA256 = "9137f37d8e15ab1fd04a448bfe9805e00c94db833786735f672d63a44fddc8dd"
G2PW_REQUIRED_FILES = (
    "g2pw.onnx",
    "config.py",
    "POLYPHONIC_CHARS.txt",
    "MONOPHONIC_CHARS.txt",
)

TEMP_PATTERN = re.compile(
    r"(?P<sign>[-−])?(?P<num>\d+)\s*(?:°\s*C|℃)",  # handles "-7°C", "7℃", "−3°C"
)

# 98.76% / -7% / 77％
# 九十八点七六% / 七十七％
PERCENT_PATTERN = re.compile(
    r"(?P<num>-?\d+(?:\.\d+)?|[零〇一二三四五六七八九十百千万亿两点]+)\s*(?:%|％)"
)


class ChinesePhonemizer:
    """Phonemize Chinese text using g2pW."""

    def __init__(self, model_dir: Union[str, Path]) -> None:
        """Initialize phonemizer."""

        # Ensure model is downloaded
        download_model(model_dir)

        self.g2p = G2PWOnnxConverter(
            model_dir=model_dir, style="pinyin", enable_non_tradional_chinese=True
        )
        self.number_engine = RbnfEngine.for_language("zh")

    def phonemize(self, text: str) -> list[list[str]]:
        """Turn text into phonemes per sentence."""
        from sentence_stream import stream_to_sentences

        text = re.sub('[“”"]', "", text)

        all_phonemes: list[list[str]] = []

        for sentence in stream_to_sentences([text]):
            sentence = self._numbers_to_words(sentence)
            sylls = self.g2p(sentence)[0]
            sentence_phonemes = []
            for syl, syl_char in zip(sylls, sentence):
                if syl is None:
                    # Punctuation
                    if syl_char in PHONEME_TO_ID:
                        sentence_phonemes.append(syl_char)

                    continue

                syl = _normalize_g2pw_syllable(syl)
                ini_p, fin_p, tone = _split_initial_final_tone(syl)
                if not fin_p:
                    # Not a normal pinyin syllable
                    sentence_phonemes.append(syl)
                    continue

                if not ini_p:
                    ini_p = "Ø"

                for sym in (ini_p, fin_p, tone):
                    assert sym, sym
                    sentence_phonemes.append(sym)

            all_phonemes.append(sentence_phonemes)

        return all_phonemes

    def _numbers_to_words(self, text: str) -> str:
        # TODO: dates/times/ordinals

        # 1) Temperatures: -7°C → 零下七度; 7°C → 七度
        def replace_temp(m: re.Match) -> str:
            sign = m.group("sign")
            num_str = m.group("num")
            # use absolute value for words, we handle sign ourselves
            num_words = self._zh_number(num_str)

            if sign:
                # For temperatures, "零下" is more natural than "负"
                return f"零下{num_words}度"

            return f"{num_words}度"

        text = TEMP_PATTERN.sub(replace_temp, text)

        # 2) Percentages: 77% → 百分之七十七
        def replace_percent(m: re.Match) -> str:
            num_str = m.group("num")
            if re.fullmatch(r"-?\d+(?:\.\d+)?", num_str):
                # Expand digits
                num_words = self._zh_number(num_str)
            else:
                num_words = num_str

            return f"百分之{num_words}"

        text = PERCENT_PATTERN.sub(replace_percent, text)

        return re.sub(
            r"-?\d+(?:\.\d+)?",
            lambda m: self._zh_number(m.group(0)),
            text,
        )

    def _zh_number(self, text: str) -> str:
        return self.number_engine.format_number(text).text


def phonemes_to_ids(
    phonemes: list[str],
    id_map: Optional[Mapping[str, Sequence[int]]] = None,
) -> list[int]:
    """Get phoneme ids for phonemes.

    Padding is done after a group of phonemes representing one pinyin group
    instead of between each phoneme.
    """
    if not id_map:
        id_map = PHONEME_TO_ID

    ids: list[int] = []
    ids.extend(id_map[BOS])

    for phoneme in phonemes:
        if phoneme not in id_map:
            _LOGGER.warning("Missing phoneme from id map: %s", phoneme)
            continue

        ids.extend(id_map[phoneme])

        # pad after group
        if phoneme in GROUP_END_PHONEMES:
            ids.extend(id_map[PAD])

    ids.extend(id_map[EOS])

    return ids


def _normalize_g2pw_syllable(syl: str) -> str:
    """
    - Keep only syllables like [a-züv:]+[1-5]
    - Convert g2pW's 'u:' and 'ü' -> 'v' (ü-family)
      nu:3   -> nv3        (n + v)
      lu:e4  -> lve4       (l + ve)
      ju:an3 -> jvan3      (j + van)
      ju:n3  -> jvn3       (j + vn)
    """
    m = re.match(r"^([a-züv:]+?)([1-5])$", syl)
    if not m:
        return syl

    base, tone = m.group(1), m.group(2)

    # Normalize ü-family to ASCII-friendly 'v'
    base = base.replace("u:", "v").replace("ü", "v")

    return base + tone


def _split_initial_final_tone(syl: str):
    """
    'hang2' -> ('h', 'ang', '2')
    'ai3'   -> ('', 'ai', '3')
    """
    m = re.match(r"^([a-zvü]+?)([1-5])$", syl)
    if not m:
        return "", "", None

    base, tone = m.group(1), m.group(2)

    ini = ""
    for cand in PINYIN_INITIALS:
        if base.startswith(cand):
            ini = cand
            break

    fin = base[len(ini) :] if ini else base
    return ini, fin, tone


def _validate_archive(members: Sequence[tarfile.TarInfo]) -> None:
    """Validate every archive member before extraction."""
    symlinks = set()
    for member in members:
        name = member.name
        archive_path = PurePosixPath(name.replace("\\", "/"))
        if (
            name in ("", ".")
            or "\\" in name
            or archive_path.is_absolute()
            or PureWindowsPath(name).is_absolute()
            or ".." in archive_path.parts
        ):
            raise ValueError(f"Unsafe path in g2pW archive: {name!r}")
        if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
            raise ValueError(f"Special file in g2pW archive: {name!r}")

        if member.issym():
            symlinks.add(name.rstrip("/"))
            target = posixpath.normpath(
                posixpath.join(posixpath.dirname(name), member.linkname)
            )
            if (
                PureWindowsPath(member.linkname).is_absolute()
                or "\\" in member.linkname
                or member.linkname.startswith("/")
                or target == ".."
                or target.startswith("../")
            ):
                raise ValueError(f"Unsafe link in g2pW archive: {name!r}")
        elif member.islnk():
            target = posixpath.normpath(member.linkname)
            if (
                PureWindowsPath(member.linkname).is_absolute()
                or "\\" in member.linkname
                or member.linkname.startswith("/")
                or target == ".."
                or target.startswith("../")
            ):
                raise ValueError(f"Unsafe link in g2pW archive: {name!r}")

    for member in members:
        parents = Path(member.name).parents
        if any(parent.as_posix() in symlinks for parent in parents):
            raise ValueError(f"Archive path traverses a symbolic link: {member.name!r}")


def _extract_archive(archive_path: Path, destination: Path) -> None:
    """Extract a prevalidated model archive."""
    with tarfile.open(archive_path, mode="r:gz") as archive:
        members = archive.getmembers()
        _validate_archive(members)
        if hasattr(tarfile, "data_filter"):
            archive.extractall(destination, members=members, filter="data")
        else:
            archive.extractall(destination, members=members)


def download_model(model_dir: Union[str, Path]) -> None:
    """Download, validate, and atomically install the g2pW model."""
    model_dir = Path(model_dir)
    model_path = model_dir / "g2pw.onnx"

    if model_path.exists():
        # Already downloaded
        _LOGGER.debug("Found g2pW model at %s", model_path)
        return

    _LOGGER.info("Downloading g2pW model from '%s' to '%s'", G2PW_URL, model_dir)
    model_dir.parent.mkdir(parents=True, exist_ok=True)
    archive_file = tempfile.NamedTemporaryFile(
        prefix=f".{model_dir.name}-",
        suffix=".tar.gz",
        dir=model_dir.parent,
        delete=False,
    )
    archive_path = Path(archive_file.name)
    temporary_dir = Path(
        tempfile.mkdtemp(prefix=f".{model_dir.name}-", dir=model_dir.parent)
    )
    try:
        digest = hashlib.sha256()
        with archive_file, urlopen(G2PW_URL) as response:
            while chunk := response.read(1024 * 1024):
                archive_file.write(chunk)
                digest.update(chunk)
        if digest.hexdigest() != G2PW_SHA256:
            raise ValueError("Downloaded g2pW archive has an invalid SHA-256 checksum")

        _extract_archive(archive_path, temporary_dir)
        missing = [
            file_name
            for file_name in G2PW_REQUIRED_FILES
            if not (temporary_dir / file_name).is_file()
        ]
        if missing:
            raise ValueError(f"g2pW archive is missing required files: {missing}")
        if model_dir.exists():
            backup_dir = temporary_dir.with_name(f"{temporary_dir.name}.old")
            os.replace(model_dir, backup_dir)
            try:
                os.replace(temporary_dir, model_dir)
            except BaseException:
                os.replace(backup_dir, model_dir)
                raise
            shutil.rmtree(backup_dir)
        else:
            os.replace(temporary_dir, model_dir)
    finally:
        archive_path.unlink(missing_ok=True)
        shutil.rmtree(temporary_dir, ignore_errors=True)
