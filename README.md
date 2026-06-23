# Radar de fondos · Mediolanum

Mini-web personal que muestra los mejores fondos del catálogo Mediolanum por
**desempeño** (1 mes / 3 meses / YTD / 1 año / 3 años) y por **tipo de activo**
(Renta Variable, Renta Fija, Multiactivo, Mediolanum), con ranking de posición.

**Se actualiza sola cada día. No tienes que rellenar nada.**

---

## Novedades de esta versión

- **Todo el catálogo MiFID** (209 fondos): Best Brands, Mediolanum International, la gama **Challenge** completa, Gamax y todas las gestoras de My World (PIMCO, BlackRock, Carmignac, Robeco, M&G, Fidelity, Pictet, Nordea, DNCA, DWS, Invesco, JPMorgan, Schroders, Morgan Stanley, Vontobel, Muzinich, Amundi, Candriam, Goldman Sachs, Janus Henderson, GAM, Ostrum…).
- **Vista por sector / estilo** además de por tipo de activo: tecnología, salud, materias primas y oro, recursos/energía, industria, financiero, consumo y lujo, infraestructuras, inmobiliario, agua/medioambiente, economía circular, internacional, EE. UU., Europa, Asia/Pacífico, emergentes, dividendos y **value**.
- **Rentabilidad semanal, mensual y anual** (más 3 meses, YTD y 3 años): un selector arriba separa el ranking por periodo.
- **Podio por categoría**: en cada categoría/sector se destacan los 3 mejores (oro 🥇, plata 🥈, bronce 🥉) y debajo el resto del ranking.
- **Comparador con gráficos**: marca con el botón ＋ los fondos que quieras (hasta 6) y pulsa "Comparar gráficos" para ver dos gráficas: la **evolución base 100** del último año (curvas superpuestas) y la **rentabilidad por periodo** (barras Sem/Mes/YTD/Año). Las curvas se rellenan al desplegar el repo (el motor guarda una serie semanal por fondo).
- Ratios: **Sharpe, volatilidad, beta y alfa** (beta/alfa a 3A frente al índice de la clase de activo).
- Filtro **Solo Mediolanum (Core + Challenge)** para tu 60% obligatorio de la cartera Core.
- Cada estrategia aparece una sola vez (no se duplican clases ni versiones *hedged*); si quieres las cubiertas, se pueden añadir en `funds.json`.

## Cómo funciona (en una frase)

Un pequeño programa (`update_funds.py`) se ejecuta **solo, una vez al día, en la
nube gratis de GitHub**, descarga los desempeños de cada fondo, los ordena y deja
un fichero `data.json`. La web (`index.html`) lee ese fichero y pinta los rankings.

```
funds.json  ──►  update_funds.py  ──►  data.json  ──►  index.html (tu web)
(lista)          (motor diario)        (datos)          (lo que ves)
```

## Por qué no es "solo un HTML"

Ningún archivo HTML suelto puede bajar a diario el desempeño de fondos LU/FR:
no hay API pública y gratis que un navegador pueda leer, y un archivo no tiene
quién lo ejecute cada día. Por eso hace falta el motor + la automatización.
Aquí ya están hechos; solo tienes que publicarlos una vez.

---

## Puesta en marcha (5 minutos, gratis, una sola vez)

1. Crea una cuenta en **github.com** (si no tienes) y pulsa **New repository**.
   Nombre por ejemplo `radar-fondos`. Marca **Public**. Crea.
2. **Sube estos archivos** al repositorio (botón *Add file ▸ Upload files*,
   arrastra todo y *Commit*):
   - `index.html`
   - `update_funds.py`
   - `funds.json`
   - `data.json`  (semilla; se irá actualizando solo)
   - la carpeta `.github/workflows/update.yml`
   - este `README.md`
3. Activa la web: **Settings ▸ Pages ▸ Source: Deploy from a branch ▸
   branch `main` / carpeta `/ (root)` ▸ Save**. En 1-2 min tu web estará en
   `https://TU-USUARIO.github.io/radar-fondos/`.
4. Lanza la primera actualización a mano: pestaña **Actions ▸ "Actualizar radar
   de fondos" ▸ Run workflow**. Cuando termine (un par de minutos), recarga tu
   web: verás todos los fondos con datos.

A partir de ahí se actualiza **automáticamente cada día** (~07:30, hora
peninsular). No tienes que hacer nada más. Guárdate la URL en el móvil.

---

## Ajustes opcionales

- **Añadir o quitar fondos:** edita `funds.json` (nombre, gestora, tipo,
  categoría y, si lo tienes, el `isin` — mejora la precisión del emparejamiento).
- **Cambiar la hora:** edita el `cron` en `.github/workflows/update.yml`.
- **Si un fondo no encuentra datos:** suele ser por el emparejamiento de nombre.
  Añade su `isin` en `funds.json` y vuelve a lanzar el workflow.

## Avisos

- Los desempeños son orientativos (fuente: Yahoo Finance, uso personal).
  **Verifica siempre** en la ficha oficial (KIID/DFI) o Morningstar antes de
  usar un dato con un cliente, y confirma la clase/ISIN disponible en Mediolanum.
- Es una herramienta de soporte, **no asesoramiento** ni recomendación
  personalizada. La idoneidad depende de cada cliente (MiFID II). Rentabilidades
  pasadas no garantizan resultados futuros.
