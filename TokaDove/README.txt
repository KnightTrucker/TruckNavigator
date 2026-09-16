ToraDove v0.3.7

MAP REAL FIX:
- rimossi Esri + overlay CARTO a due griglie;
- satellite ibrido Google, stessa sorgente già usata in ToraNavy;
- ResizeObserver sul contenitore mappa;
- MutationObserver quando la card mappa diventa visibile;
- niente zoom/fade animation Leaflet su Android;
- route/marker/fitBounds applicati solo dopo la misura reale del contenitore;
- eliminati i setTimeout usati come toppa per ridimensionare la mappa;
- coordinate -> indirizzo e GPS -> indirizzo invariati;
- routing ORS HGV invariato.

File principale: index.html
