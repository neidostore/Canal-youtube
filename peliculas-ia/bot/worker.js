// =====================================================================================
// Bot de revisión de NEIDO STUDIO (Telegram) — Cloudflare Worker
// Solo para el canal Neido Studio. Solo responde al dueño (OWNER_ID).
//
// Configuración en Cloudflare (Settings → Variables and Secrets):
//   Secretos:  TELEGRAM_TOKEN   clave del bot que da BotFather
//              WEBHOOK_SECRET   una palabra secreta inventada (letras y números)
//              CLAUDE_KEY       otra palabra secreta inventada, para que Claude hable con el bot
//              OWNER_ID         tu ID de Telegram (el bot te lo dice con /id; mientras no esté puesto, responde a cualquiera solo con su ID)
//   Opcionales (YouTube, más adelante): YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
//   Base de datos D1 enlazada con el nombre: DB
//
// Instalación del webhook: abrir en el navegador  https://<tu-worker>.workers.dev/instalar?clave=<WEBHOOK_SECRET>
// =====================================================================================

const ESTADOS = {
  pendiente: "🕓 Pendiente de revisar",
  cambios: "✏️ Cambios pedidos",
  aprobado: "✅ Aprobado (se programará en la próxima pasada)",
  programado: "📅 Programado en YouTube",
  publicado: "🎬 Publicado",
  descartado: "❌ Descartado",
};

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    try {
      await prepararBD(env);
      if (url.pathname === "/instalar") return instalar(url, env);
      if (url.pathname === `/telegram/${env.WEBHOOK_SECRET}` && req.method === "POST") {
        if (req.headers.get("X-Telegram-Bot-Api-Secret-Token") !== env.WEBHOOK_SECRET) return new Response("no", { status: 403 });
        await atenderTelegram(await req.json(), env);
        return new Response("ok");
      }
      if (url.pathname.startsWith("/api/")) {
        if (req.headers.get("Authorization") !== `Bearer ${env.CLAUDE_KEY}`) return json({ error: "no autorizado" }, 401);
        return await api(url, req, env);
      }
      return new Response("Neido Studio · bot de revisión");
    } catch (e) {
      return json({ error: String(e && e.stack || e) }, 500);
    }
  },
};

// ---------------------------------------------------------------- base de datos
async function prepararBD(env) {
  await env.DB.batch([
    env.DB.prepare(`CREATE TABLE IF NOT EXISTS revisiones (
      id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, titulo TEXT, descripcion TEXT, etiquetas TEXT,
      version INTEGER DEFAULT 1, estado TEXT DEFAULT 'pendiente', enlace TEXT, publicar_en TEXT, youtube_id TEXT,
      creado TEXT DEFAULT (datetime('now')), actualizado TEXT DEFAULT (datetime('now')))`),
    env.DB.prepare(`CREATE TABLE IF NOT EXISTS cambios (
      id INTEGER PRIMARY KEY AUTOINCREMENT, revision_id INTEGER, texto TEXT, voz_file_id TEXT,
      atendido INTEGER DEFAULT 0, creado TEXT DEFAULT (datetime('now')))`),
    env.DB.prepare(`CREATE TABLE IF NOT EXISTS ideas (
      id INTEGER PRIMARY KEY AUTOINCREMENT, texto TEXT, usada INTEGER DEFAULT 0, creado TEXT DEFAULT (datetime('now')))`),
    env.DB.prepare(`CREATE TABLE IF NOT EXISTS ajustes (clave TEXT PRIMARY KEY, valor TEXT)`),
  ]);
}
const ajuste = async (env, k) => (await env.DB.prepare("SELECT valor FROM ajustes WHERE clave=?").bind(k).first())?.valor ?? null;
const fijar = (env, k, v) => env.DB.prepare("INSERT INTO ajustes(clave,valor) VALUES(?,?) ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor").bind(k, v).run();

