// Shared UI components for the Selectarr dark-theme prototype.
// Loaded after React; exports to window so pages.jsx can use them.

const { useState, useEffect, useRef } = React;

/* ─── Brand logo (Bin & Check mark — Variant 1) ─────────────────────── */
function BrandMark({ size = 22 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 200 200" aria-hidden="true">
      <circle cx="100" cy="100" r="92" fill="var(--primary)" />
      <rect x="84" y="56" width="32" height="8" rx="3" fill="#ffffff" />
      <rect x="52" y="68" width="96" height="14" rx="4" fill="#ffffff" />
      <path d="M60 90 L140 90 L132 152 Q132 156 128 156 L72 156 Q68 156 68 152 Z" fill="#ffffff" />
      <path d="M76 119 L92 137 L124 105"
            fill="none" stroke="#F04C5C" strokeWidth="11"
            strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ─── Watch dots — one per user ─────────────────────────────────────── */
function WatchDots({ status, users }) {
  if (!status) {
    return (
      <span className="watch-dots" title="Not in Jellyfin">
        <span className="dot dot-unknown" />
      </span>
    );
  }
  return (
    <span className="watch-dots">
      {users.map(u => {
        const w = status.per_user?.[u.id];
        const cls = w === true ? 'dot-watched' : w === false ? 'dot-unwatched' : 'dot-unknown';
        const label = w === true ? `${u.name} · watched` : w === false ? `${u.name} · unwatched` : `${u.name} · unknown`;
        return <span key={u.id} className={`dot ${cls}`} title={label} />;
      })}
    </span>
  );
}

/* ─── Pill / badge ──────────────────────────────────────────────────── */
function Pill({ tone = 'neutral', children, dot }) {
  return (
    <span className={`pill pill-${tone}`}>
      {dot && <span className="pill-dot" />}
      {children}
    </span>
  );
}

/* ─── Banner (error / warning / info / success) ─────────────────────── */
function Banner({ tone, title, children, action }) {
  const icons = { error: '!', warning: '!', info: 'i', success: '✓' };
  return (
    <div className={`banner banner-${tone}`}>
      <span className="banner-icon" aria-hidden="true">{icons[tone] || 'i'}</span>
      <div className="banner-body">
        {title && <strong>{title}</strong>}
        <span>{children}</span>
      </div>
      {action && <div className="banner-action">{action}</div>}
    </div>
  );
}

/* ─── Button ────────────────────────────────────────────────────────── */
function Button({ variant = 'secondary', size = 'md', children, icon, ...props }) {
  return (
    <button className={`btn btn-${variant} btn-${size}`} {...props}>
      {icon && <span className="btn-icon">{icon}</span>}
      {children}
    </button>
  );
}

/* ─── Select (styled) ───────────────────────────────────────────────── */
function Select({ label, value, onChange, options, hint }) {
  return (
    <label className="field">
      {label && <span className="field-label">{label}</span>}
      <span className="select-wrap">
        <select value={value} onChange={e => onChange(e.target.value)}>
          {options.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <span className="select-caret">▾</span>
      </span>
      {hint && <span className="field-hint">{hint}</span>}
    </label>
  );
}

/* ─── Text / password input ─────────────────────────────────────────── */
function TextInput({ label, value, onChange, type = 'text', placeholder, required, hint, mono }) {
  return (
    <label className="field">
      {label && (
        <span className="field-label">
          {label}
          {required && <span className="field-required">required</span>}
        </span>
      )}
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className={mono ? 'input mono' : 'input'}
      />
      {hint && <span className="field-hint">{hint}</span>}
    </label>
  );
}

/* ─── Checkbox ──────────────────────────────────────────────────────── */
function Checkbox({ checked, indeterminate, onChange, label, disabled }) {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current) ref.current.indeterminate = !!indeterminate;
  }, [indeterminate]);
  return (
    <label className={`cb ${disabled ? 'cb-disabled' : ''}`}>
      <input
        ref={ref}
        type="checkbox"
        checked={!!checked}
        disabled={disabled}
        onChange={e => onChange?.(e.target.checked)}
      />
      <span className="cb-box" aria-hidden="true">
        <svg viewBox="0 0 12 12" className="cb-check">
          <path d="M2.5 6.2 L4.8 8.5 L9.5 3.5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <svg viewBox="0 0 12 12" className="cb-dash">
          <path d="M3 6 H9" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
        </svg>
      </span>
      {label && <span className="cb-label">{label}</span>}
    </label>
  );
}

