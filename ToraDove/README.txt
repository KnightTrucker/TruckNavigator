ToraDove v0.4.8

TEMPO CAMION
- ORS driving-hgv resta autorità geometrica/restrizioni.
- Se la chiave TomTom già salvata da ToraNavy è disponibile:
  TomTom Truck con traffic=true diventa baseline del tempo.
- Richiesti anche i tempi traffic/no-traffic TomTom per diagnosi.
- Timeline locale resta costruita dagli step ORS HGV e scalata al totale camion.
- "Tempo route" rinominato "Tempo camion".

RICERCA SOSTE
- TomTom Search Along Route è la fonte primaria.
- Cerca solo sulla porzione 20/30/40 km della route interessata.
- Query: area di servizio / parcheggio camion / area di sosta.
- Overpass è solo integrazione/fallback se TomTom trova meno di 4 candidati.
- Overpass prova POST e GET.
- Max 6 risultati, filtri route/falsi positivi invariati.

MAPPA
- punto teorico ridotto a piccolo rombo giallo;
- eliminato il grande banner "PUNTO TEORICO";
- marker soste e nomi restano visibili.

UI
- errore ricerca soste reso compatto, non più grande riquadro tratteggiato.
