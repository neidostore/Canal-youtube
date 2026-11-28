// Pruebas del bot sin red (Telegram, Google y KV simulados).  node bot-revision/prueba_worker.mjs
import { pathToFileURL } from "url";
import path from "path";
const worker = (await import(pathToFileURL(path.resolve("bot-revision/worker.js")).href)).default;

const kv = new Map();
const DATOS = { get: async (k) => kv.get(k) ?? null, put: async (k, v) => kv.set(k, v), delete: async (k) => kv.delete(k) };
const env = { DATOS, TELEGRAM_TOKEN: "T", DUENO_ID: "111", WEBHOOK_SECRETO: "W", PC_CLAVE: "C",
  GOOGLE_CLIENT_ID: "g", GOOGLE_CLIENT_SECRET: "s", GOOGLE_REFRESH_TOKEN: "r", AUDITADO: "no" };
const enviados = [], youtube = [];
globalThis.fetch = async (url, op = {}) => {
  url = String(url);
  if (url.includes("api.telegram.org")) { enviados.push({ m: url.split("/").pop(), b: JSON.parse(op.body) }); return new Response('{"ok":true,"result":{}}'); }
  if (url.includes("oauth2.googleapis.com")) return new Response('{"access_token":"AT"}');
  if (url.includes("youtube/v3/videos")) { youtube.push(JSON.parse(op.body)); return new Response("{}"); }
  throw new Error("fetch inesperado " + url);
};
const pend = []; const ctx = { waitUntil: (p) => pend.push(p) };
const esperar = async () => { while (pend.length) await pend.shift(); };
const pc = async (ruta, datos) => (await worker.fetch(new Request("https://x/pc/" + ruta, datos ?
  { method: "POST", body: JSON.stringify(datos), headers: { "X-Clave": "C" } } : { headers: { "X-Clave": "C" } }), env, ctx)).json();
const tgUpd = async (upd) => { await worker.fetch(new Request("https://x/telegram", { method: "POST", body: JSON.stringify(upd),
  headers: { "X-Telegram-Bot-Api-Secret-Token": "W" } }), env, ctx); await esperar(); };
const msg = (text, id = 111) => tgUpd({ message: { from: { id }, chat: { id }, text } });
const boton = (data) => tgUpd({ callback_query: { id: "q", from: { id: 111 }, data, message: { chat: { id: 111 }, message_id: 5 } } });
const ultimoB = () => enviados.filter((e) => e.m === "sendMessage").at(-1)?.b;
const ultimo = () => ultimoB()?.text;
let fallos = 0;
const ok = (c, t) => { console.log((c ? "OK    " : "FALLA ") + t); if (!c) fallos++; };

// seguridad
ok((await worker.fetch(new Request("https://x/pc/items", { headers: { "X-Clave": "mal" } }), env, ctx)).status === 403, "PC con clave mala → 403");
ok((await worker.fetch(new Request("https://x/telegram", { method: "POST", body: "{}", headers: { "X-Telegram-Bot-Api-Secret-Token": "x" } }), env, ctx)).status === 403, "webhook con secreto malo → 403");
const n0 = enviados.length; await msg("/start", 999); ok(enviados.length === n0, "un desconocido no recibe respuesta");

// calendario del PC (2 Shorts al día 13:00 y 19:00; largos martes y viernes 18:00)
const cal = { short: [0, 1, 2, 3, 4, 5, 6].flatMap((d) => [[d, 13, 0], [d, 19, 0]]), largo: [[2, 18, 0], [5, 18, 0]] };
ok((await pc("calendario", cal)).ok, "el PC manda el calendario");
const h = await pc("hueco?tipo=short&id=s1");
ok(/ (13|19):00$/.test(h.fecha_texto), "hueco de Short a las 13:00 o 19:00: " + h.fecha_texto);
const hl = await pc("hueco?tipo=largo&id=l1");
ok(/^(martes|viernes) .* 18:00$/.test(hl.fecha_texto), "hueco de largo martes/viernes 18:00: " + hl.fecha_texto);
const hr = await pc("hueco?tipo=ranking&id=viejo");
ok(/^(martes|viernes) .* 19:00$/.test(hr.fecha_texto), "los tipos antiguos siguen funcionando: " + hr.fecha_texto);

