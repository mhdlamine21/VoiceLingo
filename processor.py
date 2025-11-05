"""
processor.py - Orchestrateur du pipeline de traitement multimedia VoiceLingo.
Auteur: Mouhamadou Lamine Niang (2026) - mouhamedlniang@gmail.com
Description: Coordonne l'analyse, l'extraction audio, la transcription Whisper,
             la traduction NLLB avec conservation du contexte technique,
             la generation des sous-titres SRT et le doublage vocal eventuel.
             Le traitement est execute dans un thread d'arriere-plan dedie afin
             de maintenir la reactivite complete de l'interface graphique.
"""

import os
import threading
import tempfile


class ProcessingPipeline:
    """
    Gestionnaire d'orchestration pour le flux de travail de traduction video.
    Assure le suivi de la progression et la possibilite d'interruption a tout moment.
    """

    def __init__(self, config=None):
        self.config = config or {}
        self._annuler = threading.Event()

    def run(self, video_path, src_lang, tgt_lang, output_mode,
            output_dir, burn_subs, progress_cb, done_cb):
        """
        Lance le pipeline dans un thread daemon pour ne pas bloquer le thread principal.
        """
        thread = threading.Thread(
            target=self._executer,
            args=(video_path, src_lang, tgt_lang, output_mode,
                  output_dir, burn_subs, progress_cb, done_cb),
            daemon=True
        )
        thread.start()

    def cancel(self):
        """Notifie le pipeline d'arreter immediatement les operations en cours."""
        self._annuler.set()

    def _verifier_annulation(self):
        """Verifie si l'utilisateur a demande l'arret du processus."""
        if self._annuler.is_set():
            raise InterruptedError("Traitement interrompu par l'utilisateur.")

    def _progression(self, callback, pourcent, message):
        """Transmet l'avancement numerique et textuel a la fonction de rappel."""
        if callback:
            callback(pourcent, message)

    def _executer(self, video_path, src_lang, tgt_lang, output_mode,
                  output_dir, burn_subs, progress_cb, done_cb):
        """
        Sequence d'execution etape par etape :
        Etape 1: Verifications de coherence et d'espace disque disponible
        Etape 2: Extraction audio via FFmpeg
        Etape 3: Transcription vocale Whisper
        Etape 4: Segmentation SRT avec regles de pauses et de ponctuation
        Etape 5: Traduction neuronale NLLB avec protection des termes techniques
        Etape 6: Generation et validation du fichier SRT conforme UTF-8 BOM
        Etape 7: Finalisation (incrustation video ou synthese vocale selon le mode)
        """
        fichier_audio_temp = None

        try:
            # Etape 1: Verifications preliminaires
            self._progression(progress_cb, 2, "Analyse video...")
            self._verifier_annulation()

            from video_handler import (
                get_video_info, check_has_audio,
                check_disk_space, extract_audio
            )

            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Le fichier video specifie est introuvable : {video_path}")

            if not check_has_audio(video_path):
                raise ValueError("Aucune piste audio n'a ete detectee dans cette video.")

            espace = check_disk_space(video_path, output_dir)
            if not espace["ok"]:
                raise ValueError(
                    f"Espace disque insuffisant dans le repertoire de destination.\n"
                    f"Espace requis : {espace['necessaire_mo']} Mo\n"
                    f"Espace disponible : {espace['disponible_mo']} Mo"
                )

            self._progression(progress_cb, 5, "Analyse video terminee")

            # Etape 2: Extraction du signal audio
            self._verifier_annulation()
            self._progression(progress_cb, 6, "Extraction audio...")

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                fichier_audio_temp = f.name

            extract_audio(video_path, fichier_audio_temp)
            self._progression(progress_cb, 20, "Audio extrait")

            # Etape 3: Transcription Whisper
            self._verifier_annulation()
            self._progression(progress_cb, 21, "Transcription Whisper en cours...")

            from speech_to_text import transcribe
            texte, langue_detectee, mots = transcribe(
                fichier_audio_temp,
                langue_src=src_lang,
                config=self.config,
                progress_cb=progress_cb
            )

            self._progression(progress_cb, 40, "Transcription terminee")

            # Etape 4: Decoupage en segments SRT
            self._verifier_annulation()
            self._progression(progress_cb, 41, "Creation des segments SRT...")

            from srt_generator import words_to_segments, generate_srt, validate_srt
            segments = words_to_segments(mots)

            self._progression(progress_cb, 45, f"{len(segments)} segments crees")

            # Etape 5: Traduction neuronale NLLB avec conservation du vocabulaire technique
            self._verifier_annulation()
            self._progression(progress_cb, 46, "Traduction en cours...")

            from context_translation_ia import translate_segments_batch, detect_domain
            domaine = detect_domain(texte)
            self._progression(
                progress_cb, 47,
                f"Traduction [{domaine}] en cours..."
            )

            segments_traduits = translate_segments_batch(
                segments,
                langue_src=langue_detectee if src_lang == "auto" else src_lang,
                langue_cible=tgt_lang,
                config=self.config,
                progress_cb=progress_cb
            )

            self._progression(progress_cb, 62, "Traduction terminee")

            # Etape 6: Production du fichier SRT
            self._verifier_annulation()
            self._progression(progress_cb, 63, "Generation du fichier SRT...")

            nom_video = os.path.splitext(os.path.basename(video_path))[0]
            nom_fichier_srt = f"{nom_video}_{tgt_lang}.srt"
            chemin_srt = os.path.join(output_dir, nom_fichier_srt)

            generate_srt(segments_traduits, chemin_srt)

            erreurs_srt = validate_srt(chemin_srt)
            if erreurs_srt:
                print(f"Avertissement validation SRT : {erreurs_srt}")

            self._progression(progress_cb, 78, "Fichier SRT genere")

            # Etape 7: Finalisation en fonction du mode selectionne
            self._verifier_annulation()

            if output_mode == "srt":
                if burn_subs:
                    self._progression(progress_cb, 80, "Incrustation des sous-titres...")
                    from video_handler import burn_subtitles
                    nom_video_out = f"{nom_video}_{tgt_lang}_sous_titres.mp4"
                    chemin_video_out = os.path.join(output_dir, nom_video_out)
                    burn_subtitles(video_path, chemin_srt, chemin_video_out)
                    self._progression(progress_cb, 100, "Termine !")
                    done_cb(True, chemin_video_out)
                else:
                    self._progression(progress_cb, 100, "Termine !")
                    done_cb(True, chemin_srt)

            elif output_mode == "dub":
                self._progression(progress_cb, 80, "Synthese vocale en cours...")
                from text_to_speech import synthesize_speech
                from video_handler import replace_audio_track

                nom_audio = f"{nom_video}_{tgt_lang}_audio.wav"
                chemin_audio_traduit = os.path.join(output_dir, nom_audio)

                synthesize_speech(
                    segments_traduits,
                    tgt_lang,
                    chemin_audio_traduit,
                    self.config
                )

                self._progression(progress_cb, 92, "Assemblage de la video...")

                nom_video_out = f"{nom_video}_{tgt_lang}_double.mp4"
                chemin_video_out = os.path.join(output_dir, nom_video_out)
                replace_audio_track(video_path, chemin_audio_traduit, chemin_video_out)

                if os.path.exists(chemin_audio_traduit):
                    try:
                        os.remove(chemin_audio_traduit)
                    except OSError:
                        pass

                self._progression(progress_cb, 100, "Termine !")
                done_cb(True, chemin_video_out)

        except InterruptedError:
            done_cb(False, "Traitement annule par l'utilisateur.")

        except Exception as erreur:
            print(f"Erreur durant l'execution du pipeline : {erreur}")
            import traceback
            traceback.print_exc()
            done_cb(False, str(erreur))

        finally:
            if fichier_audio_temp and os.path.exists(fichier_audio_temp):
                try:
                    os.remove(fichier_audio_temp)
                except OSError:
                    pass
