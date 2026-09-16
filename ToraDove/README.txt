ToraDove v0.4.6 - SEMANTIC MAP

CORREZIONE MAPPA:
- route Leaflet rossa;
- il punto teorico e le soste NON dipendono più dai marker Leaflet;
- overlay DOM indipendente e ancorato al riquadro mappa;
- overlay aggiornato a ogni pan, zoom e resize;
- punto teorico: giallo + etichetta PUNTO TEORICO;
- soste prima del limite: azzurro + numero + nome;
- soste in tolleranza: arancio + numero + nome;
- i numeri corrispondono alla lista "Dove fermarti";
- "Mostra sulla mappa" centra e fa pulsare il marker;
- drawRoute(false) evita il vecchio fitBounds asincrono che poteva cambiare inquadratura.

ICONA:
- icona ToraDove fucsia approvata mantenuta in icon-192.png e icon-512.png.

File principale: index.html
