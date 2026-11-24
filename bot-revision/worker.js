// Bot de Telegram «Shock Mental · Revisión» — corre gratis en Cloudflare Workers, 24 h.
// SOLO para el canal Shock Mental. Solo responde al dueño (DUENO_ID).
//
// Secretos (wrangler secret put …, nunca en el repo):
//   TELEGRAM_TOKEN, DUENO_ID, WEBHOOK_SECRETO, PC_CLAVE,
//   GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN
// Variables (wrangler.toml): AUDITADO = "no" | "si"
// Almacén: KV «DATOS»  →  item:<id>, indice, ideas, esperando

const ZONA = "Europe/Madrid";
// Calendario acordado (día de la semana: 0 = domingo … 6 = sábado; hora de España)
const CALENDARIO = {
  ranking: [[2, 19, 0], [5, 19, 0]],             // martes y viernes 19:00
  short: [[1, 19, 0], [3, 19, 0], [6, 12, 0]],    // lunes y miércoles 19:00, sábado 12:00
  dosis: [[4, 18, 0]],                            // jueves 18:00
};
const DIAS = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];
const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const ESTADOS = {
  revision: "👀 esperando tu revisión", esperando_cambios: "✏️ esperando que me digas los cambios",
  cambios: "🛠️ cambios pedidos (los aplico cuando el PC esté encendido)", rehaciendo: "🛠️ rehaciendo",
  programado: "📅 programado", descartado: "❌ descartado", publicado: "✅ publicado",
};

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    if (url.pathname === "/telegram" && req.method === "POST") {
      if (req.headers.get("X-Telegram-Bot-Api-Secret-Token") !== env.WEBHOOK_SECRETO) return new Response("no", { status: 403 });
      const upd = await req.json();
      ctx.waitUntil(manejar(upd, env).catch((e) => console.log("ERROR", e.stack || e)));
      return new Response("ok");
    }
    if (url.pathname.startsWith("/pc/")) {
      if (!env.PC_CLAVE || req.headers.get("X-Clave") !== env.PC_CLAVE) return new Response("no", { status: 403 });
      try {
        return json(await pc(url, req, env));
      } catch (e) {
        return json({ ok: false, error: String(e.message || e) }, 500);
      }
    }
    return new Response("Shock Mental · Revisión");
  },
  async scheduled(ev, env, ctx) {
    ctx.waitUntil(recordatorios(env));
  },
};

// ---------- utilidades ----------
const json = (o, status = 200) => new Response(JSON.stringify(o), { status, headers: { "content-type": "application/json" } });
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