// ficha completa con 6 botones y versión
await pc("revision", { id: "s1", tipo: "short", version: 1, titulo: "Título <b>", descripcion: "desc", etiquetas: [], fecha_utc: h.fecha_utc,
  prueba: true, duracion: 55, puntuacion: 85.5, coste: 0, guion_texto: "Frase uno\nFrase dos", fuentes_texto: "• dato — NPR: https://npr.org",
  avisos_calidad: ["volumen bajo"], comentario: "¿Cuál?" });
await esperar();
const f = ultimoB();
const btn = f.reply_markup.inline_keyboard.flat().map((b) => b.callback_data);
ok(btn.length === 8 && btn.includes("ok:s1:1") && btn.includes("g:s1") && btn.includes("f:s1") && btn.includes("fe:s1:1") &&
  btn.includes("mi:s1:1") && btn.includes("vo:s1:1"), "8 botones con versión: " + btn.join(" "));
ok(f.text.includes("MODO PRUEBA") && f.text.includes("85.5/100") && f.text.includes("0:55") && f.text.includes("Título &lt;b&gt;") && f.text.includes("volumen bajo"),
  "la ficha lleva prueba, calidad, duración, título escapado y avisos");

// ver guion y fuentes
await boton("g:s1"); ok(ultimo().includes("Frase dos"), "VER GUION");
await boton("f:s1"); ok(ultimo().includes("npr.org"), "VER FUENTES");

// cambiar fecha
await boton("fe:s1:1");
const opciones = ultimoB().reply_markup.inline_keyboard.flat();
ok(opciones.length === 4 && opciones.every((o) => o.callback_data.startsWith("fs:s1:")), "CAMBIAR FECHA ofrece 4 huecos libres");
await boton(opciones[2].callback_data);
ok(ultimo().includes("Nueva fecha"), "elige la fecha: " + ultimo().split("<b>")[1]);

// pedir cambios → versión 2; los botones de la versión 1 ya no valen
await boton("cam:s1:1"); await msg("Más corto el final"); await msg("/listo");
ok((await pc("tareas")).tareas.length === 1, "el PC ve el cambio pedido");
await pc("revision", { id: "s1", tipo: "short", version: 2, titulo: "Título v2", descripcion: "d", fecha_utc: h.fecha_utc, prueba: true });
await esperar();
await boton("ok:s1:1"); ok(ultimo().includes("versión 1") && ultimo().includes("la actual es la 2"), "un ✅ de la versión 1 NO aprueba la 2");

// aprobar en modo prueba: no toca YouTube
await boton("ok:s1:2");
ok(youtube.length === 0 && ultimo().includes("modo prueba"), "aprobar en prueba no sube nada a YouTube");
ok(JSON.parse(kv.get("item:s1")).estado === "aprobado" && JSON.parse(kv.get("item:s1")).version_aprobada === 2, "queda aprobado con su versión");

// producción: aprobado sin vídeo subido → el PC lo programa solo si coincide la versión
await pc("revision", { id: "s2", tipo: "short", version: 1, titulo: "Real", descripcion: "d", fecha_utc: h.fecha_utc, prueba: false });
await esperar();
let r = await pc("programado", { id: "s2", version: 1, youtube_id: "YTX" });
ok(r.ok === false, "no se programa nada que no hayas aprobado");
await boton("ok:s2:1"); ok(ultimo().includes("próximo ciclo"), "aprobado: lo subirá el PC");
r = await pc("programado", { id: "s2", version: 3, youtube_id: "YTX" }); ok(r.ok === false, "versión distinta → no se programa");
r = await pc("programado", { id: "s2", version: 1, youtube_id: "YTX" }); ok(r.ok && ultimo().includes("Programado"), "versión aprobada → programado");

