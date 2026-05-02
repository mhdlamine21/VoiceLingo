"""
main_api.py - Interface de programmation applicative REST (FastAPI) pour VoiceLingo.
Auteur: Mouhamadou Lamine Niang (2026) - mouhamedlniang@gmail.com
Description: Permet de piloter la transcription, la traduction et le doublage vocal a distance
             ou d'integrer le moteur VoiceLingo dans d'autres applications clientes.

Lancement : uvicorn main_api:app --host 0.0.0.0 --port 8000
Documentation Swagger : http://localhost:8000/docs
"""

import os
import uuid
import time
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from config_manager import load_config
from processor import ProcessingPipeline

app = FastAPI(
    title="VoiceLingo API",
    description="API REST locale pour la transcription et traduction video contextuelle.",
    version="1.0.0",
)

# Registre en memoire pour le suivi asynchrone des jobs
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


# Modeles de requetes et reponses Pydantic

class ProcessVideoRequest(BaseModel):
    video_path: str
    language_source: str = "auto"
    language_target: str = "fr"
    mode: str = "srt"                   # "srt" ou "dub"
    output_dir: Optional[str] = None
    detect_theme: bool = True
    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    nllb_model: str = "facebook/nllb-200-distilled-600M"
    burn_subtitles: bool = False


class JobStatus(BaseModel):
    job_id: str
    status: str                         # pending | running | done | error | cancelled
    progress: int = 0
    current_step: str = ""
    domain: Optional[str] = None
    output_file: Optional[str] = None
    error: Optional[str] = None
    duration_sec: Optional[float] = None
    total_segments: Optional[int] = None
    created_at: float = 0.0
    updated_at: float = 0.0


# Points de terminaison (Endpoints)

@app.get("/", tags=["Sante"])
def health_check():
    """Controle la disponibilite et l'etat de l'API."""
    return {
        "service": "VoiceLingo API",
        "author": "Mouhamadou Lamine Niang",
        "year": "2026",
        "version": "1.0.0",
        "status":  "running",
        "active_jobs": len(_jobs),
    }


@app.post("/api/v1/process-video", response_model=JobStatus, tags=["Traitements"])
def process_video(req: ProcessVideoRequest, background_tasks: BackgroundTasks):
    """Enregistre et demarre une operation de traduction en arriere-plan."""
    if not os.path.exists(req.video_path):
        raise HTTPException(
            status_code=400,
            detail=f"Fichier video introuvable : {req.video_path}",
        )

    # Resolution securisee du repertoire de sortie
    cfg = load_config()
    output_dir = req.output_dir or cfg.get("output_dir") or os.path.dirname(os.path.abspath(req.video_path))
    os.makedirs(output_dir, exist_ok=True)

    job_id = str(uuid.uuid4())[:8]
    now = time.time()

    job_data = {
        "job_id":         job_id,
        "status":         "pending",
        "progress":       0,
        "current_step":   "En attente de prise en charge",
        "domain":         None,
        "output_file":    None,
        "error":          None,
        "duration_sec":   None,
        "total_segments": None,
        "created_at":     now,
        "updated_at":     now,
        "_output_dir":    os.path.abspath(output_dir),
    }

    with _jobs_lock:
        _jobs[job_id] = job_data

    background_tasks.add_task(_run_job, job_id, req, output_dir)
    return JobStatus(**_jobs[job_id])


@app.get("/api/v1/job/{job_id}", response_model=JobStatus, tags=["Traitements"])
def get_job_status(job_id: str):
    """Consulte l'avancement et les metadonnees d'un job donne."""
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' introuvable.")
    return JobStatus(**job)


@app.get("/api/v1/job/{job_id}/download", tags=["Traitements"])
def download_result(job_id: str):
    """Telecharge de facon securisee le fichier resultat issu d'un traitement termine."""
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable.")
    if job["status"] != "done":
        raise HTTPException(
            status_code=400,
            detail=f"Job non termine - statut actuel : {job['status']}",
        )
    output = job.get("output_file")
    if not output or not os.path.exists(output):
        raise HTTPException(status_code=404, detail="Fichier de sortie introuvable.")

    # Protection contre le Path Traversal
    allowed_dir = os.path.abspath(job.get("_output_dir", os.path.dirname(output)))
    resolved_path = os.path.abspath(output)
    if not resolved_path.startswith(allowed_dir):
        raise HTTPException(status_code=403, detail="Acces interdit au chemin specifie.")

    return FileResponse(resolved_path, filename=Path(resolved_path).name)


@app.delete("/api/v1/job/{job_id}", tags=["Traitements"])
def cancel_job(job_id: str):
    """Interrompt un job actuellement en cours d'execution."""
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable.")
    if job["status"] not in ("pending", "running"):
        return {"message": f"Job deja finalise avec le statut : {job['status']}"}

    pipeline: Optional[ProcessingPipeline] = job.get("_pipeline")
    if pipeline:
        pipeline.cancel()

    with _jobs_lock:
        _jobs[job_id]["status"]     = "cancelled"
        _jobs[job_id]["updated_at"] = time.time()

    return {"message": f"Job {job_id} annule avec succes."}


@app.get("/api/v1/jobs", tags=["Traitements"])
def list_jobs():
    """Recense l'ensemble des jobs enregistres au cours de la session."""
    with _jobs_lock:
        jobs = [
            JobStatus(**{k: v for k, v in j.items() if not k.startswith("_")})
            for j in _jobs.values()
        ]
    return {"jobs": jobs, "total": len(jobs)}


# Gestionnaire d'arriere-plan

def _run_job(job_id: str, req: ProcessVideoRequest, output_dir: str) -> None:
    """Execute le pipeline de traitement de facon asynchrone."""
    start = time.time()

    cfg = load_config()
    cfg["whisper_model_size"]   = req.whisper_model_size
    cfg["whisper_device"]       = req.whisper_device
    cfg["nllb_model"]           = req.nllb_model

    pipeline = ProcessingPipeline(cfg)

    with _jobs_lock:
        _jobs[job_id]["status"]    = "running"
        _jobs[job_id]["_pipeline"] = pipeline
        _jobs[job_id]["updated_at"] = time.time()

    def on_progress(pct: int, label: str) -> None:
        with _jobs_lock:
            _jobs[job_id]["progress"]     = pct
            _jobs[job_id]["current_step"] = label
            _jobs[job_id]["updated_at"]   = time.time()
            if "domaine" in label.lower():
                for dk in ["informatique", "mathematiques", "physique",
                           "medecine", "biologie", "economie", "general"]:
                    if dk in label.lower():
                        _jobs[job_id]["domain"] = dk
                        break

    def on_done(success: bool, result: str) -> None:
        with _jobs_lock:
            _jobs[job_id]["duration_sec"] = round(time.time() - start, 1)
            _jobs[job_id]["updated_at"]   = time.time()
            if success:
                _jobs[job_id]["status"]      = "done"
                _jobs[job_id]["output_file"] = result
                _jobs[job_id]["progress"]    = 100
            else:
                _jobs[job_id]["status"] = "error"
                _jobs[job_id]["error"]  = result

    pipeline.run(
        video_path=req.video_path,
        src_lang=req.language_source,
        tgt_lang=req.language_target,
        output_mode=req.mode,
        output_dir=output_dir,
        burn_subs=req.burn_subtitles,
        progress_cb=on_progress,
        done_cb=on_done,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
