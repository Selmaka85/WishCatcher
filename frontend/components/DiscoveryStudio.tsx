'use client'

import { useState } from 'react'

type Cluster = {
  cluster_id: string
  domain: string
  frame: { problem?: string; desired_outcome?: string; intent?: string; interpretation_method?: string }
  genesis: Record<string, unknown>
  mentions: number
  unique_threads: number
  known_actors: number
  source_count: number
  status: string
  signal_score: number
  market_demand: string
  willingness_to_pay: string
  supporting_sources?: {
    source: string; url: string; grounding_status: string
    evidence: { message_id: string; excerpt: string }[]
  }[]
}
type DiscoveryReport = {
  id: string; sources: string[]; status: string; collected: number
  accepted: number; inserted: number; skipped: number; errors: string[]
  rejection_reasons?: Record<string, number>
  clusters: Cluster[]
}
type Run = {
  id: string; sources: string[]; status: string; collected: number
  accepted: number; inserted: number; skipped: number; errors: string[]
  created_at: number
}

const SOURCE_OPTIONS = [
  { id: 'hn_need_search', label: 'HN — Need Search', note: 'No login · targeted public comments · verified original author' },
  { id: 'hn_ask', label: 'Hacker News — Ask', note: 'Public official API · no login' },
  { id: 'hn_show', label: 'Hacker News — Show', note: 'Public official API · no login' },
  { id: 'hn_new', label: 'Hacker News — New', note: 'Public official API · no login' },
  { id: 'search_hn', label: 'Search → Hacker News', note: 'Brave Search API key required' },
  { id: 'public_rss', label: 'Approved RSS / Atom', note: 'HTTPS feed configured in .env' },
  { id: 'approved_jsonl', label: 'Approved JSONL import', note: 'Permission + file path in .env' },
]
const button = 'rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white hover:bg-violet-500 disabled:opacity-40'
const secondary = 'rounded-xl border border-slate-600 px-5 py-3 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-40'

