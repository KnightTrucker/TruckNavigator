ToraNavy ROOT PWA SCOPE FIX per convivenza con ToraDove

DA CARICARE NELLA ROOT DI htrucker.github.io:
- manifest.webmanifest
- sw.js

NON sostituire index.html di ToraNavy.

Cosa cambia:
1) manifest ToraNavy:
   id        = ./index.html
   start_url = ./index.html
   scope     = ./index.html

   In questo modo ToraNavy NON considera più /ToraDove/ parte della propria PWA.

2) service worker ToraNavy:
   - ignora completamente /ToraDove/
   - cancella solo vecchie cache ktn-*
   - NON cancella più cache toradove-* o cache di altre PWA.

Dopo il commit:
1. attendi il deploy GitHub Pages;
2. apri ToraNavy dal suo URL root /index.html con Internet e ricarica;
3. apri una volta la PWA ToraNavy già installata e poi chiudila;
4. chiudi completamente Chrome e riaprilo;
5. apri /ToraDove/ e prova Installa app.

Se Chrome conserva ancora il vecchio scope installato, NON cancellare dati del sito:
prima prova un secondo ciclo apertura/chiusura ToraNavy. Solo se resta bloccato
sarà necessario reinstallare ToraNavy dopo che questo fix è già online.
