// =====================================================================================
// Bot de revisión de NEIDO STUDIO (Telegram) — Cloudflare Worker
// Solo para el canal Neido Studio. Solo responde al dueño (OWNER_ID).
//
// Configuración en Cloudflare (Settings → Variables and Secrets):
//   Secretos:  TELEGRAM_TOKEN   clave del bot que da BotFather
//              WEBHOOK_SECRET   una palabra secreta inventada (letras y números)
//              CLAUDE_KEY       otra palabra secreta inventada, para que Claude hable con el bot
//              OWNER_ID         (opcional) tu ID de Telegram. Si no se pone, el PRIMERO que escriba /start queda como dueño
//                               y nadie más puede usar el bot.
//   Variable:  BASE_URL         dirección del bot (https://neido-bot.<subdominio>.workers.dev), para activar el webhook
//   Tarea programada (cron) cada minuto: comprueba que el webhook esté activo y, si no, lo activa.
//   Opcionales (YouTube, más adelante): YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
//   Almacenamiento KV enlazado con el nombre: KV  (todo el estado se guarda en una sola clave JSON)
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
      env.OWNER = env.OWNER_ID || (await leer(env)).ajustes.dueno || null;
      if (url.pathname === "/instalar") return instalar(url, env);
      if (url.pathname === "/configurar") return configurarYouTube(url, req, env);
      if (url.pathname === "/oauth/callback") return callbackYouTube(url, env);
      if (url.pathname === `/telegram/${env.WEBHOOK_SECRET}` && req.method === "POST") {
        if (req.headers.get("X-Telegram-Bot-Api-Secret-Token") !== env.WEBHOOK_SECRET) return new Response("no", { status: 403 });
        await atenderTelegram(await req.json(), env);
        return new Response("ok");
      }
      if (url.pathname.startsWith("/api/")) {
        if (req.headers.get("Authorization") !== `Bearer ${env.CLAUDE_KEY}`) return json({ error: "no autorizado" }, 401);
        return await api(url, req, env);
      }
      if (url.pathname === "/privacidad") return pagina(`<h1>Política de privacidad · Neido Studio Publicador</h1>
<p><i>Última actualización: 24 de noviembre de 2026</i></p>
<p>Neido Studio Publicador es una herramienta privada del canal de YouTube <b>Neido Studio</b>. La usa únicamente su propietario para revisar y programar la publicación de sus propios vídeos.</p>
<h3>Qué datos usa</h3><p>Con el permiso del propietario, accede a su canal de YouTube solo para <b>subir vídeos</b> y <b>leer el nombre del canal</b>. No accede a datos de otras personas.</p>
<h3>Dónde se guardan</h3><p>La autorización de YouTube se guarda cifrada en la cuenta de Cloudflare del propietario. No se vende, no se comparte con terceros y no se usa para publicidad.</p>
<h3>Cómo revocarlo</h3><p>El propietario puede retirar el acceso en cualquier momento desde <a style="color:#C9A46A" href="https://myaccount.google.com/permissions">myaccount.google.com/permissions</a>.</p>
<p>El uso de los datos de las API de Google cumple la <a style="color:#C9A46A" href="https://developers.google.com/terms/api-services-user-data-policy">Política de datos de usuario de los servicios de API de Google</a>, incluidos los requisitos de uso limitado.</p>`);
      return pagina(`<h1>🎬 Neido Studio</h1><p><b>Películas imposibles.</b></p><p>Herramienta privada de revisión y publicación del canal de YouTube Neido Studio.</p>
<p><a style="color:#C9A46A" href="/privacidad">Política de privacidad</a></p>`);
    } catch (e) {
      return json({ error: String(e && e.stack || e) }, 500);
    }
  },
  // Cada minuto: si el webhook no apunta a este bot, lo activa (así la instalación no necesita pasos manuales)
  async scheduled(evento, env) {
    if (!env.BASE_URL || !env.TELEGRAM_TOKEN) return;
    const esperado = `${env.BASE_URL}/telegram/${env.WEBHOOK_SECRET}`;
    const info = await tg(env, "getWebhookInfo", {});
    const diag = { hora: new Date().toISOString(), getWebhookInfo: info.ok ? { url_ok: info.result.url === esperado,
      pendientes: info.result.pending_update_count, ultimo_error: info.result.last_error_message || null } : info };
    if (!(info.ok && info.result.url === esperado)) {
      const r = await instalar(new URL(`${env.BASE_URL}/instalar?clave=${env.WEBHOOK_SECRET}`), env);
      diag.instalar = await r.text();
    }
    // diagnóstico legible por Claude desde la API de Cloudflare (sin datos secretos)
    await env.KV.put("diagnostico", JSON.stringify(diag));
  },
};

