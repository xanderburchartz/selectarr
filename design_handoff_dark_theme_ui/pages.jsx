// Page views for the Selectarr dark prototype.
// Pulls components from window (loaded in components.jsx).
// Exports each Page component back to window so app.jsx can route to them.

const { useState, useMemo } = React;

const FILTER_OPTIONS = [
  { value: 'all',          label: 'All' },
  { value: 'watched_all',  label: 'Watched by all users' },
  { value: 'watched_any',  label: 'Watched by any user' },
  { value: 'watched_user', label: 'Watched by selected user' },
  { value: 'unwatched',    label: 'Not watched by anyone' },
];

/* ═══ Filter bar ════════════════════════════════════════════════════ */
function FilterBar({ users, filter, userId, onFilter, onUser, count, label, right }) {
  return (
    <div className="filter-bar">
      <Select
        label="Filter"
        value={filter}
        onChange={onFilter}
        options={FILTER_OPTIONS}
      />
      <Select
        label="User"
        value={userId}
        onChange={onUser}
        options={[{ value: '', label: '— all users —' }, ...users.map(u => ({ value: u.id, label: u.name }))]}
      />
      <div className="filter-bar-spacer" />
      {count != null && (
        <div className="filter-bar-count">
          <span className="mono">{count}</span>
          <span className="muted"> {label}</span>
        </div>
      )}
      {right}
    </div>
  );
}

/* ═══ Page header ═══════════════════════════════════════════════════ */
function PageHeader({ title, subtitle, eyebrow, action }) {
  return (
    <header className="page-header">
      <div>
        {eyebrow && <div className="page-eyebrow">{eyebrow}</div>}
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {action && <div className="page-action">{action}</div>}
    </header>
  );
}