/* ─── Toggle switch ─────────────────────────────────────────────────── */
function Toggle({ checked, onChange, label, hint }) {
  return (
    <label className="toggle">
      <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} />
      <span className="toggle-track"><span className="toggle-thumb" /></span>
      <span className="toggle-text">
        <span className="toggle-label">{label}</span>
        {hint && <span className="toggle-hint">{hint}</span>}
      </span>
    </label>
  );
}

/* ─── Icon set (inline SVG, currentColor) ───────────────────────────── */
const Icon = {
  Film:    () => <svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.4"><rect x="2" y="2.5" width="12" height="11" rx="1.5"/><path d="M5 2.5v11M11 2.5v11M2 6h12M2 10h12"/></svg>,
  Tv:      () => <svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.4"><rect x="2" y="3.5" width="12" height="9" rx="1.5"/><path d="M5.5 1.5 8 3.5 10.5 1.5"/></svg>,
  Music:   () => <svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M6 12V4l7-1.5V11"/><circle cx="4.5" cy="12" r="1.6"/><circle cx="11.5" cy="11" r="1.6"/></svg>,
  Log:     () => <svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M3 3h7l3 3v7H3z"/><path d="M10 3v3h3M5.5 8.5h5M5.5 11h4"/></svg>,
  Cog:     () => <svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.4"><circle cx="8" cy="8" r="2.2"/><path d="M8 1.5v2M8 12.5v2M1.5 8h2M12.5 8h2M3.4 3.4l1.4 1.4M11.2 11.2l1.4 1.4M3.4 12.6l1.4-1.4M11.2 4.8l1.4-1.4"/></svg>,
  Chevron: ({ open }) => <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.6" style={{ transform: open ? 'rotate(90deg)' : 'none', transition: 'transform .15s' }}><path d="M6 4l4 4-4 4"/></svg>,
  Trash:   () => <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M3 4.5h10M6.5 4.5V3a1 1 0 0 1 1-1h1a1 1 0 0 1 1 1v1.5M4.5 4.5l.7 8a1.5 1.5 0 0 0 1.5 1.4h2.6a1.5 1.5 0 0 0 1.5-1.4l.7-8"/><path d="M7 7v4M9 7v4"/></svg>,
  Search:  () => <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.4"><circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5 13.5 13.5"/></svg>,
  Check:   () => <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M3.5 8.5 L7 12 L13 5"/></svg>,
  X:       () => <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M4 4l8 8M12 4l-8 8"/></svg>,
  Eye:     () => <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M1.5 8s2.3-4.5 6.5-4.5S14.5 8 14.5 8 12.2 12.5 8 12.5 1.5 8 1.5 8z"/><circle cx="8" cy="8" r="1.8"/></svg>,
  Plug:    () => <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M5.5 1.5v3M10.5 1.5v3M4 4.5h8v3a4 4 0 0 1-8 0v-3zM8 11.5v3"/></svg>,
};

/* ─── Format helpers ────────────────────────────────────────────────── */
const fmt = {
  size(bytes) {
    if (!bytes) return '—';
    const gb = bytes / 1073741824;
    if (gb >= 1) return `${gb.toFixed(1)} GB`;
    const mb = bytes / 1048576;
    return `${mb.toFixed(0)} MB`;
  },
  ts(iso) {
    return iso.slice(0, 19).replace('T', ' ');
  },
};

Object.assign(window, { BrandMark, WatchDots, Pill, Banner, Button, Select, TextInput, Checkbox, Toggle, Icon, fmt });
