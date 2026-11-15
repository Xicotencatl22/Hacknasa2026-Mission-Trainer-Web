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


- El MCP puede conectarse con  /mcp?sala=*  para mandar eventos en modo global:
  todos los juegos con conexión reciben el evento.
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
SALA_GLOBAL = "*"  # código especial: /mcp?sala=* → modo global (eventos a todas las salas)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("relay")

DIFUSION_CLAVE = os.environ.get("DIFUSION_CLAVE", "").strip()
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "").strip()
RESULTADOS_QUE_CUENTAN = {"superado", "fallado", "con_danos"}

# sala -> {"juego": conexión o None, "mcps": set de conexiones}
salas: dict[str, dict] = {}
_ids_difusion = itertools.count(1)
# MCPs conectados en modo global (sala=*)
mcps_globales: set = set()



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
    if codigo == SALA_GLOBAL and rol != "mcp":
        await ws.close(1008, "El código global solo lo usan los MCP (/mcp?sala=*)")
        return
    if codigo != SALA_GLOBAL and not SALA_VALIDA.fullmatch(codigo):
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
    broadcast(sala["mcps"] | mcps_globales, estado_sala(sala))
    try:
        async for raw in ws:
            if isinstance(raw, str) and '"pedir_ranking"' in raw:
                # El juego pide el ranking (tecla Tab): se contesta solo a esta sala
                if SUPABASE_URL and SUPABASE_KEY:
                    asyncio.create_task(enviar_ranking(codigo, None))
                continue
            broadcast(sala["mcps"] | mcps_globales, raw)  # respuestas y eventos van a todos los MCP
            if isinstance(raw, str) and '"evento_nasa_fin"' in raw:
                asyncio.create_task(guardar_resultado(codigo, raw))
    except ConnectionClosed:
        pass
    finally:
        if sala["juego"] is ws:
            sala["juego"] = None
            broadcast(sala["mcps"] | mcps_globales, estado_sala(sala))
        log.info("Juego salió de la sala %s", codigo)


async def responder_sin_juego(ws, raw: str, codigo: str) -> None:
    """Si no hay juego en la sala, contestamos con un error en lugar de dejar el comando esperando."""
    try:
        datos = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return
    if isinstance(datos, dict) and "id" in datos:
        await ws.send(json.dumps({
            "id": datos["id"],
            "ok": False,
            "error": f"No hay ningún juego en la sala '{codigo}'. Abre el juego "
                     f"agregando ?sala={codigo} al final de la dirección.",
        }, ensure_ascii=False))


async def atender_mcp(ws, codigo: str, sala: dict) -> None:
    if codigo == SALA_GLOBAL:
        mcps_globales.add(ws)
        log.info("Servidor MCP en modo global")
        try:
            await ws.send(estado_sala(sala))
            async for raw in ws:
                juegos = [s["juego"] for s in salas.values() if s["juego"] is not None]
                if not juegos:
                    await responder_sin_juego(ws, raw, codigo)
                    continue
                for juego in juegos:
                    try:
                        await juego.send(raw)
                    except ConnectionClosed:
                        pass
        except ConnectionClosed:
            pass
        finally:
            mcps_globales.discard(ws)
            log.info("Servidor MCP salió del modo global")
        return
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
            await responder_sin_juego(ws, raw, codigo)
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
        "duracion_seg": float(d["duracion_seg"]) if isinstance(d.get("duracion_seg"), (int, float)) and d["duracion_seg"] > 0 else None,
    }
    def enviar() -> dict:
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/resultados_eventos?select=puntos",
            data=json.dumps(fila).encode(),
            method="POST",
            headers=_cabeceras_supabase() | {
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            filas = json.loads(r.read() or b"[]")
            return filas[0] if filas else {}
    try:
        guardada = await asyncio.to_thread(enviar)
        log.info("Resultado guardado (sala %s, %s %s): %s pts", codigo, tipo, fila["resultado"], guardada.get("puntos"))
    except urllib.error.HTTPError as e:
        log.warning("Supabase rechazó el resultado: HTTP %s %s", e.code, e.read()[:200])
        return
    except Exception as e:
        log.warning("No se pudo guardar el resultado: %s", e)
        return
    await enviar_ranking(codigo, guardada.get("puntos"))


def _cabeceras_supabase() -> dict:
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}


def leer_ranking() -> list:
    """Todas las salas ordenadas por puntos (máximo 500, igual que MAX_SALAS)."""
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/ranking_salas?select=sala,puntos,superados,jugados,mejor_tiempo_seg"
        "&jugados=gt.0&order=puntos.desc,mejor_tiempo_seg.asc.nullslast&limit=500",
        headers=_cabeceras_supabase(),
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read() or b"[]")


async def enviar_ranking(codigo: str, puntos_ganados) -> None:
    """Manda al juego de la sala (y a sus MCP) el top 10 y su posición.
    Va sin "id", así que un juego que todavía no muestra el ranking simplemente lo ignora."""
    try:
        todas = await asyncio.to_thread(leer_ranking)
    except Exception as e:
        log.warning("No se pudo leer el ranking: %s", e)
        return
    filas = [
        {"pos": i + 1, "sala": f.get("sala"), "puntos": f.get("puntos") or 0,
         "superados": f.get("superados") or 0, "jugados": f.get("jugados") or 0,
         "mejor_tiempo_seg": f.get("mejor_tiempo_seg")}
        for i, f in enumerate(todas)
    ]
    propia = next((f for f in filas if f["sala"] == codigo), None)
    datos = {"tu_sala": codigo, "puntos_ganados": puntos_ganados, "tu_posicion": propia,
             "total_salas": len(filas), "top": filas[:10]}
    sala = salas.get(codigo)
    if sala is None:
        return
    if sala["juego"] is not None:
        try:
            await sala["juego"].send(json.dumps({"tipo": "ranking", **datos}, ensure_ascii=False))
        except ConnectionClosed:
            pass
    broadcast(sala["mcps"], json.dumps({"tipo": "evento", "evento": "ranking", "datos": datos}, ensure_ascii=False))


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
