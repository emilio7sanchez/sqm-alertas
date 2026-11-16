"""Revisa las ofertas laborales de SQM y SQM Litio y envía un mail con las nuevas.

Variables de entorno (en GitHub van como "Secrets"):
  GMAIL_USER          tu dirección de Gmail (la que envía)
  GMAIL_APP_PASSWORD  contraseña de aplicación de Gmail (16 caracteres)
  MAIL_TO             a quién llega el aviso (opcional; por defecto GMAIL_USER)

Uso:
  python check_sqm.py            revisa, envía mail si hay nuevas y actualiza seen.json
  python check_sqm.py --seed     solo guarda las ofertas actuales como "ya vistas" (sin mail)
  python check_sqm.py --dry-run  muestra lo que enviaría, sin mandar mail ni guardar
"""

import html
import json
import os
import smtplib
import sys
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

SITES = {
    "SQM": "https://www.trabajaensqm.com",
    "SQM Litio": "https://trabajaen.sqmlitio.com",
}
STATE_FILE = Path(__file__).with_name("seen.json")


def fetch_jobs(base_url):
    """Devuelve la lista de ofertas publicadas en el sitio."""
    body = json.dumps({"size": 500, "sort": [{"created_at": "desc"}]}).encode()
    req = urllib.request.Request(
        f"{base_url}/app/minisite/site/_search",
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    jobs = []
    for hit in data["hits"]["hits"]:
        s = hit["_source"]
        jobs.append({
            "id": str(s["id"]),
            "title": (s.get("title") or "").strip(),
            "position": s.get("position") or "",
            "city": s.get("city") or s.get("company_location") or "",
            "contract": s.get("company_contract_type") or "",
            "created_at": (s.get("created_at") or "")[:10],
            "closes_at": (s.get("desactivate_at") or "")[:10],
            "url": f"{base_url}/{s.get('seo_path') or s['id']}",
        })
    return jobs


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def build_email(new_by_site):
    total = sum(len(v) for v in new_by_site.values())
    sites = " y ".join(new_by_site)
    subject = f"{total} nueva{'s' if total != 1 else ''} oferta{'s' if total != 1 else ''} laboral{'es' if total != 1 else ''} en {sites}"

    parts_html, parts_text = [], []
    for site, jobs in new_by_site.items():
        parts_html.append(f"<h2 style='color:#00594f;margin:24px 0 8px'>{html.escape(site)}</h2>")
        parts_text.append(f"\n== {site} ==")
        for j in jobs:
            details = " · ".join(x for x in [j["position"], j["city"], j["contract"]] if x)
            dates = f"Publicada {j['created_at']}" + (f" · cierra {j['closes_at']}" if j["closes_at"] else "")
            parts_html.append(
                "<div style='border:1px solid #ddd;border-radius:8px;padding:12px 16px;margin:8px 0'>"
                f"<a href='{html.escape(j['url'])}' style='font-size:16px;font-weight:bold;color:#0b57d0'>{html.escape(j['title'])}</a>"
                f"<div style='color:#444;margin-top:4px'>{html.escape(details)}</div>"
                f"<div style='color:#777;font-size:13px;margin-top:2px'>{html.escape(dates)}</div>"
                "</div>"
            )
            parts_text.append(f"- {j['title']}\n  {details}\n  {dates}\n  {j['url']}")

    body_html = (
        "<div style='font-family:Arial,sans-serif;max-width:640px'>"
        f"<p>Se publicaron <b>{total}</b> oferta(s) nueva(s):</p>"
        + "".join(parts_html)
        + "<p style='color:#999;font-size:12px;margin-top:24px'>Alerta automática SQM.</p></div>"
    )
    return subject, "\n".join(parts_text), body_html


def send_email(subject, text, body_html):
    user = os.environ["GMAIL_USER"]
    password = os.environ["GMAIL_APP_PASSWORD"].replace(" ", "")
    to = os.environ.get("MAIL_TO") or user
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Alertas SQM <{user}>"
    msg["To"] = to
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)


def main():
    seed = "--seed" in sys.argv
    dry = "--dry-run" in sys.argv
    state = load_state()
    new_by_site = {}
    errors = []

    for site, url in SITES.items():
        try:
            jobs = fetch_jobs(url)
        except Exception as e:  # si un sitio falla, no tocamos su estado
            errors.append(f"{site}: {e}")
            continue
        seen = set(state.get(site, []))
        new = [j for j in jobs if j["id"] not in seen]
        print(f"{site}: {len(jobs)} ofertas, {len(new)} nuevas")
        if new and not seed:
            new_by_site[site] = new
        # Guardamos todo lo visto (incluye ofertas ya cerradas, para no re-avisar si reaparecen)
        state[site] = sorted(seen | {j["id"] for j in jobs}, key=int)

    if new_by_site:
        subject, text, body_html = build_email(new_by_site)
        print(subject)
        print(text)
        if not dry:
            send_email(subject, text, body_html)
            print("Mail enviado.")

    if not dry:
        save_state(state)

    if errors:
        print("Errores:", *errors, sep="\n  ")
        sys.exit(1)


if __name__ == "__main__":
    main()
