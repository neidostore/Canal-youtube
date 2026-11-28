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
  aprobado: "✅ aprobado (pendiente de subir)", programado: "📅 programado", descartado: "❌ descartado", publicado: "✅ publicado",
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
    if (url.pathname === "/tiktok/callback") {   // vuelta de la autorización oficial de TikTok (no guarda contraseñas)
      const code = url.searchParams.get("code"), state = url.searchParams.get("state");
      if (!code || !state) return new Response("Falta el código de TikTok.", { status: 400 });
      await guardar(env, "tiktok_auth", { code, state, fecha: new Date().toISOString() });
      ctx.waitUntil(decir(env, "🔗 TikTok ha autorizado la conexión. El PC la termina en su próximo ciclo (o ejecuta <code>python -m autopilot tiktok vuelta</code>)."));
      return new Response("<meta charset=utf-8><h2>✅ Listo. Ya puedes cerrar esta página y volver a Telegram.</h2>",
        { headers: { "content-type": "text/html; charset=utf-8" } });
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
// Calendario efectivo: el que manda el PC (autopilot/config.toml) para short/largo; el antiguo para ranking/dosis
async function calendario(env) {
  const delPc = await leer(env, "calendario", null);
  return { ...CALENDARIO, ...(delPc || {}) };
}
// Próximos huecos libres (para «Cambiar fecha»)
async function huecosLibres(env, tipo, excluirId, n = 4) {
  const out = [];
  for (let i = 0; i < n; i++) {
    const f = await hueco(env, tipo, excluirId, out);
    out.push(f);
  }
  return out;
}
// Siguiente hueco libre del calendario para un tipo de vídeo
async function hueco(env, tipo, excluirId, ademas = []) {
  const slots = (await calendario(env))[tipo];
  if (!slots) throw new Error(`tipo desconocido: ${tipo} (usa short, largo, ranking o dosis)`);
  const ocupadas = new Set((await todos(env))
    .filter((i) => i.id !== excluirId && ["revision", "esperando_cambios", "cambios", "rehaciendo", "programado"].includes(i.estado))
    .map((i) => i.fecha_utc));
  for (const f of ademas) ocupadas.add(f);
  for (const f of (await leer(env, "calendario", {}))?.reservados || []) ocupadas.add(f);   // programados a mano
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
// La aprobación va ligada al vídeo Y a su versión: un botón de una versión vieja no vale.
function botones(id, version) {
  const v = version ? ":" + version : "";
  return { inline_keyboard: [
    [{ text: "✅ APROBAR Y PUBLICAR", callback_data: "ok:" + id + v }],
    [{ text: "✏️ SOLICITAR CAMBIOS", callback_data: "cam:" + id + v }, { text: "❌ RECHAZAR", callback_data: "no:" + id + v }],
    [{ text: "📜 GUION", callback_data: "g:" + id }, { text: "📚 FUENTES", callback_data: "f:" + id }, { text: "📅 FECHA", callback_data: "fe:" + id + v }],
    [{ text: "🖼️ MINIATURA", callback_data: "mi:" + id + v }, { text: "🎙️ VOZ", callback_data: "vo:" + id + v }],
  ] };
}
const TIPOS = { short: "Short", largo: "Vídeo largo", ranking: "Short de ranking", dosis: "Dosis (vídeo largo)" };
function fichaTexto(it) {
  let desc = it.descripcion || "";
  if (desc.length > 1800) desc = desc.slice(0, 1800) + "…";
  const mmss = (s) => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, "0")}`;
  return (it.prueba ? "🧪 <b>MODO PRUEBA</b> (no se subirá a YouTube)\n" : "") +
    `🎬 <b>Para revisar</b> · ${esc(it.id)} · versión ${it.version}\n\n` +
    `<b>Título:</b> ${esc(it.titulo)}\n` +
    `<b>Tipo:</b> ${esc(TIPOS[it.tipo] || it.tipo)}` + (it.duracion ? ` · ${mmss(it.duracion)}` : "") + "\n" +
    (it.puntuacion != null || it.nota_visual != null || it.nota_voz != null ?
      "<b>Calidad:</b> " + [it.puntuacion != null ? `${it.puntuacion}/100` : null, it.nota_visual != null ? `🖼️ visual ${it.nota_visual}` : null,
        it.nota_voz != null ? `🎙️ locución ${it.nota_voz}` : null].filter(Boolean).join(" · ") + "\n" : "") +
    (it.perfil_voz ? `<b>Voz:</b> perfil ${esc(it.perfil_voz)}\n` : "") +
    (it.plataformas ? `<b>Se publicará en:</b> ${esc(it.plataformas.join(" + "))}\n` : "") +
    (it.recomendacion ? `🤖 <b>Recomendación:</b> ${esc(it.recomendacion)}\n` : "") +
    `<b>Se publicaría:</b> ${esc(fechaTexto(it.fecha_utc))}\n` +
    (it.coste != null ? `<b>Coste de producción:</b> ${Number(it.coste).toFixed(2)} €\n` : "") +
    ((it.avisos_calidad || []).length ? `⚠️ ${esc(it.avisos_calidad.join(" · "))}\n` : "") +
    `\n<b>Descripción:</b>\n${esc(desc)}\n\n` +
    (it.comentario ? `📌 <b>Comentario fijado:</b> ${esc(it.comentario)}\n` : "") +
    (it.youtube_id ? `▶️ En YouTube (privado): https://youtu.be/${it.youtube_id}` : "");
}
const AYUDA =
  "🤖 <b>Shock Mental · Revisión</b>\n\n" +
  "Cuando los agentes terminan un vídeo y pasa el control de calidad, te llega aquí con su portada y estos botones:\n" +
  "✅ <b>Aprobar y programar</b>: se programa en YouTube en la fecha indicada.\n" +
  "✏️ <b>Solicitar cambios</b>: me escribes o me mandas un audio; los agentes hacen una versión nueva.\n" +
  "❌ <b>Rechazar</b>: no se publica; te pregunto el motivo para que no se repita.\n" +
  "📜 <b>Ver guion</b> · 📚 <b>Ver fuentes</b> · 📅 <b>Cambiar fecha</b>\n\n" +
  "<b>Órdenes:</b>\n" +
  "/panel — progreso del canal, objetivos y monetización\n" +
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
    const [accion, id, extra] = (cb.data || "").split(":");
    if (accion === "cr") {   // el gerente aprueba publicar una respuesta del Community Manager
      const ok = await leer(env, "respuestas_ok", []);
      if (!ok.includes(id)) ok.push(id);
      await guardar(env, "respuestas_ok", ok);
      return decir(env, "💬 Respuesta aprobada. La publico en el próximo ciclo del PC.");
    }
    if (accion === "vz") {   // elección del perfil oficial de locución (A/B/C)
      await guardar(env, "voz_elegida", { letra: id, fecha: new Date().toISOString() });
      return decir(env, `🎙️ Elegida la interpretación <b>${esc(id)}</b>. La aplico como voz oficial en el próximo ciclo del PC.`);
    }
    // Ajustes de miniatura y voz: generan una versión nueva sin pasar por el guionista
    const ajustes = { mz: (x) => `[miniatura] ${x}`, mr: () => "[miniatura] regenerar", vp: (x) => `[voz] ${x}`, vr: () => "[voz] regenerar" };
    if (ajustes[accion]) {
      const it2 = await getItem(env, id);
      if (!it2) return decir(env, "No encuentro ese vídeo.");
      if (!["revision", "esperando_cambios"].includes(it2.estado))
        return decir(env, `«${esc(it2.titulo)}» ya está ${ESTADOS[it2.estado] || it2.estado}.`);
      it2.estado = "cambios"; it2.cambios = [{ texto: ajustes[accion](extra), fecha: new Date().toISOString() }];
      await putItem(env, it2);
      return decir(env, `🛠️ Apuntado (${esc(it2.cambios[0].texto)}) para «${esc(it2.titulo)}». Te llega la versión nueva en el próximo ciclo.`);
    }
    const it = await getItem(env, id);
    if (!it) return decir(env, "No encuentro ese vídeo.");
    // Solo lectura: sirven en cualquier estado
    if (accion === "g") return decir(env, `📜 <b>Guion</b> · ${esc(it.titulo)} (v${it.version})\n\n${esc(it.guion_texto || "No tengo el guion guardado para este vídeo.")}`);
    if (accion === "f") return decir(env, `📚 <b>Fuentes</b> · ${esc(it.titulo)}\n\n${esc(it.fuentes_texto || "No tengo las fuentes guardadas para este vídeo.")}`);
    // Aprobación ligada a la versión: los botones de una versión anterior ya no valen
    const version = ["ok", "cam", "no", "fe", "mi", "vo"].includes(accion) ? extra : null;
    if (version && String(version) !== String(it.version))
      return decir(env, `⚠️ Ese botón es de la versión ${version} de «${esc(it.titulo)}», pero la actual es la ${it.version}. Usa los botones del último mensaje.`);
    if (accion === "fs") {   // fecha elegida: fs:id:minutosUTC
      if (!["revision", "esperando_cambios", "programado", "aprobado"].includes(it.estado))
        return decir(env, `«${esc(it.titulo)}» ya está ${ESTADOS[it.estado] || it.estado}.`);
      it.fecha_utc = new Date(Number(extra) * 60000).toISOString().replace(/\.\d+Z$/, ".000Z");
      await putItem(env, it);
      if (it.estado === "programado" && it.youtube_id) {
        try { await programarEnYouTube(env, it); } catch (e) { return decir(env, `⚠️ No he podido cambiar la fecha en YouTube: ${esc(e.message)}`); }
      }
      return decir(env, `📅 Nueva fecha para «${esc(it.titulo)}»: <b>${esc(fechaTexto(it.fecha_utc))}</b>`);
    }
    if (accion === "mi") {
      const cs = it.miniaturas || [];
      return decir(env, cs.length ? `🖼️ Conceptos de miniatura de «${esc(it.titulo)}» (te los mandé encima de la ficha):\n` +
        cs.map((c) => `${c.id}${c.id === it.miniatura_elegida ? " ✅" : ""} · ${esc(c.idea)} (${c.nota}/100)`).join("\n") :
        "🖼️ Este vídeo usa como portada un fotograma (Short). Puedes regenerarla:", { reply_markup: { inline_keyboard: [
        cs.map((c) => ({ text: "Usar " + c.id, callback_data: `mz:${it.id}:${c.id}` })),
        [{ text: "🔄 Regenerar miniatura", callback_data: `mr:${it.id}` }]].filter((f) => f.length) } });
    }
    if (accion === "vo") {
      return decir(env, `🎙️ Voz de «${esc(it.titulo)}»: ahora perfil ${esc(it.perfil_voz || "oficial")}.`, { reply_markup: { inline_keyboard: [
        ["A", "B", "C"].map((l) => ({ text: "Perfil " + l, callback_data: `vp:${it.id}:${l}` })),
        [{ text: "🔄 Regenerar locución", callback_data: `vr:${it.id}` }]] } });
    }
    if (accion === "fe") {
      const libres = await huecosLibres(env, it.tipo, it.id, 4);
      return decir(env, `📅 ¿Cuándo publico «${esc(it.titulo)}»?`, { reply_markup: { inline_keyboard:
        libres.map((f) => [{ text: fechaTexto(f), callback_data: `fs:${it.id}:${Math.round(Date.parse(f) / 60000)}` }]) } });
    }
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
      await guardar(env, "motivo", id);
      return decir(env, `❌ Rechazado «${esc(it.titulo)}». No se publica.\n\n¿Por qué? Escríbeme el motivo en una frase (o un audio). ` +
        "Lo apunto para que no se repita. Si no quieres decirlo, escribe /saltar.");
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
      await decir(env, fichaTexto(i), { reply_markup: botones(i.id, i.version) });
    return;
  }
  if (cmd === "/panel") {
    const p = await leer(env, "panel", null);
    if (!p) return decir(env, "📊 Todavía no tengo el panel. Se actualiza cada vez que el PC hace su ciclo diario.");
    return decir(env, `<pre>${esc(p.texto)}</pre>\n<i>Actualizado: ${esc(fechaTexto(p.fecha))}</i>`);
  }
  if (cmd === "/tiktok") {
    return decir(env, "🎵 <b>Conectar TikTok</b>\n1. Crea la app gratuita en developers.tiktok.com (te guío paso a paso desde Claude).\n" +
      "2. Yo te mando un enlace oficial de TikTok: entras con TU cuenta de Shock Mental y pulsas Autorizar.\n" +
      "3. Nunca me des tu contraseña: TikTok solo me da un permiso para subir vídeos, que puedes retirar cuando quieras.\n" +
      "Mientras la app no pase la auditoría de TikTok, los vídeos llegan a tus <b>borradores</b> y los publicas con 2 toques.");
  }
  if (cmd === "/organigrama") {
    return decir(env, "🏢 <b>Shock Mental</b>\n👤 Gerente general: tú (aprobar contenido, gastos, cambios importantes)\n" +
      "🤖 CEO: coordina todo y te informa\n• Contenido: investigador, verificador, guionistas\n• Producción: productor, Thumbnail Director, Voice Director, calidad\n" +
      "• Distribución: YouTube, TikTok, Community Manager (borradores)\n• Analítica: crecimiento y monetización");
  }
  if (cmd === "/saltar") {
    if (await leer(env, "motivo")) await env.DATOS.delete("motivo");
    return decir(env, "👍 Vale, sin motivo.");
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

  // texto libre o audio: ¿es el motivo de un rechazo?
  const idMotivo = await leer(env, "motivo");
  if (idMotivo && (texto || msg.voice || msg.audio)) {
    const r = await getItem(env, idMotivo);
    if (r) {
      r.motivo_rechazo = texto || "(audio)"; if (msg.voice || msg.audio) r.motivo_voz = (msg.voice || msg.audio).file_id;
      await putItem(env, r);
    }
    await env.DATOS.delete("motivo");
    return decir(env, "📝 Apuntado. Los agentes lo tendrán en cuenta para que no se repita.");
  }
  // ¿son cambios de un vídeo?
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
  if (it.prueba || !it.youtube_id) {
    // Modo prueba, o el vídeo aún no está en YouTube: queda APROBADO (esta versión). El PC lo sube en privado
    // y lo programa en su siguiente ciclo (solo en modo producción). Nunca se publica nada sin este ✅.
    it.estado = "aprobado"; it.aprobado = new Date().toISOString(); it.version_aprobada = it.version;
    await putItem(env, it); await quitarBotones();
    return decir(env, (it.prueba ? "🧪 <b>Aprobado en modo prueba</b>: no se sube a YouTube.\n" :
      "✅ <b>Aprobado</b>. Lo subo y lo programo en el próximo ciclo del PC.\n") +
      `«${esc(it.titulo)}» · ${esc(fechaTexto(it.fecha_utc))}`);
  }
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
      version: cuerpo.version || (previo ? (previo.version || 1) + 1 : 1), enviado: new Date().toISOString() };
    if (previo && previo.cambios && previo.cambios.length) it.cambios_anteriores = [...(previo.cambios_anteriores || []), ...previo.cambios];
    await putItem(env, it);
    if ((await leer(env, "esperando")) === it.id) await env.DATOS.delete("esperando");
    await decir(env, fichaTexto(it), { reply_markup: botones(it.id, it.version) });
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
  if (ruta === "calendario") {   // el PC manda el calendario de autopilot/config.toml
    for (const k of Object.keys(cuerpo)) if (!Array.isArray(cuerpo[k])) throw new Error("calendario mal formado");
    await guardar(env, "calendario", cuerpo); return { ok: true };
  }
  if (ruta === "ajustes") return { ok: true, voz_elegida: await leer(env, "voz_elegida", null),
    respuestas_ok: await leer(env, "respuestas_ok", []) };
  if (ruta === "respondidas") { await guardar(env, "respuestas_ok", []); return { ok: true }; }
  if (ruta === "tiktok_code") { const a = await leer(env, "tiktok_auth", null); if (a) await env.DATOS.delete("tiktok_auth"); return { ok: true, auth: a }; }
  if (ruta === "panel") { await guardar(env, "panel", { texto: String(cuerpo.texto || ""), fecha: new Date().toISOString() }); return { ok: true }; }
  if (ruta === "programado") {   // el PC subió y programó en YouTube un vídeo ya aprobado
    const it = await getItem(env, cuerpo.id);
    if (!it) throw new Error("no existe " + cuerpo.id);
    if (it.estado !== "aprobado" || String(it.version_aprobada) !== String(cuerpo.version))
      throw new Error("ese vídeo/versión no está aprobado: no se programa");
    it.youtube_id = cuerpo.youtube_id; it.estado = "programado"; it.avisado = false;
    await putItem(env, it);
    await decir(env, `📅 <b>Programado</b>: «${esc(it.titulo)}»\n🕒 ${esc(fechaTexto(it.fecha_utc))}\n▶️ https://youtu.be/${it.youtube_id}`);
    return { ok: true };
  }
  throw new Error("ruta desconocida: " + ruta);
}
