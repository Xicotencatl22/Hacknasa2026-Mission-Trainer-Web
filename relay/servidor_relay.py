"""
Relay de Mission Trainer: conecta el juego con el servidor MCP desde cualquier
dispositivo, a través de internet.

    Juego (navegador, cualquier dispositivo) --wss--> relay <--wss-- servidor_mcp.py (PC con Claude)

Funciona con "salas": el juego entra con  /juego?sala=CODIGO  y el servidor MCP
con  /mcp?sala=CODIGO . Todo lo que manda uno le llega al otro.

- Una sala tiene como máximo un juego (si entra otro, reemplaza al anterior)
  y cualquier número de servidores MCP.
- A los servidores MCP se les avisa cuando el juego entra o sale:
      {"tipo": "sistema", "juego_conectado": true/false}
- Si un servidor MCP manda un comando y no hay juego en la sala, el relay
  responde con un error en lugar de dejarlo esperando.

Difusión: el listener de la NASA (u otro programa con la clave) entra a
/difusion?clave=CLAVE y cada comando que manda llega a TODOS los juegos conectados,
en todas las salas. Las salas siguen separadas para todo lo demás.

Resultados: cuando un juego avisa "evento_nasa_fin", el relay lo guarda en la tabla
resultados_eventos de Supabase (el ranking de la página web sale de ahí).

Variables de entorno (en Render):
    DIFUSION_CLAVE        clave para /difusion (sin ella, la difusión está apagada)
    SUPABASE_URL          https://<proyecto>.supabase.co
    SUPABASE_SERVICE_KEY  service_role key (secreta) para guardar resultados

Pensado para Render (https://render.com): escucha en el puerto de la variable
PORT y responde "ok" a las peticiones HTTP normales (revisión de salud).

Probar en tu PC:  pip install websockets  y  python servidor_relay.py
                  (escucha en ws://localhost:10000)
"""
import asyncio
import hmac
import itertools
import json
import logging
import os
import re
import signal
import urllib.error
import urllib.request
from http import HTTPStatus
from urllib.parse import parse_qs, urlparse

from websockets.asyncio.server import broadcast, serve
from websockets.exceptions import ConnectionClosed

PUERTO = int(os.environ.get("PORT", "10000"))
MAX_SALAS = 500
SALA_VALIDA = re.compile(r"[A-Za-z0-9_-]{3,40}")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("relay")

DIFUSION_CLAVE = os.environ.get("DIFUSION_CLAVE", "").strip()
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "").strip()
RESULTADOS_QUE_CUENTAN = {"superado", "fallado", "con_danos"}

# sala -> {"juego": conexión o None, "mcps": set de conexiones}
salas: dict[str, dict] = {}
_ids_difusion = itertools.count(1)


def salud(conexion, peticion):
    """Las peticiones que no son WebSocket (navegador, revisión de salud de Render)
    reciben un simple "ok"."""
    if peticion.headers.get("Upgrade", "").lower() != "websocket":
        return conexion.respond(HTTPStatus.OK, "Mission Trainer relay: ok\n")
    return None


def estado_sala(sala: dict) -> str:
    return json.dumps({"tipo": "sistema", "juego_conectado": sala["juego"] is not None})


def limpiar(codigo: str) -> None:
    sala = salas.get(codigo)
    if sala and sala["juego"] is None and not sala["mcps"]:
        del salas[codigo]


async def manejar(ws) -> None:
    url = urlparse(ws.request.path)
    rol = url.path.strip("/")
    codigo = parse_qs(url.query).get("sala", [""])[0]

    if rol == "difusion":
        await atender_difusion(ws, parse_qs(url.query).get("clave", [""])[0])
        return
    if rol not in ("juego", "mcp"):
        await ws.close(1008, "Usa /juego?sala=CODIGO, /mcp?sala=CODIGO o /difusion?clave=CLAVE")
        return
    if not SALA_VALIDA.fullmatch(codigo):
        await ws.close(1008, "Código de sala inválido (3 a 40 letras, números, - o _)")
        return
    if codigo not in salas and len(salas) >= MAX_SALAS:
        await ws.close(1013, "Demasiadas salas abiertas, intenta más tarde")
        return

    sala = salas.setdefault(codigo, {"juego": None, "mcps": set()})
    try:
        if rol == "juego":
            await atender_juego(ws, codigo, sala)
        else:
            await atender_mcp(ws, codigo, sala)
    finally:
        limpiar(codigo)


async def atender_juego(ws, codigo: str, sala: dict) -> None:
    anterior = sala["juego"]
    sala["juego"] = ws
    log.info("Juego entró a la sala %s", codigo)
    if anterior is not None:
        await anterior.close(4000, "Otro juego entró a esta sala")
    broadcast(sala["mcps"], estado_sala(sala))
    try:
        async for raw in ws:
            broadcast(sala["mcps"], raw)  # respuestas y eventos van a los MCP de esta sala
            if isinstance(raw, str) and '"evento_nasa_fin"' in raw:
                asyncio.create_task(guardar_resultado(codigo, raw))
    except ConnectionClosed:
        pass
    finally:
        if sala["juego"] is ws:
            sala["juego"] = None
            broadcast(sala["mcps"], estado_sala(sala))
        log.info("Juego salió de la sala %s", codigo)


