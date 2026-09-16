ToraDove v0.4.7 — TRUCK TIME + STOPS

TEMPO CAMION
- ORS driving-hgv resta autorità geometrica e legale.
- ORS richiesto con instructions=true.
- Timeline costruita dalle duration reali degli step ORS (way_points), non più tempo uniforme per km.
- Se nello stesso origin è presente la chiave TomTom di ToraNavy (ktn57_tomtom_api_key), viene richiesta una route truck no-traffic con peso/assi/dimensioni reali.
- Il tempo TomTom viene usato solo se distanza e corridoio sono coerenti con ORS HGV; gli step ORS vengono scalati al totale canonico.
- Se TomTom non è disponibile, resta ORS HGV ma con timeline step-by-step corretta.

RICERCA SOSTE
- eliminata query Overpass a 28 scansioni around;
- una sola bbox stretta sulla finestra utile della route;
- tre endpoint in parallelo, timeout 15 s;
- cache 5 minuti;
- se Overpass fallisce, punto teorico e mappa restano comunque visibili e validi.

File principale: index.html