/* ═══ Movies ═══════════════════════════════════════════════════════════ */
function MoviesPage({ data, dryRun, onConfirm }) {
  const [filter, setFilter] = useState('all');
  const [userId, setUserId] = useState('');
  const [selected, setSelected] = useState(new Set());

  const visible = useMemo(() => {
    return data.movies.filter(m => {
      if (filter === 'unwatched') {
        if (!m.watch_status) return true;
        return !Object.values(m.watch_status.per_user).some(v => v);
      }
      if (filter === 'watched_all' && m.watch_status) {
        return Object.values(m.watch_status.per_user).every(v => v);
      }
      if (filter === 'watched_any' && m.watch_status) {
        return Object.values(m.watch_status.per_user).some(v => v);
      }
      if (filter === 'watched_user' && userId && m.watch_status) {
        return !!m.watch_status.per_user[userId];
      }
      return true;
    });
  }, [filter, userId, data.movies]);

  const selectableIds = visible.filter(m => m.has_file).map(m => m.radarr_id);
  const allChecked = selectableIds.length > 0 && selectableIds.every(id => selected.has(id));
  const someChecked = selectableIds.some(id => selected.has(id));

  const toggle = id => {
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelected(next);
  };
  const toggleAll = () => {
    if (allChecked) setSelected(new Set());
    else setSelected(new Set(selectableIds));
  };

  const selectedMovies = data.movies.filter(m => selected.has(m.radarr_id));
  const totalSize = selectedMovies.reduce((a, m) => a + (m.file_size_bytes || 0), 0);

  return (
    <div>
      <PageHeader
        eyebrow={<span className="service-tag"><span className="service-dot radarr" /> Radarr</span>}
        title="Movies"
        subtitle="Browse and selectively delete movies. Files are removed via Radarr and added to the import exclusion list."
      />

      <FilterBar
        users={data.users}
        filter={filter} userId={userId}
        onFilter={setFilter} onUser={setUserId}
        count={visible.length} label="movies"
      />

      <div className="table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th className="col-cb">
                <Checkbox
                  checked={allChecked}
                  indeterminate={!allChecked && someChecked}
                  onChange={toggleAll}
                />
              </th>
              <th>Title</th>
              <th className="col-year">Year</th>
              <th className="col-size">Size</th>
              <th className="col-watched">Watched</th>
            </tr>
          </thead>
          <tbody>
            {visible.map(m => (
              <tr key={m.radarr_id} className={selected.has(m.radarr_id) ? 'row-selected' : ''}>
                <td className="col-cb">
                  {m.has_file ? (
                    <Checkbox checked={selected.has(m.radarr_id)} onChange={() => toggle(m.radarr_id)} />
                  ) : (
                    <span className="muted-dim">—</span>
                  )}
                </td>
                <td>
                  <span className="title-cell">{m.title}</span>
                  {!m.has_file && <Pill tone="muted">no file</Pill>}
                </td>
                <td className="col-year mono">{m.year}</td>
                <td className="col-size mono muted">{fmt.size(m.file_size_bytes)}</td>
                <td className="col-watched">
                  <WatchDots status={m.watch_status} users={data.users} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="action-row">
        <div className="action-info">
          {selected.size > 0 ? (
            <>
              <strong className="mono">{selected.size}</strong>
              <span className="muted"> selected · </span>
              <span className="mono">{fmt.size(totalSize)}</span>
              <span className="muted"> to free</span>
            </>
          ) : (
            <span className="muted">Select movies to delete.</span>
          )}
        </div>
        <Button
          variant="danger"
          disabled={selected.size === 0}
          icon={<Icon.Trash />}
          onClick={() => onConfirm({
            kind: 'movies',
            dryRun,
            items: selectedMovies.map(m => ({ title: `${m.title} (${m.year})`, size: m.file_size_bytes, id: m.radarr_id })),
          })}>
          {dryRun ? 'Preview deletion' : 'Delete selected'}
        </Button>
      </div>
    </div>
  );
}

/* ═══ Series ══════════════════════════════════════════════════════════ */
function SeriesPage({ data, dryRun, onConfirm }) {
  const [filter, setFilter] = useState('all');
  const [userId, setUserId] = useState('');
  const [expanded, setExpanded] = useState(new Set([201]));
  const [seasonExpanded, setSeasonExpanded] = useState(new Set(['201-2']));
  const [episodeSel, setEpisodeSel] = useState(new Set([9101, 9102]));

  const toggle = (set, setSet, key) => {
    const next = new Set(set);
    next.has(key) ? next.delete(key) : next.add(key);
    setSet(next);
  };

  return (
    <div>
      <PageHeader
        eyebrow={<span className="service-tag"><span className="service-dot sonarr" /> Sonarr</span>}
        title="Series"
        subtitle="Delete at series, season, or individual episode level."
      />

      <FilterBar
        users={data.users}
        filter={filter} userId={userId}
        onFilter={setFilter} onUser={setUserId}
        count={data.series.length} label="series"
      />

      <div className="table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th className="col-expand"></th>
              <th>Title</th>
              <th className="col-year">Year</th>
              <th className="col-num">Seasons</th>
              <th className="col-size">Size</th>
              <th className="col-watched">Watched</th>
              <th className="col-actions"></th>
            </tr>
          </thead>
          <tbody>
            {data.series.map(s => {
              const open = expanded.has(s.sonarr_id);
              return (
                <React.Fragment key={s.sonarr_id}>
                  <tr className={open ? 'row-expanded' : ''}>
                    <td className="col-expand">
                      <button className="row-toggle" onClick={() => toggle(expanded, setExpanded, s.sonarr_id)} aria-label="Expand">
                        <Icon.Chevron open={open} />
                      </button>
                    </td>
                    <td><span className="title-cell">{s.title}</span></td>
                    <td className="col-year mono">{s.year}</td>
                    <td className="col-num mono">{s.seasons.length}</td>
                    <td className="col-size mono muted">{fmt.size(s.total_size_bytes)}</td>
                    <td className="col-watched"><WatchDots status={s.watch_status} users={data.users} /></td>
                    <td className="col-actions">
                      <Button variant="ghost-danger" size="sm" icon={<Icon.Trash />}
                        onClick={() => onConfirm({
                          kind: 'series', dryRun,
                          items: [{ title: `${s.title} · entire series`, size: s.total_size_bytes }],
                        })}>
                        Delete series
                      </Button>
                    </td>
                  </tr>
                  {open && (
                    <tr className="row-nested">
                      <td colSpan={7}>
                        <div className="nested-wrap">
                          <table className="data-table data-table-sub">
                            <thead>
                              <tr>
                                <th className="col-expand"></th>
                                <th>Season</th>
                                <th className="col-num">Episodes</th>
                                <th className="col-actions"></th>
                              </tr>
                            </thead>
                            <tbody>
                              {s.seasons.map(season => {
                                const sk = `${s.sonarr_id}-${season.number}`;
                                const sopen = seasonExpanded.has(sk);
                                return (
                                  <React.Fragment key={sk}>
                                    <tr className={sopen ? 'row-expanded' : ''}>
                                      <td className="col-expand">
                                        {season.episodes.length > 0 && (
                                          <button className="row-toggle" onClick={() => toggle(seasonExpanded, setSeasonExpanded, sk)}>
                                            <Icon.Chevron open={sopen} />
                                          </button>
                                        )}
                                      </td>
                                      <td><span className="title-cell">Season {season.number}</span></td>
                                      <td className="col-num mono">
                                        <span>{season.episode_file_count}</span>
                                        <span className="muted">/{season.episode_count}</span>
                                      </td>
                                      <td className="col-actions">
                                        <Button variant="ghost-danger" size="sm" icon={<Icon.Trash />}
                                          onClick={() => onConfirm({
                                            kind: 'season', dryRun,
                                            items: [{ title: `${s.title} · Season ${season.number}`, size: 5.8e9 }],
                                          })}>
                                          Delete season
                                        </Button>
                                      </td>
                                    </tr>
                                    {sopen && season.episodes.length > 0 && (
                                      <tr className="row-nested">
                                        <td colSpan={4}>
                                          <div className="nested-wrap nested-wrap-inner">
                                            <table className="data-table data-table-sub">
                                              <thead>
                                                <tr>
                                                  <th className="col-cb"></th>
                                                  <th className="col-num">Ep.</th>
                                                  <th>Title</th>
                                                  <th className="col-status">File</th>
                                                </tr>
                                              </thead>
                                              <tbody>
                                                {season.episodes.map(ep => (
                                                  <tr key={ep.episode_number} className={episodeSel.has(ep.episode_file_id) ? 'row-selected' : ''}>
                                                    <td className="col-cb">
                                                      {ep.episode_file_id ? (
                                                        <Checkbox
                                                          checked={episodeSel.has(ep.episode_file_id)}
                                                          onChange={() => toggle(episodeSel, setEpisodeSel, ep.episode_file_id)}
                                                        />
                                                      ) : <span className="muted-dim">—</span>}
                                                    </td>
                                                    <td className="col-num mono">{String(ep.episode_number).padStart(2, '0')}</td>
                                                    <td className="title-cell">{ep.title}</td>
                                                    <td className="col-status">
                                                      {ep.has_file
                                                        ? <span className="file-ok"><Icon.Check /></span>
                                                        : <span className="muted-dim">—</span>}
                                                    </td>
                                                  </tr>
                                                ))}
                                              </tbody>
                                            </table>
                                            <div className="nested-action">
                                              <Button variant="danger" size="sm" icon={<Icon.Trash />}
                                                disabled={episodeSel.size === 0}
                                                onClick={() => onConfirm({
                                                  kind: 'episodes', dryRun,
                                                  items: [...episodeSel].map(id => ({ title: `Episode file #${id}`, size: 1.1e9 })),
                                                })}>
                                                Delete {episodeSel.size} episode{episodeSel.size === 1 ? '' : 's'}
                                              </Button>
                                            </div>
                                          </div>
                                        </td>
                                      </tr>
                                    )}
                                  </React.Fragment>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ═══ Music ══════════════════════════════════════════════════════════ */
function MusicPage({ data, dryRun, onConfirm }) {
  const [filter, setFilter] = useState('all');
  const [userId, setUserId] = useState('');
  const [expanded, setExpanded] = useState(new Set([301]));

  const toggle = id => {
    const next = new Set(expanded);
    next.has(id) ? next.delete(id) : next.add(id);
    setExpanded(next);
  };

  return (
    <div>
      <PageHeader
        eyebrow={<span className="service-tag"><span className="service-dot lidarr" /> Lidarr</span>}
        title="Music"
        subtitle="Delete artists, albums, or individual tracks."
      />

      <FilterBar
        users={data.users}
        filter={filter} userId={userId}
        onFilter={setFilter} onUser={setUserId}
        count={data.artists.length} label="artists"
      />

      <div className="table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th className="col-expand"></th>
              <th>Artist</th>
              <th className="col-num">Albums</th>
              <th className="col-status">MusicBrainz</th>
              <th className="col-actions"></th>
            </tr>
          </thead>
          <tbody>
            {data.artists.map(a => {
              const open = expanded.has(a.lidarr_id);
              return (
                <React.Fragment key={a.lidarr_id}>
                  <tr className={open ? 'row-expanded' : ''}>
                    <td className="col-expand">
                      <button className="row-toggle" onClick={() => toggle(a.lidarr_id)}>
                        <Icon.Chevron open={open} />
                      </button>
                    </td>
                    <td><span className="title-cell">{a.name}</span></td>
                    <td className="col-num mono">{a.album_count}</td>
                    <td className="col-status">
                      {a.mb_id ? <Pill tone="info" dot>linked</Pill> : <Pill tone="muted">none</Pill>}
                    </td>
                    <td className="col-actions">
                      <Button variant="ghost-danger" size="sm" icon={<Icon.Trash />}
                        onClick={() => onConfirm({
                          kind: 'artist', dryRun,
                          items: [{ title: `${a.name} · all albums`, size: 1.2e9 }],
                        })}>
                        Delete artist
                      </Button>
                    </td>
                  </tr>
                  {open && a.albums.length > 0 && (
                    <tr className="row-nested">
                      <td colSpan={5}>
                        <div className="nested-wrap">
                          <table className="data-table data-table-sub">
                            <thead>
                              <tr>
                                <th>Album</th>
                                <th className="col-year">Year</th>
                                <th className="col-num">Tracks</th>
                                <th className="col-status">Files</th>
                                <th className="col-actions"></th>
                              </tr>
                            </thead>
                            <tbody>
                              {a.albums.map(al => (
                                <tr key={al.lidarr_id}>
                                  <td><span className="title-cell">{al.title}</span></td>
                                  <td className="col-year mono">{al.year || '—'}</td>
                                  <td className="col-num mono">{al.track_count}</td>
                                  <td className="col-status">
                                    {al.has_files
                                      ? <span className="file-ok"><Icon.Check /></span>
                                      : <span className="muted-dim">—</span>}
                                  </td>
                                  <td className="col-actions">
                                    <Button variant="ghost-danger" size="sm" icon={<Icon.Trash />}
                                      onClick={() => onConfirm({
                                        kind: 'album', dryRun,
                                        items: [{ title: `${a.name} — ${al.title}`, size: 1.2e8 }],
                                      })}>
                                      Delete album
                                    </Button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ═══ Logs ═══════════════════════════════════════════════════════════ */
function LogsPage({ data }) {
  const [entries, setEntries] = useState(data.logs);
  const [filter, setFilter] = useState('all');

  const visible = entries.filter(e => {
    if (filter === 'all') return true;
    if (filter === 'errors') return !e.success;
    if (filter === 'live') return !e.dry_run;
    if (filter === 'dry') return e.dry_run;
    return true;
  });

  return (
    <div>
      <PageHeader
        eyebrow={<span className="muted small mono">/var/log/selectarr</span>}
        title="Activity"
        subtitle="Every deletion is logged here with timestamp, scope, mode, and result."
        action={
          <div className="row gap-sm">
            <Select
              value={filter}
              onChange={setFilter}
              options={[
                { value: 'all',    label: 'All entries' },
                { value: 'errors', label: 'Errors only' },
                { value: 'live',   label: 'Live runs' },
                { value: 'dry',    label: 'Dry-runs' },
              ]}
            />
            <Button variant="secondary" icon={<Icon.Trash />} onClick={() => setEntries([])}>
              Clear log
            </Button>
          </div>
        }
      />

      <div className="logs-summary">
        <div className="stat">
          <div className="stat-label">Entries</div>
          <div className="stat-value mono">{entries.length}</div>
        </div>
        <div className="stat">
          <div className="stat-label">Succeeded</div>
          <div className="stat-value mono success">{entries.filter(e => e.success).length}</div>
        </div>
        <div className="stat">
          <div className="stat-label">Failed</div>
          <div className="stat-value mono danger">{entries.filter(e => !e.success).length}</div>
        </div>
        <div className="stat">
          <div className="stat-label">Dry-runs</div>
          <div className="stat-value mono warning">{entries.filter(e => e.dry_run).length}</div>
        </div>
      </div>

      <div className="table-card">
        <table className="data-table data-table-logs">
          <thead>
            <tr>
              <th className="col-ts">Timestamp</th>
              <th className="col-type">Type</th>
              <th>Title</th>
              <th className="col-mode">Mode</th>
              <th className="col-result">Result</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((e, i) => (
              <tr key={i}>
                <td className="col-ts mono muted">{fmt.ts(e.timestamp)}</td>
                <td className="col-type"><Pill tone={typePillTone(e.media_type)}>{e.media_type}</Pill></td>
                <td>
                  <span className="title-cell">{e.title}</span>
                  <div className="muted small">{e.message}</div>
                </td>
                <td className="col-mode">
                  {e.dry_run
                    ? <Pill tone="warning" dot>dry-run</Pill>
                    : <Pill tone="info" dot>live</Pill>}
                </td>
                <td className="col-result">
                  {e.success
                    ? <span className="result-success"><Icon.Check /> OK</span>
                    : <span className="result-error"><Icon.X /> error</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {visible.length === 0 && (
          <div className="empty-state">No log entries match the current filter.</div>
        )}
      </div>
    </div>
  );
}

function typePillTone(t) {
  return { movie: 'primary', series: 'primary', season: 'primary', episode: 'primary', album: 'accent', track: 'accent', artist: 'accent' }[t] || 'muted';
}

/* ═══ Settings ═══════════════════════════════════════════════════════ */
function SettingsPage({ dryRun, addExclusion, onDryRun, onExclusion }) {
  const services = [
    { id: 'jellyfin', name: 'Jellyfin', kind: 'required',  desc: 'Watch-status source',                placeholder: 'http://jellyfin:8096', defaultStatus: 'connected' },
    { id: 'radarr',   name: 'Radarr',   kind: 'optional',  desc: 'Movies',                              placeholder: 'http://radarr:7878',   defaultStatus: 'connected' },
    { id: 'sonarr',   name: 'Sonarr',   kind: 'optional',  desc: 'Series, seasons, episodes',           placeholder: 'http://sonarr:8989',   defaultStatus: 'connected' },
    { id: 'lidarr',   name: 'Lidarr',   kind: 'optional',  desc: 'Artists, albums, tracks',             placeholder: 'http://lidarr:8686',   defaultStatus: 'untested' },
  ];

  return (
    <div>
      <PageHeader
        eyebrow={<span className="muted small mono">~/config/config.yaml</span>}
        title="Settings"
        subtitle="Saved to config.yaml on disk. Jellyfin is required; the *arr services are optional — leave both fields empty to disable a tab."
      />

      <div className="settings-grid">
        {services.map(s => <ServiceCard key={s.id} {...s} />)}
      </div>

      <section className="card">
        <header className="card-header">
          <h2>Behaviour</h2>
          <p className="muted">How Selectarr handles deletions across services.</p>
        </header>
        <div className="card-body card-body-stack">
          <Toggle
            checked={dryRun} onChange={onDryRun}
            label="Dry-run mode"
            hint="Simulate every deletion without touching any files. Recommended while you tune filters."
          />
          <Toggle
            checked={addExclusion} onChange={onExclusion}
            label="Add to import exclusion list"
            hint="Prevent deleted items from being re-downloaded by Radarr / Sonarr / Lidarr."
          />
        </div>
      </section>
    </div>
  );
}

function ServiceCard({ id, name, kind, desc, placeholder, defaultStatus }) {
  const [url, setUrl] = useState(placeholder);
  const [key, setKey] = useState(id === 'lidarr' ? '' : '••••••••••••••••••••');
  const [status, setStatus] = useState(defaultStatus);
  const [testing, setTesting] = useState(false);

  const test = () => {
    setTesting(true);
    setStatus('testing');
    setTimeout(() => {
      setTesting(false);
      setStatus(key && url ? 'connected' : 'failed');
    }, 700);
  };

  const statusEl = {
    connected: <Pill tone="success" dot>connected</Pill>,
    failed:    <Pill tone="danger" dot>failed</Pill>,
    testing:   <Pill tone="info" dot>testing…</Pill>,
    untested:  <Pill tone="muted">not tested</Pill>,
  }[status];

  return (
    <section className={`card service-card service-${id}`}>
      <header className="card-header">
        <div className="service-head">
          <span className={`service-dot ${id}`} />
          <h2>{name}</h2>
          <span className={`kind-tag kind-${kind}`}>{kind}</span>
        </div>
        <p className="muted">{desc}</p>
      </header>
      <div className="card-body card-body-stack">
        <TextInput label="URL" value={url} onChange={setUrl} placeholder={placeholder} mono />
        <TextInput label="API key" value={key} onChange={setKey} type="password" placeholder="Paste API key" mono required={kind === 'required'} />
        <div className="row gap-sm align-center">
          <Button variant="secondary" size="sm" icon={<Icon.Plug />} onClick={test} disabled={testing}>
            Test connection
          </Button>
          {statusEl}
        </div>
      </div>
    </section>
  );
}

/* ═══ Confirm drawer (right side panel) ══════════════════════════════ */
function ConfirmDrawer({ payload, dryRun, onClose, onDelete }) {
  const [phase, setPhase] = useState('confirm'); // confirm | working | result

  if (!payload) return null;

  const total = payload.items.reduce((a, i) => a + (i.size || 0), 0);

  const run = () => {
    setPhase('working');
    setTimeout(() => setPhase('result'), 900);
  };

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={e => e.stopPropagation()}>
        <header className="drawer-header">
          <div>
            <div className="drawer-eyebrow">{dryRun ? 'Dry-run preview' : 'Confirm deletion'}</div>
            <h2>{phase === 'result' ? (dryRun ? 'Dry-run complete' : 'Deletion complete') : 'Review before delete'}</h2>
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close"><Icon.X /></button>
        </header>

        <div className="drawer-body">
          {phase === 'confirm' && (
            <>
              {dryRun ? (
                <Banner tone="warning" title="Dry-run mode is on.">
                  No files will be touched. This panel will show what <em>would</em> happen.
                </Banner>
              ) : (
                <Banner tone="error" title="This will permanently delete files.">
                  Files are removed from disk by the source *arr service. This cannot be undone.
                </Banner>
              )}
              <div className="drawer-stat-row">
                <div className="stat">
                  <div className="stat-label">Scope</div>
                  <div className="stat-value">{payload.kind}</div>
                </div>
                <div className="stat">
                  <div className="stat-label">Items</div>
                  <div className="stat-value mono">{payload.items.length}</div>
                </div>
                <div className="stat">
                  <div className="stat-label">{dryRun ? 'Would free' : 'Will free'}</div>
                  <div className="stat-value mono">{fmt.size(total)}</div>
                </div>
              </div>
              <h3 className="drawer-section-title">Items</h3>
              <ul className="drawer-list">
                {payload.items.map((i, k) => (
                  <li key={k}>
                    <span className="title-cell">{i.title}</span>
                    <span className="mono muted">{fmt.size(i.size)}</span>
                  </li>
                ))}
              </ul>
            </>
          )}

          {phase === 'working' && (
            <div className="drawer-working">
              <div className="spinner" />
              <p>{dryRun ? 'Simulating deletion…' : 'Deleting files…'}</p>
            </div>
          )}

          {phase === 'result' && (
            <>
              {dryRun ? (
                <Banner tone="info" title="Dry-run complete.">
                  {payload.items.length} item(s) would be deleted · {fmt.size(total)} would be freed.
                </Banner>
              ) : (
                <Banner tone="success" title="Deletion complete.">
                  {payload.items.length} item(s) deleted · {fmt.size(total)} freed.
                </Banner>
              )}
              <h3 className="drawer-section-title">Result</h3>
              <ul className="drawer-list">
                {payload.items.map((i, k) => (
                  <li key={k}>
                    <span className="title-cell">{i.title}</span>
                    <span className="result-success small"><Icon.Check /> {dryRun ? 'would delete' : 'deleted'}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>

        <footer className="drawer-footer">
          {phase === 'confirm' ? (
            <>
              <Button variant="secondary" onClick={onClose}>Cancel</Button>
              <Button variant="danger" icon={<Icon.Trash />} onClick={run}>
                {dryRun ? 'Run simulation' : 'Delete now'}
              </Button>
            </>
          ) : (
            <Button variant="primary" onClick={onClose}>Close</Button>
          )}
        </footer>
      </aside>
    </div>
  );
}

Object.assign(window, { MoviesPage, SeriesPage, MusicPage, LogsPage, SettingsPage, ConfirmDrawer });
