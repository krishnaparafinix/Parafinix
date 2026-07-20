// Design tokens — "Precision Instrument" dark theme (approved direction 1B).
// Source: Claude Design handoff, Parafinix AI brand identity.zip / README.md.
// Values are transcribed exactly from the .dc.html reference files — do not
// round or approximate; if a value needs to change, update here so every
// component that imports these stays in sync.

export const color = {
  bg: '#0f1113',
  bgAlt: '#0b0c0e',
  rail: '#131518',
  card: '#16181b',
  raised: '#1b1e22',
  border: '#26292d',
  borderSubtle: '#23262a',
  borderRaised: '#2d3136',

  teal: '#5fd0c4',
  teal2: '#3bb3a6',
  tealLight: '#7fe0d5',
  tealSoftBg: 'rgba(95,208,196,0.1)',
  tealSoftBorder: 'rgba(95,208,196,0.25)',

  amber: '#c7893f',
  amberLight: '#d89646',
  amberDark: '#b9781f',
  amberSoftBg: 'rgba(199,137,63,0.12)',
  amberSoftBorder: 'rgba(199,137,63,0.35)',

  textPrimary: '#f4f5f6',
  textSecondary: '#e7e9ea',
  textSecondary2: '#c3c8cd',
  textMuted: '#9298a0',
  textFaint: '#7c8288',
  textFainter: '#6a7076',
  textFaintest: '#5a6067',

  ink: '#0f1113',
}

export const pageBg =
  'radial-gradient(1200px 600px at 78% -8%, rgba(95,208,196,0.06), transparent 60%),' +
  'radial-gradient(900px 500px at 12% 108%, rgba(199,137,63,0.07), transparent 55%),' +
  '#0f1113'

export const font = {
  display: "'Space Grotesk', sans-serif",
  body: "'IBM Plex Sans', sans-serif",
  mono: "'IBM Plex Mono', monospace",
}

export const shadow = {
  cardHover: '0 26px 44px -22px rgba(0,0,0,0.75)',
  panel: '0 30px 60px -22px rgba(0,0,0,0.7)',
  sidebar: '34px 0 64px -26px rgba(0,0,0,.85)',
}

export const easing = {
  primary: 'cubic-bezier(.2,.8,.2,1)',
  tilt: 'cubic-bezier(.2,.7,.2,1)',
}

// Doc-type accent triads used across Client Profile / Reports (SR/CR/FF).
export const docAccent = {
  suitability: { code: 'SR', accent: color.amber, accent2: color.amberLight, soft: color.amberSoftBg, border: color.amberSoftBorder },
  compliance: { code: 'CR', accent: color.teal, accent2: color.teal2, soft: color.tealSoftBg, border: color.tealSoftBorder },
  factfind: { code: 'FF', accent: color.teal, accent2: color.teal2, soft: color.tealSoftBg, border: color.tealSoftBorder },
}