// rechazar con motivo
await pc("revision", { id: "s3", tipo: "short", version: 1, titulo: "Malo", descripcion: "d", fecha_utc: h.fecha_utc, prueba: true });
await esperar();
await boton("no:s3:1"); ok(ultimo().includes("¿Por qué?"), "RECHAZAR pide el motivo");
await msg("El gancho es aburrido"); ok(JSON.parse(kv.get("item:s3")).motivo_rechazo === "El gancho es aburrido", "el motivo queda guardado");

// panel
await msg("/panel"); ok(ultimo().includes("Todavía no"), "/panel sin datos avisa");
await pc("panel", { texto: "📊 PANEL\nSuscriptores: 31" }); await msg("/panel"); ok(ultimo().includes("Suscriptores: 31"), "/panel enseña lo que manda el PC");

// compatibilidad: botones antiguos sin versión
await pc("revision", { id: "viejo", tipo: "ranking", titulo: "Antiguo", descripcion: "d", youtube_id: "YTV", fecha_utc: hr.fecha_utc });
await esperar();
await boton("ok:viejo"); ok(youtube.length === 1 && youtube[0].id === "YTV", "los mensajes antiguos (sin versión) siguen funcionando");

// --- mejoras de imagen y voz, empresa y TikTok ---
await pc("revision", { id: "l9", tipo: "largo", version: 1, titulo: "Arca", descripcion: "d", fecha_utc: hl.fecha_utc, prueba: true,
  nota_voz: 91.4, nota_visual: 100, perfil_voz: "C", plataformas: ["YouTube"], recomendacion: "Publicar",
  miniaturas: [{ id: "A", idea: "Arca abriéndose", nota: 100 }, { id: "B", idea: "Capilla", nota: 98 }], miniatura_elegida: "A" });
await esperar();
const fl = ultimoB();
ok(fl.text.includes("visual 100") && fl.text.includes("locución 91.4") && fl.text.includes("Recomendación") && fl.text.includes("perfil C"),
  "la ficha del largo lleva notas visual y de locución, perfil de voz y recomendación");
ok(fl.reply_markup.inline_keyboard.flat().some((b) => b.text.includes("APROBAR Y PUBLICAR")), "botón APROBAR Y PUBLICAR");
await boton("mi:l9:1"); const mi = ultimoB().reply_markup.inline_keyboard.flat().map((b) => b.callback_data);
ok(mi.includes("mz:l9:A") && mi.includes("mz:l9:B") && mi.includes("mr:l9"), "MINIATURA ofrece conceptos y regenerar");
await boton("vo:l9:1"); const vo = ultimoB().reply_markup.inline_keyboard.flat().map((b) => b.callback_data);
ok(vo.includes("vp:l9:B") && vo.includes("vr:l9"), "VOZ ofrece perfiles y regenerar");
await boton("mz:l9:B");
ok(JSON.parse(kv.get("item:l9")).cambios[0].texto === "[miniatura] B" && JSON.parse(kv.get("item:l9")).estado === "cambios", "elegir concepto B → versión nueva");
ok((await pc("tareas")).tareas.some((t) => t.id === "l9"), "el PC lo ve como cambio");
await boton("vz:B"); ok((await pc("ajustes")).voz_elegida.letra === "B", "elegir perfil oficial de voz B");
await boton("cr:Ugx1"); ok((await pc("ajustes")).respuestas_ok.includes("Ugx1"), "aprobar respuesta del Community Manager");
await pc("respondidas", {}); ok((await pc("ajustes")).respuestas_ok.length === 0, "respuestas publicadas se limpian");
let rr = await worker.fetch(new Request("https://x/tiktok/callback?code=C1&state=S1"), env, ctx); await esperar();
ok(rr.status === 200 && (await pc("tiktok_code")).auth.code === "C1", "vuelta de TikTok guardada para el PC");
ok((await pc("tiktok_code")).auth === null, "el código de TikTok se entrega una sola vez");
await msg("/tiktok"); ok(ultimo().includes("Nunca me des tu contraseña"), "/tiktok explica la conexión segura");
await msg("/organigrama"); ok(ultimo().includes("CEO"), "/organigrama");

console.log(fallos ? `\n${fallos} FALLOS` : "\nTODO OK");
process.exitCode = fallos ? 1 : 0;
