// Renderiza la cortinilla fotograma a fotograma y la convierte en vídeo con ffmpeg.
// Uso: node renderizar.js  (desde esta carpeta). Salida: cortinilla.mp4 (1920x1080, 24 fps, 4 s)
const {chromium}=require('playwright');
const {execSync}=require('child_process');
const fs=require('fs'),path=require('path');
const FPS=24, DURACION=4;
(async()=>{
  const dir=__dirname, frames=path.join(dir,'frames');
  fs.rmSync(frames,{recursive:true,force:true}); fs.mkdirSync(frames);
  const b=await chromium.launch();
  const p=await b.newPage({viewport:{width:1920,height:1080}});
  await p.goto('file://'+path.join(dir,'cortinilla.html'));
  await p.evaluate(()=>document.fonts.ready); await p.waitForTimeout(500);
  const n=FPS*DURACION;
  for(let i=0;i<n;i++){
    await p.evaluate(t=>pintar(t), i/FPS);
    await p.screenshot({path:path.join(frames,String(i).padStart(4,'0')+'.png')});
  }
  await b.close();
  execSync(`ffmpeg -y -loglevel error -framerate ${FPS} -i "${frames}/%04d.png" -c:v libx264 -pix_fmt yuv420p -crf 16 "${path.join(dir,'cortinilla.mp4')}"`);
  fs.rmSync(frames,{recursive:true,force:true});
  console.log('cortinilla.mp4 lista');
})();