async function tg(env, metodo, datos) {
  const r = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/${metodo}`, {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(datos),
  });
  const j = await r.json();
  if (!j.ok) console.log("Telegram", metodo, JSON.stringify(j));
  return j;
}
const decir = (env, texto, extra = {}) =>
  tg(env, "sendMessage", { chat_id: env.DUENO_ID, text: texto, parse_mode: "HTML", disable_web_page_preview: true, ...extra });

async function leer(env, clave, defecto = null) {
  const v = await env.DATOS.get(clave);
  return v ? JSON.parse(v) : defecto;
}
const guardar = (env, clave, valor) => env.DATOS.put(clave, JSON.stringify(valor));
const getItem = (env, id) => leer(env, "item:" + id);
async function putItem(env, item) {
  await guardar(env, "item:" + item.id, item);
  const indice = await leer(env, "indice", []);
  if (!indice.includes(item.id)) { indice.push(item.id); await guardar(env, "indice", indice.slice(-200)); }
}
async function todos(env) {
  const indice = await leer(env, "indice", []);
  return (await Promise.all(indice.map((id) => getItem(env, id)))).filter(Boolean);
}

// Partes de una fecha en hora de España
function partesMadrid(d) {
  const p = {};
  for (const x of new Intl.DateTimeFormat("en-US", {
    timeZone: ZONA, hour12: false, year: "numeric", month: "numeric", day: "numeric",
    hour: "numeric", minute: "numeric", weekday: "short",
  }).formatToParts(d)) p[x.type] = x.value;
  const dow = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].indexOf(p.weekday);
  return { y: +p.year, m: +p.month, d: +p.day, h: +p.hour % 24, min: +p.minute, dow };
}
// Hora de España → Date (UTC)
function madridAUtc(y, m, d, h, min) {
  let t = Date.UTC(y, m - 1, d, h, min);
  for (let i = 0; i < 2; i++) {
    const p = partesMadrid(new Date(t));
    const dif = Date.UTC(p.y, p.m - 1, p.d, p.h, p.min) - Date.UTC(y, m - 1, d, h, min);
    t -= dif;
  }
  return new Date(t);
}
function fechaTexto(iso) {
  if (!iso) return "sin fecha";
  const p = partesMadrid(new Date(iso));
  return `${DIAS[p.dow]} ${p.d} ${MESES[p.m - 1]} · ${String(p.h).padStart(2, "0")}:${String(p.min).padStart(2, "0")}`;
}
// Siguiente hueco libre del calendario para un tipo de vídeo
async function hueco(env, tipo, excluirId) {
  const slots = CALENDARIO[tipo];
  if (!slots) throw new Error(`tipo desconocido: ${tipo} (usa ranking, short o dosis)`);
  const ocupadas = new Set((await todos(env))
    .filter((i) => i.id !== excluirId && ["revision", "esperando_cambios", "cambios", "rehaciendo", "programado"].includes(i.estado))
    .map((i) => i.fecha_utc));
  const minimo = Date.now() + 60 * 60 * 1000;   // al menos 1 hora de margen
  const hoy = partesMadrid(new Date());
  for (let k = 0; k < 90; k++) {
    const base = new Date(Date.UTC(hoy.y, hoy.m - 1, hoy.d + k, 12));
    const dow = base.getUTCDay();
    for (const [dia, h, min] of slots) {
      if (dia !== dow) continue;
      const f = madridAUtc(base.getUTCFullYear(), base.getUTCMonth() + 1, base.getUTCDate(), h, min);
      const iso = f.toISOString().replace(/\.\d+Z$/, ".000Z");
      if (f.getTime() >= minimo && !ocupadas.has(iso)) return iso;
    }
  }
  throw new Error("no encuentro hueco en los próximos 90 días");
}

// ---------- mensajes al dueño ----------
function botones(id) {
  return { inline_keyboard: [
    [{ text: "✅ Aprobar", callback_data: "ok:" + id }],
    [{ text: "✏️ Pedir cambios", callback_data: "cam:" + id }, { text: "❌ Descartar", callback_data: "no:" + id }],
  ] };
}
function fichaTexto(it) {
  let desc = it.descripcion || "";
  if (desc.length > 2500) desc = desc.slice(0, 2500) + "…";
  return `🎬 <b>Para revisar</b> · versión ${it.version}\n📺 El vídeo te lo he dejado en la conversación de Claude.\n\n` +
    `<b>Título:</b> ${esc(it.titulo)}\n` +
    `<b>Se publicaría:</b> ${esc(fechaTexto(it.fecha_utc))}\n` +
    `<b>Etiquetas:</b> ${esc((it.etiquetas || []).map((e) => "#" + e).join(" "))}\n\n` +
    `<b>Descripción:</b>\n${esc(desc)}\n\n` +
    (it.youtube_id ? `▶️ Verlo en YouTube (privado, calidad completa): https://youtu.be/${it.youtube_id}` : "");
}
const AYUDA =
  "🤖 <b>Shock Mental · Revisión</b>\n\n" +
  "Cuando termine un vídeo te lo mando aquí con tres botones:\n" +
  "✅ <b>Aprobar</b>: lo programo en YouTube según el calendario.\n" +
  "✏️ <b>Pedir cambios</b>: luego me escribes o me mandas un audio con lo que quieres cambiar.\n" +
  "❌ <b>Descartar</b>: no se publica (se queda privado).\n\n" +
  "<b>Órdenes:</b>\n" +
  "/idea texto — guarda una idea para próximos vídeos\n" +
  "/ideas — ver la lista de ideas\n" +
  "/pendientes — lo que espera tu revisión\n" +
  "/calendario — lo que ya está programado\n" +
  "/ayuda — este mensaje";

