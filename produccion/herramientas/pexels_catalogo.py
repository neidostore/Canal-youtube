import pandas as pd,sys,warnings; warnings.simplefilter("ignore")
d=pd.read_parquet('px.parquet'); d['id']=d['loc'].str.extract(r'-(\d+)/?$',expand=False); d['t']=d.title.str.split(' · ').str[0]
d['duration']=pd.to_numeric(d.duration,errors='coerce'); d['view_count']=pd.to_numeric(d.view_count,errors='coerce')
d=d[(d.duration>=5)&(d.duration<=40)]
Q={'rayo':r'lightning','colibri':r'hummingbird','eiffel':r'eiffel','pulpo':r'octopus','bambu':r'bamboo (forest|trees|grove|stalk)','emu':r'\bemu\b','trigo':r'wheat field','soldado':r'machine gun|soldier.*(aim|fir|shoot|rifle)','ojo':r'close.?up.*\beye\b|\beye\b.*close.?up|pupil|\biris\b','radiotel':r'radio telescope|satellite dish|observatory|antenna','estrellas':r'starry|milky way|night sky.*star','cafe':r'coffee (pot|maker|machine)|pouring coffee|filter coffee','ordenador':r'old computer|retro computer|vintage computer|webcam|crt','cohete':r'rocket (launch|engine)|spacex|thruster','cristal':r'exoplanet|blue planet|shattered glass|broken glass|glass shards','sol':r'solar flare|\bsun\b.*(surface|animation)','tormenta':r'thunderstorm|storm clouds'}
for k,q in Q.items():
  m=d[d.t.str.contains(q,case=False,regex=True)].sort_values('view_count',ascending=False)
  print('==',k,len(m))
  for _,r in m.head(9).iterrows(): print('  ',r.id,int(r.duration),r.t[:70])