// ---------------------------------------------------------------- Telegram
async function tg(env, metodo, datos) {
  const r = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/${metodo}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(datos),
  });
  return r.json();
}
const decir = (env, texto, extra = {}) => tg(env, "sendMessage", { chat_id: env.OWNER_ID, text: texto, parse_mode: "HTML", disable_web_page_preview: true, ...extra });
const esc = (t) => String(t ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const botones = (id) => ({ inline_keyboard: [[
  { text: "✅ Aprobar", callback_data: `aprobar:${id}` },
  { text: "✏️ Pedir cambios", callback_data: `cambios:${id}` },
  { text: "❌ Descartar", callback_data: `descartar:${id}` },
]] });

async function instalar(url, env) {
  if (url.searchParams.get("clave") !== env.WEBHOOK_SECRET) return new Response("Clave incorrecta", { status: 403 });
  const base = `${url.protocol}//${url.host}`;
  const w = await tg(env, "setWebhook", { url: `${base}/telegram/${env.WEBHOOK_SECRET}`, secret_token: env.WEBHOOK_SECRET,
    allowed_updates: ["message", "callback_query"], drop_pending_updates: true });
  const c = await tg(env, "setMyCommands", { commands: [
    { command: "pendientes", description: "Lo que espera tu revisión" },
    { command: "idea", description: "Guardar una idea: /idea tu idea" },
    { command: "ideas", description: "Ver la lista de ideas" },
    { command: "id", description: "Ver tu ID de Telegram" },
    { command: "ayuda", description: "Cómo funciona el bot" },
  ] });
  return new Response(`Webhook: ${w.ok ? "OK" : JSON.stringify(w)}\nComandos: ${c.ok ? "OK" : JSON.stringify(c)}\n\nYa puedes escribir /start al bot.`);
}

const AYUDA = `<b>Neido Studio · Revisión</b> 🎬
Te mando cada película y cada Short para que los revises.

Debajo de cada uno tienes:
✅ <b>Aprobar</b>: lo programo en YouTube y te confirmo la fecha.
✏️ <b>Pedir cambios</b>: después me escribes o me mandas un audio con lo que quieres cambiar.
❌ <b>Descartar</b>: no se publica.

Comandos:
/pendientes — lo que espera tu revisión
/idea <i>texto</i> — guardar una idea para próximos vídeos
/ideas — ver las ideas guardadas
/id — tu ID de Telegram

ℹ️ Claude revisa el bot cada hora: los cambios y las publicaciones se hacen en la siguiente pasada.`;

async function atenderTelegram(u, env) {
  const de = u.message?.from?.id ?? u.callback_query?.from?.id;
  const chat = u.message?.chat?.id ?? u.callback_query?.message?.chat?.id;
  // Mientras no hay dueño configurado, el bot solo dice el ID a quien le escriba (para la instalación).
  if (!env.OWNER_ID) {
    if (chat) await tg(env, "sendMessage", { chat_id: chat, text: `Tu ID de Telegram es: ${de}\nCópialo en Cloudflare como OWNER_ID.` });
    return;
  }
  if (String(de) !== String(env.OWNER_ID)) return; // cualquier otra persona: silencio total

  if (u.callback_query) return botonPulsado(u.callback_query, env);
  const m = u.message; if (!m) return;
  const texto = (m.text || "").trim();
  const cmd = (texto.match(/^\/(\w+)(@\w+)?/) || [])[1]?.toLowerCase();
  const resto = texto.replace(/^\/\w+(@\w+)?/, "").trim();

  if (cmd === "start" || cmd === "ayuda" || cmd === "help") return decir(env, AYUDA);
  if (cmd === "id") return decir(env, `Tu ID de Telegram es <code>${de}</code>`);
  if (cmd === "idea") {
    const idea = resto;
    if (!idea) return decir(env, "Escribe la idea detrás del comando, por ejemplo:\n<code>/idea Un vikingo en un centro comercial</code>");
    const r = await env.DB.prepare("INSERT INTO ideas(texto) VALUES(?)").bind(idea).run();
    return decir(env, `💡 Idea nº ${r.meta.last_row_id} guardada. La tendré en cuenta para los próximos vídeos.`);
  }
  if (cmd === "ideas") {
    const { results } = await env.DB.prepare("SELECT id,texto,usada FROM ideas ORDER BY id DESC LIMIT 30").all();
    if (!results.length) return decir(env, "Todavía no hay ideas. Guarda una con /idea");
    return decir(env, "💡 <b>Ideas</b>\n" + results.map(i => `${i.usada ? "✔️" : "•"} ${i.id}. ${esc(i.texto)}`).join("\n"));
  }
  if (cmd === "pendientes") return listarPendientes(env);

  // Texto o audio: si se estaban pidiendo cambios, se guardan como cambios de esa revisión
  const esperando = await ajuste(env, "esperando_cambios");
  if (esperando && (texto || m.voice || m.audio)) {
    const voz = m.voice?.file_id || m.audio?.file_id || null;
    await env.DB.prepare("INSERT INTO cambios(revision_id,texto,voz_file_id) VALUES(?,?,?)").bind(Number(esperando), texto || null, voz).run();
    await fijar(env, "esperando_cambios", "");
    return decir(env, `📝 Anotado para la revisión nº ${esperando}${voz ? " (audio recibido)" : ""}. Lo aplicaré en la próxima pasada (como mucho, 1 hora) y te mandaré la versión nueva.\n\nSi quieres añadir algo más, vuelve a pulsar ✏️ Pedir cambios.`);
  }
  return decir(env, "No he entendido el mensaje. Usa /ayuda para ver lo que puedo hacer.\nSi quieres pedir cambios, pulsa primero ✏️ en el vídeo correspondiente.");
}

async function botonPulsado(q, env) {
  const [accion, idTxt] = (q.data || "").split(":");
  const id = Number(idTxt);
  const rev = await env.DB.prepare("SELECT * FROM revisiones WHERE id=?").bind(id).first();
  await tg(env, "answerCallbackQuery", { callback_query_id: q.id });
  if (!rev) return decir(env, "No encuentro esa revisión.");
  if (["programado", "publicado"].includes(rev.estado)) return decir(env, `La revisión nº ${id} ya está ${ESTADOS[rev.estado].toLowerCase()}.`);
  const poner = (e) => env.DB.prepare("UPDATE revisiones SET estado=?, actualizado=datetime('now') WHERE id=?").bind(e, id).run();

  if (accion === "aprobar") {
    await poner("aprobado");
    return decir(env, `✅ <b>${esc(rev.titulo)}</b> aprobado. En la próxima pasada lo programo en YouTube y te confirmo el día y la hora.`);
  }
  if (accion === "cambios") {
    await poner("cambios"); await fijar(env, "esperando_cambios", String(id));
    return decir(env, `✏️ ¿Qué quieres cambiar de <b>${esc(rev.titulo)}</b>?\nEscríbemelo o mándame un audio.`);
  }
  if (accion === "descartar") {
    return decir(env, `¿Seguro que quieres descartar <b>${esc(rev.titulo)}</b>? No se publicará.`, { reply_markup: { inline_keyboard: [[
      { text: "Sí, descartar", callback_data: `descartar_ok:${id}` }, { text: "No, dejarlo", callback_data: `nada:${id}` }]] } });
  }
  if (accion === "descartar_ok") { await poner("descartado"); return decir(env, `❌ Descartado: ${esc(rev.titulo)}`); }
  if (accion === "nada") return decir(env, "De acuerdo, sigue pendiente.");
}

async function listarPendientes(env) {
  const { results } = await env.DB.prepare(
    "SELECT id,tipo,titulo,estado,version,publicar_en FROM revisiones WHERE estado IN ('pendiente','cambios','aprobado','programado') ORDER BY id").all();
  if (!results.length) return decir(env, "No hay nada pendiente. 🎉");
  const lineas = results.map(r => `<b>${r.id}.</b> ${r.tipo === "short" ? "📱" : "🎬"} ${esc(r.titulo)} (v${r.version})\n    ${ESTADOS[r.estado]}${r.publicar_en ? ` · ${esc(r.publicar_en)}` : ""}`);
  return decir(env, "📋 <b>Pendientes</b>\n\n" + lineas.join("\n\n"));
}

// ---------------------------------------------------------------- API para Claude
async function api(url, req, env) {
  const ruta = url.pathname.slice(5);

  // Enviar un vídeo a revisión (multipart: campo "video" opcional + campo "datos" con JSON)
  if (ruta === "revision" && req.method === "POST") {
    const form = await req.formData();
    const d = JSON.parse(form.get("datos"));
    let id = d.id;
    if (id) await env.DB.prepare("UPDATE revisiones SET titulo=?,descripcion=?,etiquetas=?,version=version+1,estado='pendiente',enlace=?,actualizado=datetime('now') WHERE id=?")
      .bind(d.titulo, d.descripcion, (d.etiquetas || []).join(", "), d.enlace || null, id).run();
    else id = (await env.DB.prepare("INSERT INTO revisiones(tipo,titulo,descripcion,etiquetas,enlace) VALUES(?,?,?,?,?)")
      .bind(d.tipo, d.titulo, d.descripcion, (d.etiquetas || []).join(", "), d.enlace || null).run()).meta.last_row_id;
    const rev = await env.DB.prepare("SELECT * FROM revisiones WHERE id=?").bind(id).first();
    const cabecera = `${rev.tipo === "short" ? "📱 SHORT" : "🎬 PELÍCULA"} · revisión nº ${id} · versión ${rev.version}`;
    const video = form.get("video");
    if (video && typeof video !== "string") {
      const f = new FormData();
      f.append("chat_id", env.OWNER_ID); f.append("caption", `${cabecera}\n${rev.titulo}`.slice(0, 1000));
      f.append("supports_streaming", "true"); f.append("video", video, video.name || "video.mp4");
      const r = await (await fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/sendVideo`, { method: "POST", body: f })).json();
      if (!r.ok) return json({ error: "Telegram rechazó el vídeo", detalle: r }, 502);
    }
    const ficha = `<b>${esc(cabecera)}</b>\n\n<b>Título:</b> ${esc(rev.titulo)}\n\n<b>Descripción:</b>\n${esc(rev.descripcion)}\n\n<b>Etiquetas:</b> ${esc(rev.etiquetas)}` +
      (rev.enlace ? `\n\n🔗 <a href="${esc(rev.enlace)}">Ver el vídeo</a>` : "") + (d.nota ? `\n\n🛠 ${esc(d.nota)}` : "");
    await decir(env, ficha.slice(0, 4000), { reply_markup: botones(id) });
    return json({ ok: true, id });
  }

  // Lo que Claude tiene que hacer: aprobados sin programar y cambios sin atender
  if (ruta === "tareas") {
    const aprobados = (await env.DB.prepare("SELECT * FROM revisiones WHERE estado='aprobado' ORDER BY id").all()).results;
    const cambios = (await env.DB.prepare(
      "SELECT c.*, r.titulo, r.tipo, r.version FROM cambios c JOIN revisiones r ON r.id=c.revision_id WHERE c.atendido=0 ORDER BY c.id").all()).results;
    const ideas = (await env.DB.prepare("SELECT * FROM ideas WHERE usada=0 ORDER BY id").all()).results;
    return json({ aprobados, cambios, ideas });
  }

  // Descargar un audio de Telegram (para transcribirlo)
  if (ruta.startsWith("voz/")) {
    const info = await tg(env, "getFile", { file_id: ruta.slice(4) });
    if (!info.ok) return json(info, 502);
    return fetch(`https://api.telegram.org/file/bot${env.TELEGRAM_TOKEN}/${info.result.file_path}`);
  }

  // Marcar cambios como atendidos, actualizar estado de una revisión, ideas usadas
  if (ruta === "actualizar" && req.method === "POST") {
    const d = await req.json();
    if (d.cambios_atendidos?.length) for (const c of d.cambios_atendidos) await env.DB.prepare("UPDATE cambios SET atendido=1 WHERE id=?").bind(c).run();
    if (d.ideas_usadas?.length) for (const i of d.ideas_usadas) await env.DB.prepare("UPDATE ideas SET usada=1 WHERE id=?").bind(i).run();
    if (d.id) await env.DB.prepare("UPDATE revisiones SET estado=COALESCE(?,estado), publicar_en=COALESCE(?,publicar_en), youtube_id=COALESCE(?,youtube_id), actualizado=datetime('now') WHERE id=?")
      .bind(d.estado || null, d.publicar_en || null, d.youtube_id || null, d.id).run();
    if (d.mensaje) await decir(env, d.mensaje);
    return json({ ok: true });
  }

  // Mensaje libre al dueño
  if (ruta === "mensaje" && req.method === "POST") { const d = await req.json(); return json(await decir(env, d.texto)); }

  // Token de acceso de YouTube (lo genera el bot con los secretos; Claude nunca ve el refresh token)
  if (ruta === "youtube-token") {
    if (!env.YT_REFRESH_TOKEN) return json({ error: "YouTube todavía no está configurado" }, 409);
    const r = await fetch("https://oauth2.googleapis.com/token", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ client_id: env.YT_CLIENT_ID, client_secret: env.YT_CLIENT_SECRET, refresh_token: env.YT_REFRESH_TOKEN, grant_type: "refresh_token" }) });
    const t = await r.json();
    return json({ access_token: t.access_token, expires_in: t.expires_in, error: t.error });
  }

  return json({ error: "ruta desconocida" }, 404);
}

function json(o, status = 200) {
  return new Response(JSON.stringify(o), { status, headers: { "Content-Type": "application/json; charset=utf-8" } });
}