// ---------------------------------------------------------------- almacenamiento (KV)
// Un bot personal mueve muy pocos datos: se guarda todo en una sola clave JSON.
const VACIO = () => ({ seq: { rev: 0, cambio: 0, idea: 0 }, revisiones: [], cambios: [], ideas: [], ajustes: {} });
async function leer(env) { return (await env.KV.get("estado", "json")) || VACIO(); }
async function guardar(env, e) { await env.KV.put("estado", JSON.stringify(e)); }
const ahora = () => new Date().toISOString().slice(0, 16).replace("T", " ");

// ---------------------------------------------------------------- Telegram
async function tg(env, metodo, datos) {
  const r = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/${metodo}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(datos),
  });
  return r.json();
}
const decir = (env, texto, extra = {}) => tg(env, "sendMessage", { chat_id: env.OWNER, text: texto, parse_mode: "HTML", disable_web_page_preview: true, ...extra });
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
  // Sin dueño todavía: el primero que escriba se queda como dueño (el bot es nuevo y nadie más lo conoce).
  if (!env.OWNER) {
    if (!de || u.message?.chat?.type !== "private") return;
    const e = await leer(env); e.ajustes.dueno = de; await guardar(env, e); env.OWNER = de;
    await decir(env, `🔐 Listo: a partir de ahora este bot solo te responde a ti (ID ${de}).`);
    return decir(env, AYUDA);
  }
  if (String(de) !== String(env.OWNER)) return; // cualquier otra persona: silencio total

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
    const e = await leer(env); const n = ++e.seq.idea;
    e.ideas.push({ id: n, texto: idea, usada: 0, creado: ahora() }); await guardar(env, e);
    return decir(env, `💡 Idea nº ${n} guardada. La tendré en cuenta para los próximos vídeos.`);
  }
  if (cmd === "ideas") {
    const results = (await leer(env)).ideas.slice(-30).reverse();
    if (!results.length) return decir(env, "Todavía no hay ideas. Guarda una con /idea");
    return decir(env, "💡 <b>Ideas</b>\n" + results.map(i => `${i.usada ? "✔️" : "•"} ${i.id}. ${esc(i.texto)}`).join("\n"));
  }
  if (cmd === "pendientes") return listarPendientes(env);

  // Texto o audio: si se estaban pidiendo cambios, se guardan como cambios de esa revisión
  const e = await leer(env);
  const esperando = e.ajustes.esperando_cambios;
  if (esperando && (texto || m.voice || m.audio)) {
    const voz = m.voice?.file_id || m.audio?.file_id || null;
    e.cambios.push({ id: ++e.seq.cambio, revision_id: esperando, texto: texto || null, voz_file_id: voz, atendido: 0, creado: ahora() });
    e.ajustes.esperando_cambios = null; await guardar(env, e);
    return decir(env, `📝 Anotado para la revisión nº ${esperando}${voz ? " (audio recibido)" : ""}. Lo aplicaré en la próxima pasada (como mucho, 1 hora) y te mandaré la versión nueva.\n\nSi quieres añadir algo más, vuelve a pulsar ✏️ Pedir cambios.`);
  }
  return decir(env, "No he entendido el mensaje. Usa /ayuda para ver lo que puedo hacer.\nSi quieres pedir cambios, pulsa primero ✏️ en el vídeo correspondiente.");
}

