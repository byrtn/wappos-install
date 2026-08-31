# Auteur : Patrick Ritaine
import fcntl
import json
import os
import time
import uuid
from pathlib import Path

_INSTALL_DIR = Path(__file__).parent
_JOBS_DIR = _INSTALL_DIR / "data" / "docker_jobs"

_JOB_TTL_SECONDS = 3600


def _job_path(job_id):
    return _JOBS_DIR / f"{job_id}.json"


def _write_job(job_id, job):
    _JOBS_DIR.mkdir(parents=True, exist_ok=True)
    path = _job_path(job_id)
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        json.dump(job, f)
        fcntl.flock(f, fcntl.LOCK_UN)
    os.replace(tmp_path, path)


def _read_job(job_id):
    path = _job_path(job_id)
    try:
        with open(path) as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            data = json.load(f)
            fcntl.flock(f, fcntl.LOCK_UN)
            return data
    except (OSError, ValueError):
        return None


def _prune_old_jobs():
    if not _JOBS_DIR.is_dir():
        return
    now = time.time()
    for entry in _JOBS_DIR.glob("*.json"):
        job = _read_job(entry.stem)
        if job and job["done"] and now - job["created_at"] > _JOB_TTL_SECONDS:
            entry.unlink(missing_ok=True)


def create_job(steps):
    job_id = uuid.uuid4().hex
    _prune_old_jobs()
    job = {
        "steps": steps,
        "current": 0,
        "done": False,
        "error": None,
        "warnings": [],
        "created_at": time.time(),
    }
    _write_job(job_id, job)
    return job_id


def advance(job_id, step_label):
    job = _read_job(job_id)
    if job is not None and step_label in job["steps"]:
        job["current"] = job["steps"].index(step_label)
        _write_job(job_id, job)


def finish(job_id, warnings=None):
    job = _read_job(job_id)
    if job is not None:
        job["done"] = True
        job["current"] = len(job["steps"])
        job["warnings"] = warnings or []
        _write_job(job_id, job)


def fail(job_id, error_message):
    job = _read_job(job_id)
    if job is not None:
        job["done"] = True
        job["error"] = error_message
        _write_job(job_id, job)


def get_job(job_id):
    return _read_job(job_id)