async def atender_mcp(ws, codigo: str, sala: dict) -> None:
    sala["mcps"].add(ws)
    log.info("Servidor MCP entró a la sala %s", codigo)
    try:
        await ws.send(estado_sala(sala))
        async for raw in ws:
            juego = sala["juego"]
            if juego is not None:
                try:
                    await juego.send(raw)
                    continue
                except ConnectionClosed:
                    pass
            # No hay juego: si era un comando, contestamos con un error.
            try:
                datos = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(datos, dict) and "id" in datos:
                await ws.send(json.dumps({
                    "id": datos["id"],
                    "ok": False,
                    "error": f"No hay ningún juego en la sala '{codigo}'. Abre el juego "
                             f"agregando ?sala={codigo} al final de la dirección.",
                }, ensure_ascii=False))
    except ConnectionClosed:
        pass
    finally:
        sala["mcps"].discard(ws)
        log.info("Servidor MCP salió de la sala %s", codigo)


async def atender_difusion(ws, clave: str) -> None:
    """Cada comando que llega por aquí se manda a todos los juegos de todas las salas.
    Formato: {"cmd": "evento_nasa", "args": {...}}. Responde {"tipo": "difusion", "juegos": N}."""
    if not DIFUSION_CLAVE or not hmac.compare_digest(clave, DIFUSION_CLAVE):
        await ws.close(1008, "Clave de difusión incorrecta o difusión desactivada")
        return
    log.info("Emisor de difusión conectado")
    try:
        async for raw in ws:
            try:
                datos = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue
            if not isinstance(datos, dict) or not isinstance(datos.get("cmd"), str):
                continue
            args = datos.get("args") if isinstance(datos.get("args"), dict) else {}
            enviados = []
            for codigo, sala in list(salas.items()):
                if sala["juego"] is None:
                    continue
                comando = {"id": f"dif-{next(_ids_difusion)}", "cmd": datos["cmd"], "args": args}
                try:
                    await sala["juego"].send(json.dumps(comando, ensure_ascii=False))
                    enviados.append(codigo)
                except ConnectionClosed:
                    continue
                # Los MCP de la sala (Claude) se enteran de que llegó una difusión
                broadcast(sala["mcps"], json.dumps(
                    {"tipo": "evento", "evento": "difusion", "cmd": datos["cmd"], "datos": args},
                    ensure_ascii=False))
            log.info("Difusión '%s' enviada a %d juego(s)", datos["cmd"], len(enviados))
            await ws.send(json.dumps({"tipo": "difusion", "juegos": len(enviados), "salas": enviados}))
    except ConnectionClosed:
        pass


def _entero(v):
    """Godot manda los números de JSON como 37.0; los convertimos a entero si lo son."""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer() and v > 0:
        return int(v)
    if isinstance(v, str) and v.isdigit():
        return int(v)
    return None


async def guardar_resultado(codigo: str, raw: str) -> None:
    """Guarda en Supabase (tabla resultados_eventos) el resultado de un evento de la NASA."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    try:
        paquete = json.loads(raw)
    except json.JSONDecodeError:
        return
    if paquete.get("evento") != "evento_nasa_fin" or not isinstance(paquete.get("datos"), dict):
        return
    d = paquete["datos"]
    if d.get("resultado") not in RESULTADOS_QUE_CUENTAN:
        return
    tipo = str(d.get("tipo", ""))[:10]
    fila = {
        "sala": codigo,
        "tipo": tipo,
        "intensidad": (str(d.get("intensidad") or "")[:40]) or None,
        "evento_id": _entero(d.get("evento_id")),
        "fecha_evento": d.get("fecha") or None,
        "dificultad": (str(d.get("dificultad") or "")[:20]) or None,
        "severidad": _entero(d.get("severidad")),
        "resultado": d["resultado"],
        "dano_recibido_pct": float(d.get("dano_recibido_pct") or 0),
        "tiempo_usado_seg": float(d["tiempo_usado_seg"]) if isinstance(d.get("tiempo_usado_seg"), (int, float)) else None,
        "reparaciones": len(d.get("problemas") or []) if tipo in ("CME", "GST") else 0,
    }
    def enviar() -> int:
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/resultados_eventos",
            data=json.dumps(fila).encode(),
            method="POST",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    try:
        estado = await asyncio.to_thread(enviar)
        log.info("Resultado guardado (sala %s, %s %s): HTTP %s", codigo, tipo, fila["resultado"], estado)
    except urllib.error.HTTPError as e:
        log.warning("Supabase rechazó el resultado: HTTP %s %s", e.code, e.read()[:200])
    except Exception as e:
        log.warning("No se pudo guardar el resultado: %s", e)


async def main() -> None:
    detener = asyncio.get_running_loop().create_future()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            asyncio.get_running_loop().add_signal_handler(sig, detener.set_result, None)
        except (NotImplementedError, RuntimeError):
            pass  # Windows
    async with serve(manejar, "0.0.0.0", PUERTO, process_request=salud, max_size=2**16):
        log.info("Relay escuchando en el puerto %s", PUERTO)
        await detener


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