// ---------- Telegram ----------
async function manejar(upd, env) {
  const cb = upd.callback_query;
  const msg = upd.message;
  const de = cb ? cb.from : msg ? msg.from : null;
  if (!de || String(de.id) !== String(env.DUENO_ID)) return;    // solo el dueño

  if (cb) {
    await tg(env, "answerCallbackQuery", { callback_query_id: cb.id });
    const [accion, id] = (cb.data || "").split(":");
    const it = await getItem(env, id);
    if (!it) return decir(env, "No encuentro ese vídeo.");
    if (!["revision", "esperando_cambios"].includes(it.estado))
      return decir(env, `«${esc(it.titulo)}» ya está ${ESTADOS[it.estado] || it.estado}.`);
    const quitarBotones = () => tg(env, "editMessageReplyMarkup", {
      chat_id: cb.message.chat.id, message_id: cb.message.message_id, reply_markup: { inline_keyboard: [] } });
    if (accion === "ok") return aprobar(env, it, quitarBotones);
    if (accion === "cam") {
      it.estado = "esperando_cambios"; await putItem(env, it);
      await guardar(env, "esperando", id);
      return decir(env, `✏️ Vale. Escríbeme o mándame un <b>audio</b> con lo que quieres cambiar de «${esc(it.titulo)}».\n` +
        "Puedes mandar varios mensajes. Cuando termines, escribe /listo.");
    }
    if (accion === "no") {
      it.estado = "descartado"; await putItem(env, it); await quitarBotones();
      return decir(env, `❌ Descartado «${esc(it.titulo)}». Se queda privado en YouTube y no se publica.`);
    }
    return;
  }

  const texto = (msg.text || "").trim();
  const [orden, ...resto] = texto.split(/\s+/);
  const arg = texto.slice(orden.length).trim();
  const cmd = orden.startsWith("/") ? orden.split("@")[0].toLowerCase() : null;

  if (cmd === "/start" || cmd === "/ayuda" || cmd === "/help") return decir(env, AYUDA);
  if (cmd === "/idea") {
    if (!arg) return decir(env, "Escribe la idea después de /idea. Por ejemplo:\n/idea los animales más venenosos del mundo");
    const ideas = await leer(env, "ideas", []);
    ideas.push({ texto: arg, fecha: new Date().toISOString(), usada: false });
    await guardar(env, "ideas", ideas);
    return decir(env, `💡 Idea guardada. Tienes ${ideas.filter((i) => !i.usada).length} ideas sin usar.`);
  }
  if (cmd === "/ideas") {
    const ideas = (await leer(env, "ideas", [])).filter((i) => !i.usada);
    if (!ideas.length) return decir(env, "No hay ideas guardadas. Mándame una con /idea …");
    return decir(env, "💡 <b>Ideas sin usar</b>\n\n" + ideas.map((i, n) => `${n + 1}. ${esc(i.texto)}`).join("\n"));
  }
  if (cmd === "/pendientes") {
    const p = (await todos(env)).filter((i) => ["revision", "esperando_cambios", "cambios", "rehaciendo"].includes(i.estado));
    if (!p.length) return decir(env, "✅ No hay nada pendiente.");
    await decir(env, `📋 <b>Pendientes (${p.length})</b>\n\n` +
      p.map((i) => `• «${esc(i.titulo)}» — ${ESTADOS[i.estado]}\n   ${esc(fechaTexto(i.fecha_utc))}`).join("\n"));
    for (const i of p.filter((i) => i.estado === "revision"))
      await decir(env, fichaTexto(i), { reply_markup: botones(i.id) });
    return;
  }
  if (cmd === "/calendario") {
    const p = (await todos(env)).filter((i) => i.estado === "programado").sort((a, b) => a.fecha_utc.localeCompare(b.fecha_utc));
    if (!p.length) return decir(env, "📅 No hay nada programado todavía.");
    return decir(env, "📅 <b>Programado</b>\n\n" + p.map((i) => `• ${esc(fechaTexto(i.fecha_utc))} — «${esc(i.titulo)}»`).join("\n"));
  }
  if (cmd === "/listo") {
    const id = await leer(env, "esperando");
    const it = id && await getItem(env, id);
    if (!it || !(it.cambios || []).length) return decir(env, "No tengo cambios apuntados. Pulsa ✏️ Pedir cambios en el vídeo primero.");
    it.estado = "cambios"; await putItem(env, it); await env.DATOS.delete("esperando");
    return decir(env, `👍 Apuntado. Aplico los cambios a «${esc(it.titulo)}» en cuanto el PC esté encendido y te mando la versión nueva.`);
  }
  if (cmd) return decir(env, "No conozco esa orden. Escribe /ayuda para ver las que hay.");

  // texto libre o audio: ¿son cambios de un vídeo?
  const id = await leer(env, "esperando");
  const it = id && await getItem(env, id);
  const voz = msg.voice || msg.audio;
  if (it && it.estado === "esperando_cambios" && (texto || voz)) {
    it.cambios = it.cambios || [];
    it.cambios.push(voz ? { voz: voz.file_id, duracion: voz.duration, fecha: new Date().toISOString() }
                        : { texto, fecha: new Date().toISOString() });
    await putItem(env, it);
    return decir(env, (voz ? "🎙️ Audio apuntado." : "📝 Apuntado.") + " Si quieres añadir algo más, mándamelo. Cuando termines, escribe /listo.");
  }
  return decir(env, "No sé a qué vídeo va esto 🤔\n• Si es una idea: <b>/idea</b> y el texto.\n• Si son cambios: pulsa ✏️ Pedir cambios en el vídeo.");
}

