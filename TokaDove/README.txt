TOKA DOVE v0.3.3

Fix ORS 2007 / "This response format is not supported":
- rimosso Accept: application/json dalla richiesta /driving-hgv/geojson;
- mantenuti Authorization e Content-Type application/json;
- routing HGV invariato;
- nessun fallback automatico a OSRM;
- cache PWA aggiornata.

File principale: index.html
