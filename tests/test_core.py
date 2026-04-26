"""
tests/test_core.py - Tests unitaires de validation de VoiceLingo.
Auteur: Mouhamadou Lamine Niang (2026) - mouhamedlniang@gmail.com
Lancement : python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest


# Tests du module srt_generator

class TestSRTTimestamps:

    def test_zero_seconds(self):
        from srt_generator import _to_srt_time
        assert _to_srt_time(0.0) == "00:00:00,000"

    def test_one_hour(self):
        from srt_generator import _to_srt_time
        assert _to_srt_time(3661.5) == "01:01:01,500"

    def test_max_duration(self):
        from srt_generator import _to_srt_time
        assert _to_srt_time(86399.999) == "23:59:59,999"

    def test_negative_clamped_to_zero(self):
        from srt_generator import _to_srt_time
        assert _to_srt_time(-1.0) == "00:00:00,000"


class TestWordSegmentation:

    def _make_words(self, texts_and_times):
        """Cree une liste de mots pour les tests."""
        return [
            {"word": t, "start": s, "end": e}
            for t, s, e in texts_and_times
        ]

    def test_basic_segmentation(self):
        from srt_generator import words_to_segments
        words = self._make_words([
            ("Hello", 0.0, 0.5),
            ("world", 0.6, 1.0),
            ("this", 2.0, 2.3),   # pause > 0.35s -> nouveau segment
            ("is", 2.4, 2.6),
            ("Python.", 2.7, 3.0),
        ])
        segments = words_to_segments(words)
        assert len(segments) >= 2, "pause > 0.35s doit creer une coupure"

    def test_empty_words(self):
        from srt_generator import words_to_segments
        assert words_to_segments([]) == []

    def test_no_negative_timestamps(self):
        from srt_generator import words_to_segments
        words = self._make_words([
            ("hello", 0.0, 0.5),
            ("world", 0.6, 1.0),
        ])
        segments = words_to_segments(words)
        for seg in segments:
            assert seg["start"] >= 0, f"start negatif : {seg}"
            assert seg["end"] >= 0, f"end negatif : {seg}"
            assert seg["start"] < seg["end"], f"start >= end : {seg}"

    def test_min_duration_respected(self):
        from srt_generator import words_to_segments, MIN_DURATION
        words = self._make_words([("hi", 0.0, 0.1)])  # duree < MIN_DURATION
        segments = words_to_segments(words)
        if segments:
            assert segments[0]["end"] - segments[0]["start"] >= MIN_DURATION - 0.001


class TestSRTValidation:

    def test_validate_valid_srt(self, tmp_path):
        from srt_generator import validate_srt
        srt = tmp_path / "test.srt"
        srt.write_text(
            "1\n00:00:01,000 --> 00:00:03,000\nBonjour le monde\n\n"
            "2\n00:00:04,000 --> 00:00:06,000\nComment allez-vous\n\n",
            encoding="utf-8-sig",
        )
        errors = validate_srt(str(srt))
        assert errors == [], f"SRT valide signale des erreurs : {errors}"

    def test_validate_invalid_timestamp(self, tmp_path):
        from srt_generator import validate_srt
        srt = tmp_path / "bad.srt"
        srt.write_text(
            "1\n00:00:05,000 --> 00:00:03,000\nTimestamp inverse\n\n",
            encoding="utf-8-sig",
        )
        errors = validate_srt(str(srt))
        assert len(errors) > 0, "SRT invalide devrait signaler une erreur"


# Tests du module context_translation_ia

class TestDomainDetection:

    def test_informatique_detection(self):
        from context_translation_ia import detect_domain
        text = """
        In this Python tutorial we learn about functions, classes, loops,
        Docker containers, API endpoints, HTTP requests, JSON responses,
        machine learning gradient descent and neural networks.
        """
        domain = detect_domain(text)
        assert domain == "informatique", f"Attendu 'informatique', obtenu '{domain}'"

    def test_empty_text_returns_general(self):
        from context_translation_ia import detect_domain
        assert detect_domain("") == "general"

    def test_no_keywords_returns_general(self):
        from context_translation_ia import detect_domain
        domain = detect_domain("bonjour comment allez vous aujourd hui")
        assert domain == "general"


class TestTermProtection:

    def test_function_protected(self):
        from context_translation_ia import (
            get_glossary, protect_terms, restore_terms
        )
        glossary = get_glossary("informatique", "fr")
        text = "use a function with async callback"
        protected, tokens = protect_terms(text, glossary)
        assert "function" not in protected or "__TK" in protected
        restored = restore_terms(protected, tokens)
        assert "function" in restored.lower()

    def test_restore_exact(self):
        from context_translation_ia import (
            get_glossary, protect_terms, restore_terms
        )
        glossary = get_glossary("informatique", "fr")
        text = "Python and Docker"
        protected, tokens = protect_terms(text, glossary)
        restored = restore_terms(protected, tokens)
        assert "Python" in restored or "python" in restored.lower()

    def test_no_stray_tokens_after_restore(self):
        from context_translation_ia import (
            get_glossary, protect_terms, restore_terms
        )
        import re
        glossary = get_glossary("informatique", "fr")
        text = "use a function and a loop"
        protected, tokens = protect_terms(text, glossary)
        restored = restore_terms(protected, tokens)
        stray = re.findall(r"__TK\d+__", restored)
        assert stray == [], f"tokens residuels : {stray}"


# Tests du module config_manager

class TestConfigValidation:

    def test_invalid_whisper_model_uses_default(self, tmp_path, monkeypatch):
        import json
        from config_manager import DEFAULTS

        bad_config = {
            "whisper_model_size": "invalid_model",
            "whisper_device":     "cpu",
            "whisper_compute_type": "int8",
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(bad_config))

        monkeypatch.setattr("config_manager.CONFIG_PATH", config_file)
        from config_manager import load_config
        config = load_config()

        assert config["whisper_model_size"] == DEFAULTS["whisper_model_size"], \
            "valeur invalide doit utiliser le defaut"

    def test_valid_config_loaded(self, tmp_path, monkeypatch):
        import json
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "whisper_model_size": "medium",
            "whisper_device": "cpu",
            "whisper_compute_type": "int8",
        }))
        monkeypatch.setattr("config_manager.CONFIG_PATH", config_file)
        from config_manager import load_config
        config = load_config()
        assert config["whisper_model_size"] == "medium"


# Tests du module video_handler

class TestDiskSpaceCheck:

    def test_returns_dict_with_required_keys(self, tmp_path):
        fake_video = tmp_path / "video.mp4"
        fake_video.write_bytes(b"0" * 1024 * 1024)  # 1 Mo

        from video_handler import check_disk_space
        result = check_disk_space(str(fake_video), str(tmp_path))

        assert "ok" in result
        assert "needed_gb" in result
        assert "available_gb" in result
        assert isinstance(result["ok"], bool)
        assert result["needed_gb"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
