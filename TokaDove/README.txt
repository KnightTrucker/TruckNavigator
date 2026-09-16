ToraDove v0.3.9 - STOPS VERIFIED

Correzioni:
- Overpass multi-server:
  1) overpass.private.coffee
  2) overpass-api.de
  3) maps.mail.ru
- su ogni server prova POST e poi GET;
- timeout controllato, niente più messaggio grezzo "Failed to fetch";
- rimossi i distributori HGV come categoria autonoma di sosta;
- accettate solo:
  * highway=services;
  * highway=rest_area;
  * amenity=parking con hgv=yes/designated e validazione pubblica;
  * parking=layby con hgv=yes/designated e validazione pubblica;
- esclusi access=private/no/customers/delivery/emergency/permit;
- esclusi piazzali aziendali ambigui;
- parcheggi hgv=yes senza altra evidenza pubblica esclusi;
- corridoio laterale ristretto da 10 km a 5 km;
- nei risultati viene mostrata la prova OSM usata per la validazione.

Mappa v0.3.8 e routing ORS HGV invariati.
File principale: index.html