async function botonPulsado(q, env) {
  const [accion, idTxt] = (q.data || "").split(":");
  const id = Number(idTxt);
  const e = await leer(env);
  const rev = e.revisiones.find(r => r.id === id);
  await tg(env, "answerCallbackQuery", { callback_query_id: q.id });
  if (!rev) return decir(env, "No encuentro esa revisión.");
  if (["programado", "publicado"].includes(rev.estado)) return decir(env, `La revisión nº ${id} ya está ${ESTADOS[rev.estado].toLowerCase()}.`);
  const poner = async (est, extra = {}) => { rev.estado = est; rev.actualizado = ahora(); Object.assign(e.ajustes, extra); await guardar(env, e); };

  if (accion === "aprobar") {
    await poner("aprobado");
    return decir(env, `✅ <b>${esc(rev.titulo)}</b> aprobado. En la próxima pasada lo programo en YouTube y te confirmo el día y la hora.`);
  }
  if (accion === "cambios") {
    await poner("cambios", { esperando_cambios: id });
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
  const results = (await leer(env)).revisiones.filter(r => ["pendiente", "cambios", "aprobado", "programado"].includes(r.estado));
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
    const e = await leer(env);
    let rev = d.id ? e.revisiones.find(r => r.id === d.id) : null;
    const etiquetas = (d.etiquetas || []).join(", ");
    if (rev) Object.assign(rev, { titulo: d.titulo, descripcion: d.descripcion, etiquetas, version: rev.version + 1, estado: "pendiente", enlace: d.enlace || null, actualizado: ahora() });
    else { rev = { id: ++e.seq.rev, tipo: d.tipo, titulo: d.titulo, descripcion: d.descripcion, etiquetas, version: 1, estado: "pendiente",
                   enlace: d.enlace || null, publicar_en: null, youtube_id: null, creado: ahora(), actualizado: ahora() }; e.revisiones.push(rev); }
    await guardar(env, e);
    const id = rev.id;
    const cabecera = `${rev.tipo === "short" ? "📱 SHORT" : "🎬 PELÍCULA"} · revisión nº ${id} · versión ${rev.version}`;
    const video = form.get("video");
    if (video && typeof video !== "string") {
      const f = new FormData();
      f.append("chat_id", env.OWNER); f.append("caption", `${cabecera}\n${rev.titulo}`.slice(0, 1000));
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
    const e = await leer(env);
    const aprobados = e.revisiones.filter(r => r.estado === "aprobado");
    const cambios = e.cambios.filter(c => !c.atendido).map(c => { const r = e.revisiones.find(x => x.id === c.revision_id) || {};
      return { ...c, titulo: r.titulo, tipo: r.tipo, version: r.version }; });
    const ideas = e.ideas.filter(i => !i.usada);
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
    const e = await leer(env);
    for (const c of e.cambios) if ((d.cambios_atendidos || []).includes(c.id)) c.atendido = 1;
    for (const i of e.ideas) if ((d.ideas_usadas || []).includes(i.id)) i.usada = 1;
    const rev = d.id ? e.revisiones.find(r => r.id === d.id) : null;
    if (rev) { for (const k of ["estado", "publicar_en", "youtube_id"]) if (d[k]) rev[k] = d[k]; rev.actualizado = ahora(); }
    await guardar(env, e);
    if (d.mensaje) await decir(env, d.mensaje);
    return json({ ok: true });
  }

  // Mensaje libre al dueño
  if (ruta === "mensaje" && req.method === "POST") { const d = await req.json(); return json(await decir(env, d.texto)); }

  // Token de acceso de YouTube (lo genera el bot con los secretos; Claude nunca ve el refresh token)
  if (ruta === "youtube-token") {
    const yt = (await env.KV.get("youtube", "json")) || {};
    const cid = env.YT_CLIENT_ID || yt.client_id, csec = env.YT_CLIENT_SECRET || yt.client_secret, rt = env.YT_REFRESH_TOKEN || yt.refresh_token;
    if (!rt) return json({ error: "YouTube todavía no está configurado" }, 409);
    const r = await fetch("https://oauth2.googleapis.com/token", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ client_id: cid, client_secret: csec, refresh_token: rt, grant_type: "refresh_token" }) });
    const t = await r.json();
    return json({ access_token: t.access_token, expires_in: t.expires_in, error: t.error });
  }

  return json({ error: "ruta desconocida" }, 404);
}

// ---------------------------------------------------------------- conexión con YouTube (OAuth)
// Claude deja en KV una clave de un solo uso ("config_token"). El usuario abre /configurar?t=<clave>, pega el
// ID y el secreto de cliente de Google, autoriza su canal y el bot guarda la autorización en KV. Nada pasa por el chat.
const ALCANCES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly";
const pagina = (cuerpo) => new Response(`<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Neido Studio · Conectar YouTube</title><style>body{font-family:system-ui,sans-serif;background:#07080B;color:#EFEAE0;max-width:560px;margin:0 auto;padding:24px 16px;line-height:1.5}
h1{font-size:22px}label{display:block;margin:18px 0 6px}input{width:100%;box-sizing:border-box;padding:12px;border-radius:8px;border:1px solid #444;background:#15171c;color:#fff;font-size:16px}
button{margin-top:24px;width:100%;padding:14px;border:0;border-radius:8px;background:#C9A46A;color:#07080B;font-size:17px;font-weight:600}.ok{color:#7ddc9b}.mal{color:#ff8a80}small{color:#aaa}</style></head><body>${cuerpo}</body></html>`,
  { headers: { "Content-Type": "text/html; charset=utf-8" } });