// ---------- YouTube ----------
async function tokenGoogle(env) {
  const r = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    body: new URLSearchParams({ client_id: env.GOOGLE_CLIENT_ID, client_secret: env.GOOGLE_CLIENT_SECRET,
      refresh_token: env.GOOGLE_REFRESH_TOKEN, grant_type: "refresh_token" }),
  });
  const j = await r.json();
  if (!j.access_token) throw new Error("Google no me deja entrar: " + (j.error_description || j.error || r.status));
  return j.access_token;
}
async function programarEnYouTube(env, it) {
  const tok = await tokenGoogle(env);
  const r = await fetch("https://www.googleapis.com/youtube/v3/videos?part=status", {
    method: "PUT",
    headers: { Authorization: "Bearer " + tok, "content-type": "application/json" },
    body: JSON.stringify({ id: it.youtube_id, status: {
      privacyStatus: "private", publishAt: it.fecha_utc, embeddable: true,
      selfDeclaredMadeForKids: !!it.para_ninos, containsSyntheticMedia: !!it.sintetico } }),
  });
  if (!r.ok) throw new Error(`YouTube respondió ${r.status}: ${(await r.text()).slice(0, 300)}`);
}
async function aprobar(env, it, quitarBotones) {
  if (!it.fecha_utc || Date.parse(it.fecha_utc) < Date.now() + 20 * 60 * 1000) it.fecha_utc = await hueco(env, it.tipo, it.id);
  try {
    if (!it.youtube_id) throw new Error("no tengo el vídeo subido en YouTube");
    await programarEnYouTube(env, it);
  } catch (e) {
    return decir(env, `⚠️ No he podido programar «${esc(it.titulo)}»:\n${esc(e.message)}\n\nNo se ha publicado nada. Vuelve a pulsar ✅ más tarde o avísame.`);
  }
  it.estado = "programado"; it.aprobado = new Date().toISOString(); it.avisado = false;
  await putItem(env, it); await quitarBotones();
  const aviso = env.AUDITADO === "si" ? "" :
    "\n\nℹ️ Mientras Google no audite el proyecto, YouTube lo deja privado. A esa hora te aviso para que lo pongas <b>Público</b> con un toque en la app.";
  return decir(env, `📅 <b>Programado</b>: «${esc(it.titulo)}»\n🕒 ${esc(fechaTexto(it.fecha_utc))} (hora de España)\n▶️ https://youtu.be/${it.youtube_id}${aviso}`);
}

