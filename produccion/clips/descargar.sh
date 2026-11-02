#!/bin/bash
# Uso: descargar.sh ID [ID...]  → descarga el vídeo de Pexels en HD (1920x1080 si existe)
for id in "$@"; do
  [ -f "$id.mp4" ] && { echo "ya $id"; continue; }
  ok=""
  for res in hd_1920_1080 hd_2048_1080 uhd_2560_1440 hd_1280_720; do
    for fps in 25 24 30 50 60; do
      u="https://videos.pexels.com/video-files/$id/$id-${res}_${fps}fps.mp4"
      if [ "$(curl -sS -o /dev/null -I -w '%{http_code}' -A 'Mozilla/5.0' "$u")" = 200 ]; then
        curl -sS -A 'Mozilla/5.0' -o "$id.mp4" "$u" && ok="$res $fps"; break 2
      fi
    done
  done
  if [ -n "$ok" ]; then
    info=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height:format=duration -of csv=p=0 "$id.mp4" | tr '\n' ' ')
    echo "OK $id $ok -> $info"
  else
    echo "NO $id"
  fi
done