export default function DiscoveryStudio({ accessToken }: { accessToken: string }) {
  const [sources, setSources] = useState<string[]>(['hn_need_search', 'hn_ask'])
  const [perSource, setPerSource] = useState(3)
  const [report, setReport] = useState<DiscoveryReport | null>(null)
  const [clusters, setClusters] = useState<Cluster[]>([])
  const [runs, setRuns] = useState<Run[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')

  async function call<T>(action: string, payload: unknown = {}): Promise<T> {
    if (!accessToken.trim()) {
      throw new Error('Introdu întâi cheia de acces în secțiunea Conectare la plugin.')
    }
    const resp = await fetch('/api/context', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json', 'X-WishCatcher-Admin': accessToken.trim(),
      },
      body: JSON.stringify({ action, payload }), cache: 'no-store',
    })
    const result = await resp.json()
    if (!resp.ok) {
      throw new Error(typeof result.detail === 'string' ? result.detail : 'Server error ' + resp.status)
    }
    return result as T
  }

  async function execute(action: 'discoveryRun' | 'discoveryClusters' | 'discoveryRuns') {
    setBusy(action); setError('')
    try {
      if (action === 'discoveryRun') {
        if (!sources.length) throw new Error('Selectează cel puțin o sursă.')
        const result = await call<DiscoveryReport>(action, {
          sources, max_per_source: perSource, max_contexts: 35,
        })
        setReport(result); setClusters(result.clusters)
      } else if (action === 'discoveryClusters') {
        const data = await call<{ clusters: Cluster[] }>(action)
        setClusters(data.clusters)
      } else {
        const data = await call<{ runs: Run[] }>(action)
        setRuns(data.runs)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Eroare necunoscută.')
    } finally {
      setBusy('')
    }
  }

  function toggle(source: string, checked: boolean) {
    setSources(previous => checked
      ? Array.from(new Set([...previous, source]))
      : previous.filter(s => s !== source))
  }

  return (
    <section className="space-y-5 rounded-2xl border border-slate-700 bg-slate-900/70 p-5 md:p-6">
      <div>
        <h2 className="text-lg font-semibold">Autonomous Discovery Engine</h2>
        <p className="mt-2 text-sm text-slate-400">
          Descoperă conversații publice, reconstruiește nevoile, grupează problemele similare și
          generează schițe Genesis cu proveniență. Totul cu limite explicite și fără autentificare pe forumuri.
        </p>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {SOURCE_OPTIONS.map(source => (
          <label key={source.id} className="flex items-start gap-3 rounded-xl border border-slate-700 bg-slate-950/50 p-3">
            <input className="mt-1" type="checkbox" checked={sources.includes(source.id)}
              onChange={e => toggle(source.id, e.target.checked)} />
            <span>
              <span className="block text-sm font-medium text-slate-100">{source.label}</span>
              <span className="block text-xs text-slate-400">{source.note}</span>
            </span>
          </label>
        ))}
      </div>
      <div className="flex flex-wrap items-end gap-3">
        <label className="block text-sm text-slate-300">
          Maximum conversații per sursă
          <input type="number" min="1" max="10"
            value={perSource} onChange={e => setPerSource(Math.max(1, Math.min(10, Number(e.target.value) || 1)))}
            className="mt-2 block w-28 rounded-lg border border-slate-600 bg-slate-950 p-2 text-white" />
        </label>
        <button className={button} disabled={!!busy || !sources.length}
          onClick={() => execute('discoveryRun')}>
          {busy === 'discoveryRun' ? 'Descopăr și analizez…' : 'Pornește descoperirea'}
        </button>
        <button className={secondary} disabled={!!busy}
          onClick={() => execute('discoveryClusters')}>Vezi oportunități</button>
        <button className={secondary} disabled={!!busy}
          onClick={() => execute('discoveryRuns')}>Istoric execuții</button>
      </div>
      {error && <p role="alert" className="rounded-xl border border-rose-700 bg-rose-950 p-3 text-sm text-rose-200">{error}</p>}
      {report && (
        <div className="flex flex-wrap gap-3 text-xs">
          {[
            ['Stare', report.status], ['Colectate', report.collected],
            ['Candidate', report.accepted], ['Salvate', report.inserted],
            ['Eliminate / duplicate', report.skipped],
          ].map(([k,v]) => <span key={k} className="rounded-lg bg-slate-800 px-3 py-2">{k}: {v}</span>)}
          {Object.entries(report.rejection_reasons || {}).map(([reason,count]) => (
            <span key={reason} className="rounded-lg border border-slate-600 px-3 py-2">
              {reason.replaceAll('_', ' ')}: {count}
            </span>
          ))}
          {report.errors.map((err,i) => <p key={i} className="w-full text-amber-300">⚠ {err}</p>)}
        </div>
      )}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-violet-300">Oportunități descoperite</h3>
        {!clusters.length && <p className="text-sm text-slate-400">
          Nicio oportunitate salvată încă. Începe cu Hacker News — Ask și verifică rezultatele.
        </p>}
        <div className="space-y-3">
          {clusters.map(item => (
            <div key={item.cluster_id} className="rounded-xl border border-slate-700 bg-slate-950/60 p-4">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <span className="rounded-md bg-violet-950 px-2 py-1 text-xs text-violet-200">{item.domain}</span>
                <span className="text-xs text-slate-400">{item.status.replaceAll('_', ' ')}</span>
                <span className="text-xs text-slate-400">{item.unique_threads} discuții · {item.known_actors} autori cunoscuți · {item.mentions} semnale</span>
              </div>
              <h4 className="text-sm font-semibold text-white">{item.frame.intent || item.frame.problem}</h4>
              <p className="mt-1 text-xs text-slate-400">{item.frame.desired_outcome}</p>
              <p className="mt-2 text-xs text-amber-300">Potențial comercial: necunoscut; necesită validare.</p>
              {(item.supporting_sources || []).length > 0 && (
                <div className="mt-3 space-y-2">
                  <div className="text-xs font-semibold text-violet-300">Dovezi și proveniență (eșantion pe conversații distincte)</div>
                  {(item.supporting_sources || []).map((source, i) => (
                    <div key={source.source + i} className="rounded-lg border border-slate-700 bg-slate-900 p-3 text-xs">
                      <span className="mr-2 text-slate-400">{source.source}</span>
                      {source.url.startsWith('https://') && (
                        <a className="break-all text-violet-300 underline" href={source.url}
                          target="_blank" rel="noopener noreferrer">Conversația publică</a>
                      )}
                      {source.evidence.map((message, j) => (
                        <p key={message.message_id + j} className="mt-2 text-slate-300">
                          <span className="mr-2 font-mono text-violet-300">{message.message_id}</span>
                          {message.excerpt}
                        </p>
                      ))}
                      <p className="mt-1 text-amber-300">Grounding: {source.grounding_status}</p>
                    </div>
                  ))}
                </div>
              )}
              <button className="mt-3 text-xs text-violet-300 underline"
                onClick={() => setSelected(selected === item.cluster_id ? null : item.cluster_id)}>
                {selected === item.cluster_id ? 'Închide' : 'Deschide schița Genesis'}
              </button>
              {selected === item.cluster_id && (
                <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-words rounded-lg bg-slate-900 p-3 text-xs text-slate-300">
                  {JSON.stringify(item.genesis, null, 2)}
                </pre>
              )}
            </div>
          ))}
        </div>
      </div>
      {runs.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold text-violet-300">Ultimele execuții</h3>
          {runs.map(run => (
            <p key={run.id} className="mb-1 rounded-lg bg-slate-950 p-3 text-xs text-slate-300">
              {new Date(run.created_at * 1000).toLocaleString()} · {run.status} · {run.sources.join(', ')}
              {' '}· {run.inserted} adăugate · {run.errors.length} erori
            </p>
          ))}
        </div>
      )}
      <p className="text-xs text-slate-500">
        Căutarea web oferă indicii, nu dovada conversației complete. Nu sunt colectate mesaje private,
        nu se ocolesc autentificări și nu sunt estimate automat venituri sau disponibilitatea de plată.
        Workerul periodic se activează separat din configurația locală.
      </p>
    </section>
  )
}