// ---------- avisos programados (cada 15 min) ----------
async function recordatorios(env) {
  const ahora = Date.now();
  for (const it of await todos(env)) {
    if (it.estado !== "programado" || it.avisado || Date.parse(it.fecha_utc) > ahora) continue;
    it.avisado = true; it.estado = "publicado"; await putItem(env, it);
    if (env.AUDITADO === "si")
      await decir(env, `🚀 Ya está publicado «${esc(it.titulo)}»\nhttps://youtu.be/${it.youtube_id}`);
    else
      await decir(env, `🔔 Es la hora de «${esc(it.titulo)}».\nAbre la app de YouTube → Tú → Tus vídeos → el vídeo → <b>Visibilidad: Público</b>.\n` +
        `https://youtu.be/${it.youtube_id}` + (it.comentario ? `\n\n📌 Comentario para fijar:\n${esc(it.comentario)}` : ""));
  }
}

// ---------- órdenes del PC ----------
async function pc(url, req, env) {
  const ruta = url.pathname.slice(4);
  const cuerpo = req.method === "POST" ? await req.json() : {};
  if (ruta === "hueco") {
    const id = url.searchParams.get("id");
    const it = id && await getItem(env, id);
    if (it && it.fecha_utc && Date.parse(it.fecha_utc) > Date.now() + 60 * 60 * 1000 && it.estado !== "descartado")
      return { ok: true, fecha_utc: it.fecha_utc, fecha_texto: fechaTexto(it.fecha_utc) };
    const f = await hueco(env, url.searchParams.get("tipo"), id);
    return { ok: true, fecha_utc: f, fecha_texto: fechaTexto(f) };
  }
  if (ruta === "revision") {         // el PC ya mandó el vídeo; aquí va la ficha con los botones
    const previo = await getItem(env, cuerpo.id);
    const it = { ...(previo || {}), ...cuerpo, estado: "revision", cambios: [],
      version: previo ? (previo.version || 1) + 1 : 1, enviado: new Date().toISOString() };
    if (previo && previo.cambios && previo.cambios.length) it.cambios_anteriores = [...(previo.cambios_anteriores || []), ...previo.cambios];
    await putItem(env, it);
    if ((await leer(env, "esperando")) === it.id) await env.DATOS.delete("esperando");
    await decir(env, fichaTexto(it), { reply_markup: botones(it.id) });
    return { ok: true, version: it.version, fecha_texto: fechaTexto(it.fecha_utc) };
  }
  if (ruta === "tareas") return { ok: true, tareas: (await todos(env)).filter((i) => i.estado === "cambios") };
  if (ruta === "estado") {
    const it = await getItem(env, cuerpo.id);
    if (!it) throw new Error("no existe " + cuerpo.id);
    if (cuerpo.estado) it.estado = cuerpo.estado;
    await putItem(env, it);
    if (cuerpo.nota) await decir(env, esc(cuerpo.nota));
    return { ok: true };
  }
  if (ruta === "avisar") { await decir(env, esc(cuerpo.texto)); return { ok: true }; }
  if (ruta === "ideas") {
    const ideas = await leer(env, "ideas", []);
    if (req.method === "POST" && Number.isInteger(cuerpo.usar)) {
      const sin = ideas.filter((i) => !i.usada);
      if (sin[cuerpo.usar]) { sin[cuerpo.usar].usada = true; await guardar(env, "ideas", ideas); }
    }
    return { ok: true, ideas: ideas.filter((i) => !i.usada) };
  }
  if (ruta === "items") return { ok: true, items: await todos(env) };
  throw new Error("ruta desconocida: " + ruta);
}
