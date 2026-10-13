"""ORYN — doações / apoio ao projeto.

Gera o PIX "Copia e Cola" (BR Code EMV) e o QR Code correspondente,
100%% offline (usa segno). Também expõe os links de plataformas de apoio.

Config opcional em config.json:
    "donate": {
      "pixKey": "076.437.581-40",
      "pixName": "NICOLLAS LORICCHIO",
      "pixCity": "SAO PAULO",
      "links": { "patreon": "https://...", "kofi": "", "buymeacoffee": "", "github": "" }
    }
"""

from __future__ import annotations

import io
import re
import unicodedata
from typing import Any

DEFAULT_DONATE: dict[str, Any] = {
    "pixKey": "076.437.581-40",
    "pixName": "NICOLLAS LORICCHIO",
    "pixCity": "SAO PAULO",
    "links": {
        "patreon": "",
        "kofi": "",
        "buymeacoffee": "",
        "github": "https://github.com/sponsors/nicollaslori-account",
    },
}


def _ascii(value: str, max_len: int = 0) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"\s+", " ", text).strip().upper()
    if max_len:
        text = text[:max_len]
    return text


def normalize_pix_key(key: str) -> str:
    key = str(key or "").strip()
    raw = re.sub(r"\s", "", key)
    if re.fullmatch(r"[\d.\-/+]+", raw):
        digits = re.sub(r"\D", "", raw)
        if len(digits) in (11, 14):
            return digits
    return key


def _emv(id_: str, value: str) -> str:
    return f"{id_}{len(value):02d}{value}"


def _crc16(payload: str) -> str:
    crc = 0xFFFF
    for byte in payload.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def build_pix_payload(key: str, name: str, city: str, amount: float | None = None,
                      txid: str = "***", description: str = "") -> str:
    key = normalize_pix_key(key)
    gui = _emv("00", "br.gov.bcb.pix")
    key_field = _emv("01", key)
    desc_field = _emv("02", _ascii(description, 72)) if description else ""
    mai = _emv("26", gui + key_field + desc_field)

    payload = _emv("00", "01") + mai
    payload += _emv("52", "0000")
    payload += _emv("53", "986")
    if amount and amount > 0:
        payload += _emv("54", f"{amount:.2f}")
    payload += _emv("58", "BR")
    payload += _emv("59", _ascii(name, 25) or "ORYN")
    payload += _emv("60", _ascii(city, 15) or "SAO PAULO")
    if txid:
        txid = re.sub(r"[^A-Za-z0-9]", "", txid)[:25] or "***"
        payload += _emv("62", _emv("05", txid))
    payload += "6304"
    return payload + _crc16(payload)


def get_donate(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    data = {
        "pixKey": DEFAULT_DONATE["pixKey"],
        "pixName": DEFAULT_DONATE["pixName"],
        "pixCity": DEFAULT_DONATE["pixCity"],
        "links": dict(DEFAULT_DONATE["links"]),
    }
    incoming = (cfg or {}).get("donate") or {}
    for field in ("pixKey", "pixName", "pixCity"):
        if incoming.get(field):
            data[field] = incoming[field]
    links = incoming.get("links") or {}
    for name, url in links.items():
        if url:
            data["links"][name] = url
    return data


def pix_payload_from_cfg(cfg: dict[str, Any] | None, amount: float | None = None) -> str:
    d = get_donate(cfg)
    return build_pix_payload(d["pixKey"], d["pixName"], d["pixCity"], amount=amount)


def pix_qr_png(payload: str, scale: int = 8, border: int = 2) -> bytes:
    import segno

    qr = segno.make(payload, error="m")
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=scale, border=border, dark="#0b0b0f", light="#ffffff")
    return buf.getvalue()


def pix_qr_svg(payload: str, scale: int = 8, border: int = 2) -> str:
    import segno

    qr = segno.make(payload, error="m")
    buf = io.BytesIO()
    qr.save(buf, kind="svg", scale=scale, border=border, dark="#0b0b0f", light="#ffffff")
    return buf.getvalue().decode("utf-8")


if __name__ == "__main__":
    d = get_donate()
    p = build_pix_payload(d["pixKey"], d["pixName"], d["pixCity"])
    print("KEY   :", normalize_pix_key(d["pixKey"]))
    print("PAYLOAD:", p)
    print("CRC    :", p[-4:])
    print("QR len :", len(pix_qr_png(p)))