async function configurarYouTube(url, req, env) {
  const t = url.searchParams.get("t"); const valido = t && t === (await env.KV.get("config_token"));
  if (!valido) return pagina(`<h1 class="mal">Enlace caducado o no válido</h1><p>Pídele a Claude un enlace nuevo.</p>`);
  const redirect = `${url.protocol}//${url.host}/oauth/callback`;
  if (req.method === "POST") {
    const f = await req.formData();
    const cid = String(f.get("client_id") || "").trim(), csec = String(f.get("client_secret") || "").trim();
    if (!cid.endsWith(".apps.googleusercontent.com") || !csec) return pagina(`<h1 class="mal">Faltan datos</h1><p>El ID de cliente termina en <b>.apps.googleusercontent.com</b>. Vuelve atrás y revísalo.</p>`);
    await env.KV.put("youtube", JSON.stringify({ client_id: cid, client_secret: csec }));
    const auth = new URL("https://accounts.google.com/o/oauth2/v2/auth");
    auth.search = new URLSearchParams({ client_id: cid, redirect_uri: redirect, response_type: "code", scope: ALCANCES,
      access_type: "offline", prompt: "consent", include_granted_scopes: "true", state: t }).toString();
    return Response.redirect(auth.toString(), 302);
  }
  return pagina(`<h1>🎬 Conectar Neido Studio con YouTube</h1>
<p>Pega aquí los dos datos que te dio Google Cloud (pantalla "Cliente de OAuth creado").</p>
<form method="post"><label>ID de cliente</label><input name="client_id" placeholder="123...-abc.apps.googleusercontent.com" required autocomplete="off">
<label>Secreto del cliente</label><input name="client_secret" placeholder="GOCSPX-..." required autocomplete="off">
<button type="submit">Conectar con YouTube →</button></form>
<p><small>Después Google te pedirá elegir la cuenta: elige la del canal <b>Neido Studio</b>. Si sale "Google no ha verificado esta aplicación", pulsa <b>Avanzado</b> → <b>Ir a … (no seguro)</b>: la aplicación es tuya.</small></p>`);
}

async function callbackYouTube(url, env) {
  const t = url.searchParams.get("state");
  if (!t || t !== (await env.KV.get("config_token"))) return pagina(`<h1 class="mal">Enlace caducado</h1><p>Pídele a Claude un enlace nuevo.</p>`);
  if (url.searchParams.get("error")) return pagina(`<h1 class="mal">No se ha autorizado</h1><p>Google dice: ${esc(url.searchParams.get("error"))}. Puedes volver a intentarlo con el mismo enlace.</p>`);
  const yt = (await env.KV.get("youtube", "json")) || {};
  const r = await (await fetch("https://oauth2.googleapis.com/token", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ code: url.searchParams.get("code"), client_id: yt.client_id, client_secret: yt.client_secret,
      redirect_uri: `${url.protocol}//${url.host}/oauth/callback`, grant_type: "authorization_code" }) })).json();
  if (!r.refresh_token) return pagina(`<h1 class="mal">Google no ha devuelto la autorización</h1><p>${esc(r.error_description || r.error || "Sin detalle")}</p>`);
  // canal autorizado
  const c = await (await fetch("https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true", { headers: { Authorization: `Bearer ${r.access_token}` } })).json();
  const canal = c.items?.[0]?.snippet?.title || "(sin canal)";
  await env.KV.put("youtube", JSON.stringify({ ...yt, refresh_token: r.refresh_token, canal, canal_id: c.items?.[0]?.id || null, conectado: new Date().toISOString() }));
  await env.KV.delete("config_token");
  if (env.OWNER || (await leer(env)).ajustes.dueno) { env.OWNER = env.OWNER || (await leer(env)).ajustes.dueno; await decir(env, `📺 YouTube conectado al canal <b>${esc(canal)}</b>.`); }
  return pagina(`<h1 class="ok">✅ YouTube conectado</h1><p>Canal autorizado: <b>${esc(canal)}</b></p><p>Ya puedes cerrar esta página y volver con Claude.</p>`);
}

function json(o, status = 200) {
  return new Response(JSON.stringify(o), { status, headers: { "Content-Type": "application/json; charset=utf-8" } });
}
