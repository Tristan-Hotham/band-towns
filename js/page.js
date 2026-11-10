/* Does anyone play your town? UK local authorities on a plain MapLibre base map (OpenFreeMap Positron), sized by the
 * concerts documented in MusicBrainz and coloured by documented / expected (from population, nation and arenas),
 * with a decade slider, documented venues, arenas and a search. Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const fmt = n => Number(n).toLocaleString('en-GB');
  const COL = ['#1F4F7A', '#6F9CC4', '#D8D1C3', '#E3A08A', '#B4442E'];
  let map = null, S = null, venues = null, dec = 7, mode = 'all', playing = null;
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  function cls(k, e) {
    const r = Math.log2((k + 0.5) / (e + 0.5));
    return r <= -2 ? 0 : r <= -1 ? 1 : r < 1 ? 2 : r < 2 ? 3 : 4;
  }
  const phrase = c => ['4x or more fewer than its size predicts', '2x to 4x fewer than its size predicts', 'about what its size predicts', '2x to 4x more than its size predicts', '4x or more than its size predicts'][c];
  const decLabel = i => i === 7 ? '1960 to 2025' : `${S.decades[i]}s`;
  function counts(a) {
    if (mode === 'tour') { const tot = S.totT, share = a.e / S.totE; return [a.t, share * tot]; }
    if (dec === 7) return [a.k, a.e];
    return [a.d[dec], a.de[dec]];
  }
  function fc() {
    return { type: 'FeatureCollection', features: S.las.map((a, i) => { const [k, e] = counts(a); return { type: 'Feature', id: i, geometry: { type: 'Point', coordinates: [a.lon, a.lat] }, properties: { i, k, c: cls(k, e), n: a.n } }; }) };
  }
  function popLA(a) {
    const [k, e] = counts(a), c = cls(k, e);
    const what = mode === 'tour' ? 'tour dates' : 'documented concerts';
    const per = dec === 7 || mode === 'tour' ? '1960 to 2025' : `the ${S.decades[dec]}s`;
    const mx = Math.max(1, ...a.d);
    const spark = '<div class="spark" aria-hidden="true">' + a.d.map(v => `<span class="${v ? '' : 'x'}" style="height:${Math.max(2, 46 * v / mx)}px" title="${v}"></span>`).join('') + '</div><div class="sparkl">' + S.decades.map(d => `<span>${String(d).slice(2)}s</span>`).join('') + '</div>';
    let h = `<b class="t">${esc(a.n)}</b><div>${esc(a.nat)} · ${fmt(a.pop)} people (census)</div>` +
      `<table><tr><td>${what}, ${per}</td><td><b>${fmt(k)}</b></td></tr><tr><td>expected from its size</td><td>${e.toFixed(e < 10 ? 1 : 0)}</td></tr>` +
      (mode === 'all' && dec !== 7 ? `<tr><td>all years, 1960 to 2025</td><td>${fmt(a.k)}</td></tr>` : '') +
      `<tr><td>tour dates (all years)</td><td>${fmt(a.t)}</td></tr><tr><td>documented venues</td><td>${fmt(a.v)}</td></tr>` +
      `<tr><td>nearest 10,000+ arena</td><td>${a.ar ? 'in this area' : esc(a.na) + ', ' + a.akm + ' km'}</td></tr></table>` +
      `<div>That is <b>${phrase(c)}</b>.</div>` + spark;
    if (a.tv.length) h += `<p class="nt">Most documented venues: ${a.tv.map(v => `${esc(v[0])} (${v[1]})`).join(', ')}.</p>`;
    if (a.tp.length) h += `<p class="nt">Most documented acts: ${a.tp.map(v => `${esc(v[0])} (${v[1]})`).join(', ')}.</p>`;
    h += `<p class="nt">Concerts someone has entered in MusicBrainz, placed by venue. Expected = from population, nation and distance to an arena (Poisson model). Census 2021 or 2022 population.</p>`;
    h += `<div class="lk"><a href="https://musicbrainz.org/search?query=${encodeURIComponent(a.n)}&type=area">Search MusicBrainz</a></div>`;
    new maplibregl.Popup({ maxWidth: '320px', focusAfterOpen: false }).setLngLat([a.lon, a.lat]).setHTML(h).addTo(map);
  }
  function popVenue(p, ll) {
    const h = `<b class="t">${esc(p.name)}</b><div>${esc(p.type || 'Place')} · ${esc(p.la)}</div>` +
      `<div><b>${fmt(p.n)}</b> documented concert${p.n === 1 ? '' : 's'}, ${p.y0 === p.y1 ? p.y0 : p.y0 + ' to ' + p.y1}</div>` +
      `<div class="lk"><a href="https://musicbrainz.org/place/${esc(p.mbid)}/events">Its events on MusicBrainz</a></div>`;
    new maplibregl.Popup({ maxWidth: '300px', focusAfterOpen: false }).setLngLat(ll).setHTML(h).addTo(map);
  }
  function refresh() {
    if (map && map.getSource('la')) map.getSource('la').setData(fc());
    if (map && map.getLayer('ven')) map.setFilter('ven', mode === 'all' && dec !== 7 ? ['all', ['<=', ['get', 'y0'], S.decades[dec] + 9], ['>=', ['get', 'y1'], S.decades[dec]]] : null);
    document.querySelectorAll('.chip[data-m]').forEach(x => x.setAttribute('aria-pressed', x.dataset.m === mode));
    const d = document.getElementById('dec'); d.value = dec; d.disabled = mode === 'tour';
    document.getElementById('decTxt').textContent = mode === 'tour' ? 'All years' : decLabel(dec);
    const tot = mode === 'tour' ? S.totT : (dec === 7 ? S.totE0 : S.totals[dec]);
    const n = S.las.filter(a => counts(a)[0] > 0).length;
    document.getElementById('decPc').textContent = `${fmt(tot)} ${mode === 'tour' ? 'tour dates' : 'gigs'} · ${n} of 361 areas`;
  }
  document.querySelectorAll('.chip[data-m]').forEach(b => b.addEventListener('click', () => { mode = b.dataset.m; refresh(); }));
  document.getElementById('dec').addEventListener('input', e => { dec = +e.target.value; refresh(); });
  document.getElementById('play').addEventListener('click', e => {
    if (playing) { clearInterval(playing); playing = null; e.target.textContent = '▶'; return; }
    mode = 'all'; dec = 0; refresh(); e.target.textContent = '❚❚';
    playing = setInterval(() => { dec += 1; if (dec > 7) { clearInterval(playing); playing = null; e.target.textContent = '▶'; dec = 7; } refresh(); }, 1300);
  });
  const lp = document.getElementById('lp'), lb = document.getElementById('lyrBtn');
  lb.addEventListener('click', () => { const o = !lp.classList.contains('open'); lp.classList.toggle('open', o); lb.setAttribute('aria-expanded', o); });
  function vis(ids, on) { ids.forEach(id => { if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', on ? 'visible' : 'none'); }); }

  // search: council areas and venues
  const q = document.getElementById('q'), sug = document.getElementById('sug');
  let hits = [], cur = -1;
  function show() { sug.innerHTML = hits.map((h, i) => `<li role="option" data-i="${i}" aria-selected="${i === cur}">${esc(h.label)} <span>${esc(h.sub)}</span></li>`).join(''); sug.style.display = hits.length ? 'block' : 'none'; }
  function pick(h) {
    sug.style.display = 'none'; q.value = h.label;
    map.flyTo({ center: h.ll, zoom: Math.max(map.getZoom(), h.v ? 12 : 8.5) });
    map.once('moveend', () => h.v ? popVenue(h.v, h.ll) : popLA(h.a));
  }
  q.addEventListener('input', () => {
    const t = norm(q.value.trim()); cur = -1;
    if (t.length < 2 || !S) { hits = []; show(); return; }
    const a = [], b = [];
    S.las.forEach(x => { const n = norm(x.n); const h = { label: x.n, sub: 'council area', ll: [x.lon, x.lat], a: x }; if (n.startsWith(t)) a.push(h); else if (n.includes(t)) b.push(h); });
    (venues || []).forEach(f => { const n = norm(f.properties.name); const h = { label: f.properties.name, sub: 'venue, ' + f.properties.la, ll: f.geometry.coordinates, v: f.properties }; if (n.startsWith(t)) a.push(h); else if (n.includes(t)) b.push(h); });
    hits = a.concat(b).slice(0, 12); show();
  });
  q.addEventListener('keydown', e => {
    if (e.key === 'ArrowDown') { cur = Math.min(cur + 1, hits.length - 1); show(); e.preventDefault(); }
    else if (e.key === 'ArrowUp') { cur = Math.max(cur - 1, 0); show(); e.preventDefault(); }
    else if (e.key === 'Enter' && hits.length) { pick(hits[Math.max(cur, 0)]); }
    else if (e.key === 'Escape') { sug.style.display = 'none'; }
  });
  sug.addEventListener('click', e => { const li = e.target.closest('li'); if (li) pick(hits[+li.dataset.i]); });
  document.addEventListener('click', e => { if (!e.target.closest('.srch')) sug.style.display = 'none'; });
  document.querySelectorAll('[data-la]').forEach(el => el.addEventListener('click', e => {
    e.preventDefault(); const a = S && S.las.find(x => x.n === el.dataset.la); if (!a) return;
    document.getElementById('mapWrap').scrollIntoView({ behavior: 'smooth' });
    map.flyTo({ center: [a.lon, a.lat], zoom: 8.5 }); map.once('moveend', () => popLA(a));
  }));

  Promise.all([fetch('data/site.json').then(r => r.json()), fetch('data/la_outlines.geojson').then(r => r.json())]).then(([site, outl]) => {
    S = site; S.totE = S.las.reduce((s, a) => s + a.e, 0); S.totT = S.las.reduce((s, a) => s + a.t, 0); S.totE0 = S.las.reduce((s, a) => s + a.k, 0);
    refresh();
    if (!window.maplibregl) { document.getElementById('nojs').textContent = 'The map could not load (MapLibre GL JS missing).'; return; }
    map = new maplibregl.Map({ container: 'map', style: STYLE, bounds: [[-8.3, 49.9], [1.9, 59.0]], fitBoundsOptions: { padding: small ? 10 : 40 }, maxZoom: 15, minZoom: 3.5, attributionControl: false });
    window.__map = map;
    map.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution: 'Data: <a href="https://musicbrainz.org/">MusicBrainz</a> (CC0) · Boundaries ONS/OSNI (OGL) · Base map <a href="https://openfreemap.org/">OpenFreeMap</a> © OpenStreetMap' }), 'bottom-right');
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    map.on('load', () => {
      document.getElementById('nojs').remove();
      document.querySelectorAll('.maplibregl-ctrl-attrib').forEach(el => el.classList.remove('maplibregl-compact-show'));
      const labels = map.getStyle().layers.filter(l => l.type === 'symbol').map(l => l.id);
      map.addSource('outl', { type: 'geojson', data: outl });
      map.addLayer({ id: 'outl', type: 'line', source: 'outl', paint: { 'line-color': '#8C7A5B', 'line-width': ['interpolate', ['linear'], ['zoom'], 4, 0.3, 9, 1.1], 'line-opacity': 0.55 } }, labels[0]);
      map.addSource('la', { type: 'geojson', data: fc() });
      const R = ['interpolate', ['linear'], ['zoom'], 4, ['+', 3, ['*', 0.9, ['sqrt', ['get', 'k']]]], 9, ['+', 5, ['*', 2.2, ['sqrt', ['get', 'k']]]]];
      map.addLayer({ id: 'la-c', type: 'circle', source: 'la', paint: {
        'circle-radius': R,
        'circle-color': ['case', ['==', ['get', 'k'], 0], '#FFFFFF', ['match', ['get', 'c'], 0, COL[0], 1, COL[1], 2, COL[2], 3, COL[3], COL[4]]],
        'circle-stroke-color': ['case', ['==', ['get', 'k'], 0], ['match', ['get', 'c'], 0, COL[0], 1, COL[1], '#9C8656'], '#2B2119'],
        'circle-stroke-width': ['case', ['==', ['get', 'k'], 0], 1.6, 0.8], 'circle-opacity': 0.88 } });
      map.addLayer({ id: 'la-t', type: 'symbol', source: 'la', filter: ['>=', ['get', 'k'], 60], layout: { 'text-field': ['get', 'n'], 'text-font': ['Noto Sans Regular'], 'text-size': 11, 'text-offset': [0, 1.4], 'text-anchor': 'top', 'text-optional': true }, paint: { 'text-color': '#2B2119', 'text-halo-color': '#FFFFFF', 'text-halo-width': 1.4 }, minzoom: 6 });
      fetch('data/venues.geojson').then(r => r.json()).then(v => {
        venues = v.features;
        map.addSource('ven', { type: 'geojson', data: v });
        map.addLayer({ id: 'ven', type: 'circle', source: 'ven', layout: { visibility: 'none' }, paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 2.5, 12, ['+', 4, ['sqrt', ['get', 'n']]]], 'circle-color': '#7A3E8E', 'circle-stroke-color': '#FFFFFF', 'circle-stroke-width': 1 } });
        map.on('click', 'ven', e => popVenue(e.features[0].properties, e.lngLat));
        map.on('mouseenter', 'ven', () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', 'ven', () => map.getCanvas().style.cursor = '');
        document.getElementById('lyV').addEventListener('change', e => vis(['ven'], e.target.checked));
        refresh();
      });
      map.addSource('arn', { type: 'geojson', data: { type: 'FeatureCollection', features: S.arenas.map(a => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [a.lon, a.lat] }, properties: a })) } });
      map.addLayer({ id: 'arn', type: 'circle', source: 'arn', paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 3.5, 10, 7], 'circle-color': '#2B2119', 'circle-stroke-color': '#FFFFFF', 'circle-stroke-width': 1.5 } });
      map.on('click', 'arn', e => { const a = e.features[0].properties; new maplibregl.Popup({ maxWidth: '280px', focusAfterOpen: false }).setLngLat(e.lngLat).setHTML(`<b class="t">${esc(a.arena)}</b><div>${esc(a.city)} · ${fmt(a.capacity)} seats · opened ${a.opened}</div><p class="nt">Indoor arena of 10,000+ seats, from Wikipedia's list of indoor arenas in the United Kingdom.</p>`).addTo(map); });
      map.on('click', 'la-c', e => { if (map.queryRenderedFeatures(e.point, { layers: ['arn'].concat(map.getLayer('ven') && map.getLayoutProperty('ven', 'visibility') === 'visible' ? ['ven'] : []) }).length) return; popLA(S.las[e.features[0].properties.i]); });
      ['la-c', 'arn'].forEach(l => { map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });
      document.getElementById('lyA').addEventListener('change', e => vis(['la-c', 'la-t'], e.target.checked));
      document.getElementById('lyR').addEventListener('change', e => vis(['arn'], e.target.checked));
      document.getElementById('lyO').addEventListener('change', e => vis(['outl'], e.target.checked));
      document.getElementById('lyL').addEventListener('change', e => vis(labels, e.target.checked));
    });
  }).catch(err => { const n = document.getElementById('nojs'); if (n) n.textContent = 'The map data could not load.'; console.error(err); });
})();
