"""PWA blueprint for CyberShield.

Serves the PWA manifest, service worker, and offline fallback page.
The service worker is served from the root scope ("/") so it can control
every route in the application. Files live under static/pwa/ and the icons
live under static/pwa/icons/.

This is the only minimal Python addition required for PWA support. It does
not alter any existing route, model, or business logic.
"""

import os

from flask import Blueprint, current_app, send_from_directory

pwa_bp = Blueprint("pwa", __name__)


def _pwa_dir():
    """Absolute path to the static/pwa directory."""
    return os.path.join(current_app.static_folder, "pwa")


@pwa_bp.route("/manifest.json")
def manifest():
    """Serve the web app manifest (needed for installability)."""
    return send_from_directory(
        _pwa_dir(),
        "manifest.json",
        mimetype="application/manifest+json",
    )


@pwa_bp.route("/service-worker.js")
def service_worker():
    """Serve the service worker at root scope so it controls all routes."""
    return send_from_directory(
        _pwa_dir(),
        "service-worker.js",
        mimetype="application/javascript",
    )


@pwa_bp.route("/offline.html")
def offline():
    """Serve the branded offline fallback page."""
    return send_from_directory(_pwa_dir(), "offline.html")

