// Main Selectarr prototype app — router + chrome + tweaks wiring.

const { useState } = React;

const NAV = [
  { id: 'movies',   label: 'Movies',   icon: Icon.Film },
  { id: 'series',   label: 'Series',   icon: Icon.Tv },
  { id: 'music',    label: 'Music',    icon: Icon.Music },
  { id: 'logs',     label: 'Activity', icon: Icon.Log },
  { id: 'settings', label: 'Settings', icon: Icon.Cog },
];

function TopNav({ page, onPage, dryRun, accent, density, onAccent, onDensity }) {
  return (
    <nav className="top-nav" data-screen-label={page}>
      <a className="brand" href="#" onClick={e => { e.preventDefault(); onPage('movies'); }}>
        <BrandMark size={22} />
        <span>Selectarr</span>
      </a>

      <div className="nav-tabs">
        {NAV.map(n => {
          const I = n.icon;
          return (
            <button
              key={n.id}
              className={`nav-tab ${page === n.id ? 'active' : ''}`}
              onClick={() => onPage(n.id)}>
              <I />
              <span>{n.label}</span>
            </button>
          );
        })}
      </div>

      <div className="nav-right">
        {dryRun && <Pill tone="warning" dot>DRY-RUN</Pill>}
        <span className="connection mono small">
          <span className="connection-dot ok" /> jellyfin · radarr · sonarr · lidarr
        </span>
      </div>
    </nav>
  );
}

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "#5865F2",
  "density": "cozy",
  "dryRun": true,
  "addExclusion": true,
  "page": "movies"
}/*EDITMODE-END*/;

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [page, setPage] = useState(t.page || 'movies');
  const [confirmPayload, setConfirmPayload] = useState(null);

  // Apply tweaks to CSS variables.
  React.useEffect(() => {
    const r = document.documentElement;
    r.style.setProperty('--primary', t.accent);
    // Derive primary-hover (slightly lighter) and primary-dim (12% alpha).
    r.style.setProperty('--primary-hover', shade(t.accent, 0.12));
    r.style.setProperty('--primary-dim', alpha(t.accent, 0.14));
    r.style.setProperty('--primary-soft', alpha(t.accent, 0.22));
    r.dataset.density = t.density;
  }, [t.accent, t.density]);

  const data = window.SELECTARR_DATA;

  return (
    <div className="app-shell">
      <TopNav
        page={page} onPage={setPage}
        dryRun={t.dryRun}
        accent={t.accent} density={t.density}
        onAccent={v => setTweak('accent', v)}
        onDensity={v => setTweak('density', v)}
      />

      <main className="page">
        {page === 'movies'   && <MoviesPage   data={data} dryRun={t.dryRun} onConfirm={setConfirmPayload} />}
        {page === 'series'   && <SeriesPage   data={data} dryRun={t.dryRun} onConfirm={setConfirmPayload} />}
        {page === 'music'    && <MusicPage    data={data} dryRun={t.dryRun} onConfirm={setConfirmPayload} />}
        {page === 'logs'     && <LogsPage     data={data} />}
        {page === 'settings' && <SettingsPage
          dryRun={t.dryRun} addExclusion={t.addExclusion}
          onDryRun={v => setTweak('dryRun', v)}
          onExclusion={v => setTweak('addExclusion', v)}
        />}
      </main>

      <ConfirmDrawer
        payload={confirmPayload}
        dryRun={t.dryRun}
        onClose={() => setConfirmPayload(null)}
      />

      <TweaksPanel title="Tweaks" defaultOpen={false}>
        <TweakSection label="Brand">
          <TweakColor
            label="Accent"
            value={t.accent}
            onChange={v => setTweak('accent', v)}
            options={['#5865F2', '#6BA0F6', '#9B7CF7', '#E4A33F']}
          />
        </TweakSection>
        <TweakSection label="Layout">
          <TweakRadio
            label="Density"
            value={t.density}
            onChange={v => setTweak('density', v)}
            options={[
              { value: 'cozy',    label: 'Cozy' },
              { value: 'compact', label: 'Compact' },
            ]}
          />
        </TweakSection>
        <TweakSection label="Behaviour">
          <TweakToggle label="Dry-run mode"        value={t.dryRun}       onChange={v => setTweak('dryRun', v)} />
          <TweakToggle label="Add import exclusion" value={t.addExclusion} onChange={v => setTweak('addExclusion', v)} />
        </TweakSection>
        <TweakSection label="Jump to page">
          <TweakSelect
            label="Page"
            value={page}
            onChange={p => { setPage(p); setTweak('page', p); }}
            options={NAV.map(n => ({ value: n.id, label: n.label }))}
          />
        </TweakSection>
      </TweaksPanel>
    </div>
  );
}

/* ─── Color helpers ─────────────────────────────────────────────────── */
function hexToRgb(h) {
  const m = h.replace('#', '');
  return [0, 2, 4].map(i => parseInt(m.slice(i, i + 2), 16));
}
function shade(hex, amount) {
  const [r, g, b] = hexToRgb(hex);
  const mix = c => Math.round(c + (255 - c) * amount);
  return `rgb(${mix(r)},${mix(g)},${mix(b)})`;
}
function alpha(hex, a) {
  const [r, g, b] = hexToRgb(hex);
  return `rgba(${r},${g},${b},${a})`;
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
