ToraDove v0.4.9 - PWA IDENTITY FIX

Correzioni PWA:
- manifest dedicato: toradove.webmanifest
- ID PWA esplicito e unico: ./toradove-pwa
- start_url dedicato: ./index.html?app=toradove-pwa
- scope esplicito: ./
- registrazione SW con scope esplicito e updateViaCache:none
- cambio controller: un solo reload per passare da eventuale SW padre a ToraDove
- cache namespace esclusivo toradove-*
- il service worker NON cancella più cache di ToraNavy o altre app sullo stesso dominio

IMPORTANTE:
ToraDove e ToraNavy devono avere URL/cartelle GitHub Pages distinti.
Esempio:
  .../ToraNavy/
  .../ToraDove/
Non devono condividere la stessa identica cartella/root se vuoi installarle entrambe come app indipendenti.

File da caricare:
- index.html
- toradove.webmanifest
- sw.js
- icon-192.png
- icon-512.png
- tora_crest.png
- powered_by_az.png
