# Inkbird INT Cook Control

Le quattro sonde, cuore e ambiente, lo storico e un avviso che si senta senza
tenere il telefono in mano. La dashboard e' facoltativa: l'integrazione funziona
anche senza.

**Dashboard facoltativa, disponibile con la release v0.2.10.** Questa
versione e' verificata con **una station INT-14-BW**, due sensori per sonda.

## Installazione

Prima devono funzionare Inkbird INT e le otto entita' di temperatura.
Da HACS installa anche **button-card**, **card-mod** e **mini-graph-card**.

**[Scarica Cook Control](https://github.com/zampix1/ha-inkbird-int14/releases/download/v0.2.10/inkbird-int-cook-control.zip)**

Estrai prima lo ZIP. La directory di configurazione HA e' quella che contiene
`configuration.yaml`, normalmente `/config`. Unisci le due cartelle a quelle
esistenti: non copiare lo ZIP intero o una cartella contenitore aggiuntiva.
Alla fine la struttura deve essere questa:

```text
config/
  configuration.yaml
  packages/inkbird_bbq.yaml
  www/inkbird-int/cook-base-v1.4.3.js
  www/inkbird-int/inkbird-int-cook-model.mjs
  www/inkbird-int/inkbird-int-cook-control.js
```

La cartella `cook-control` nello ZIP contiene guide, licenze e YAML della
plancia: non serve copiarla in HA.

1. Fai un backup HA. Copia `packages` e `www` del pacchetto nella directory di
   configurazione. Se usi gia' il pacchetto BBQ di Remco, sostituiscilo:
   **non caricare due copie**. Gli helper mantengono gli stessi ID.
2. Se non usi gia' i package, aggiungi questa voce in `configuration.yaml`.
   Se esiste gia' `homeassistant:`, aggiungi solo la riga `packages:` sotto
   quella sezione, con due spazi davanti, senza duplicarla:

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

   Controlla la configurazione e riavvia HA.
3. In **Impostazioni > Plance > Risorse**, aggiungi il modulo JavaScript
   `/local/inkbird-int/inkbird-int-cook-control.js?v=1.0.4`.
   Se manca Risorse, abilita Modalita' avanzata nel profilo. Per aggiornare,
   modifica la risorsa esistente invece di aggiungerne un'altra. Ricarica il browser.
4. Aggiungi **Inkbird Cook Control** dalle dashboard della community. In
   alternativa crea una plancia vuota e incolla [dashboard.yaml](dashboard.yaml)
   nel suo editor di configurazione grezza:

   ```yaml
   strategy:
     type: custom:inkbird-int-cook-control
   views: []
   ```

5. Alla prima apertura premi **Use this thermometer** e scegli **Italiano**.
   Con una sola station il rilevamento e' automatico. Il prefisso si configura
   una volta sola; non tocchiamo i parametri del termometro.

Con un rilevamento ambiguo, vedi il [prefisso esplicito](README.md#install).
Il pacchetto gestisce una sola station. HACS installa l'integrazione, non questa
dashboard facoltativa.

## Cottura E Avvisi

Dai un nome alla sonda, tocca la card per impostare la **soglia HA** e abilita
gli avvisi solo sulle sonde usate. Per una nuova cottura disattivali e riattivali.
La soglia HA serve agli annunci; l'**allarme station** e' quello riportato dal
termometro. I preset non modificano l'allarme del dispositivo.

L'avviso parte dopo 30 secondi sopra soglia. La riconnessione non lo ripete.
**Ignora/Dismiss** ferma rinvio e promemoria. Cambiare nome, soglia o termometro
cancella i timer precedenti. Il promemoria decorre dalla soglia, non da quando
togli il cibo dal fuoco. Le temperature dei preset non garantiscono sicurezza
o cottura riuscita: continua a controllare il cibo.

Per Echo seleziona il dispositivo, **Alexa (native)** e attiva gli annunci.
Serve **Alexa Media Player**, non OpenAI. Per la TV configura entita' e servizio
notify, poi prova il pulsante. La LG mostra un popup breve **senza audio**:
non cambiamo volume, ingresso o stato di accensione.

Gli avvisi HA persistenti vengono creati per primi. Verifica di persona gli
altri canali: una chiamata accettata non certifica che tu l'abbia sentita.

## Limiti

- Oltre 120 secondi senza pacchetti locali, le letture non alimentano nuovi
  allarmi; il controllo temporale HA puo' aggiungere fino a un minuto.
- I timer non sopravvivono a riavvio HA o ricarica delle automazioni.
- Le batterie sono quelle dichiarate dalla station. Un valore sospetto viene
  segnalato, non sostituito con una percentuale inventata.
- Stallo e batteria bassa sono avvisi facoltativi, non sistemi di sicurezza.
- Prove reali e simulate sono distinte in [VALIDATION.md](VALIDATION.md).

La base grafica deriva dal lavoro MIT di Remco, con i crediti di design
conservati. Comunicazione e protocollo arrivano dalla nostra integrazione
`zampix1/ha-inkbird-int14`. Vedi [fonti e licenze](THIRD_PARTY_NOTICES.md).

Per tornare indietro ripristina package e dashboard dal backup, controlla la
configurazione e riavvia HA. Non serve rifare il pairing.
