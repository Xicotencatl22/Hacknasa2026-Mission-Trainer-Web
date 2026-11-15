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

Pensado para Render (https://render.com): escucha en el puerto de la variable
PORT y responde "ok" a las peticiones HTTP normales (revisión de salud).

Probar en tu PC:  pip install websockets  y  python servidor_relay.py
                  (escucha en ws://localhost:10000)
"""
import asyncio
import json
import logging
import os
import re
import signal
from http import HTTPStatus
from urllib.parse import parse_qs, urlparse

from websockets.asyncio.server import broadcast, serve
from websockets.exceptions import ConnectionClosed

PUERTO = int(os.environ.get("PORT", "10000"))
MAX_SALAS = 500
SALA_VALIDA = re.compile(r"[A-Za-z0-9_-]{3,40}")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("relay")

# sala -> {"juego": conexión o None, "mcps": set de conexiones}
salas: dict[str, dict] = {}


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

    if rol not in ("juego", "mcp"):
        await ws.close(1008, "Usa /juego?sala=CODIGO o /mcp?sala=CODIGO")
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
            broadcast(sala["mcps"], raw)  # respuestas y eventos van a todos los MCP
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
