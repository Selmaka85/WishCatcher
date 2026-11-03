'use client'

import { useState } from 'react'
import Link from 'next/link'

type Evidence = { message_id: string; author: string; excerpt: string }
type Frame = {
  source_id: string; primary_actor: string; language: string; domain: string
  problem: string; desired_outcome: string; intent: string
  constraints: string[]; attempted_solutions: string[]; rejected_alternatives: string[]
  unmet_needs: string[]; evidence: Evidence[]; other_actor_signals: Evidence[]
  confidence: number; epistemic_status: string; interpretation_method: string
  actionable: boolean; needs_review: boolean; message_count: number
}
type Analysis = {
  frame: Frame; knowledge: { id: string; excerpt: string; source: string; matched_via: string }[]
  external_research: { source_type: string; title?: string; url?: string; snippet?: string }[]
  warnings: string[]; memory_record_id: string | null
}
type PluginConfig = {
  version: string; interpreter: string; llm_enabled: boolean; llm_endpoint_type: string
  rag: string; web_search_enabled: boolean; mcp_enabled: boolean
}
type Solution = Record<string, unknown>

const SAMPLE = [
  'Owner: Am încercat trei programe de contabilitate. Toate sunt o porcărie.',
  'Owner: Primul era scump, al doilea complicat, iar al treilea nu se conecta cu banca.',
  'Owner: Eu vreau doar să termin facturile seara, fără să stau două ore.',
  'Owner: Dacă ar face cineva unul simplu, l-aș încerca imediat.',
  'Another person: Am aceeași problemă, dar mi-ar trebui o aplicație offline.',
].join('\n')

const control = 'w-full rounded-xl border border-slate-600 bg-slate-900 p-3 text-slate-50 placeholder:text-slate-500 focus:border-violet-400 focus:outline-none'
const button = 'rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-40'
const section = 'rounded-2xl border border-slate-700 bg-slate-900/70 p-5 md:p-6'

function stableId(content: string): string {
  // Deterministic grouping for repeated analysis of the SAME manual example.
  // This is not a security hash or an identifying user profile.
  let h = 2166136261
  for (let i = 0; i < content.length; i++) {
    h = Math.imul(h ^ content.charCodeAt(i), 16777619) >>> 0
  }
  return 'manual-' + h.toString(16)
}

function parseConversation(raw: string): Record<string, unknown> {
  const entries: { author: string; text: string }[] = []
  for (const original of raw.split(/\r?\n/)) {
    const line = original.trim()
    if (!line) continue
    const match = line.match(/^([^:\n]{1,55}):\s+(.+)$/)
    if (match) {
      entries.push({ author: match[1].trim(), text: match[2].trim() })
    } else if (entries.length) {
      entries[entries.length - 1].text += '\n' + line
    } else {
      entries.push({ author: 'Owner', text: line })
    }
  }
  if (!entries.length) throw new Error('Adaugă cel puțin un mesaj.')
  return {
    post_id: stableId(raw),
    post_title: '',
    post_text: entries[0].text,
    post_author: entries[0].author,
    post_timestamp: 1,
    comments: entries.slice(1).map((entry, index) => ({
      id: 'comment-' + (index + 1),
      author: entry.author, timestamp: index + 2, text: entry.text,
    })),
  }
}

function Field({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-950/60 p-4">
      <div className="mb-2 text-xs font-semibold uppercase tracking-widest text-violet-300">{title}</div>
      <div className="whitespace-pre-wrap break-words text-sm leading-relaxed text-slate-100">{children}</div>
    </div>
  )
}

function downloadJSON(data: unknown, name: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = name
  link.click()
  URL.revokeObjectURL(url)
}

export default function ContextStudio() {
  const [accessToken, setAccessToken] = useState('')
  const [conversationText, setConversationText] = useState(SAMPLE)
  const [retrieveKnowledge, setRetrieveKnowledge] = useState(true)
  const [research, setResearch] = useState(false)
  const [remember, setRemember] = useState(false)
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [solution, setSolution] = useState<Solution | null>(null)
  const [status, setStatus] = useState<PluginConfig | null>(null)
  const [tab, setTab] = useState<'analyze' | 'knowledge'>('analyze')
  const [docId, setDocId] = useState('knowledge:invoice-integration')
  const [docText, setDocText] = useState('Accounting tools often need bank synchronization and faster invoice processing.')
  const [docSource, setDocSource] = useState('operator-reviewed')
  const [linkFrom, setLinkFrom] = useState('')
  const [linkTo, setLinkTo] = useState('')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  async function invoke<T>(action: string, payload: unknown): Promise<T> {
    if (!accessToken.trim()) throw new Error('Introdu mai întâi cheia de acces pentru dashboard.')
    const response = await fetch('/api/context', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-WishCatcher-Admin': accessToken.trim(),
      },
      body: JSON.stringify({ action, payload }),
      cache: 'no-store',
    })
    let result: { detail?: string } & T
    try {
      result = await response.json()
    } catch {
      throw new Error('Răspuns invalid de la server.')
    }
    if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Eroare de server (' + response.status + ')')
    return result
  }

  async function execute(action: 'analyze' | 'solution' | 'config' | 'knowledge' | 'knowledgeLink') {
    setBusy(action); setError(''); setNotice('')
    try {
      if (action === 'analyze') {
        const result = await invoke<Analysis>('analyze', {
          conversation: parseConversation(conversationText),
          retrieve_knowledge: retrieveKnowledge, research, remember,
        })
        setAnalysis(result); setSolution(null)
        setNotice('Analiza conversației a fost finalizată.')
      } else if (action === 'solution') {
        const result = await invoke<Solution>('solution', {
          conversation: parseConversation(conversationText),
        })
        setSolution(result)
        setNotice('Genesis a produs o schiță de soluție verificabilă.')
      } else if (action === 'config') {
        setStatus(await invoke<PluginConfig>('config', {}))
        setNotice('Conexiune verificată.')
      } else if (action === 'knowledge') {
        await invoke('knowledge', { id: docId.trim(), text: docText, source: docSource, metadata: { reviewed: false } })
        setNotice('Document indexat local. Activează RAG în analiză pentru a-l regăsi.')
      } else {
        await invoke('knowledgeLink', { source_id: linkFrom, target_id: linkTo, relation: 'related' })
        setNotice('Relația graph a fost salvată.')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Eroare necunoscută.')
    } finally {
      setBusy('')
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-8 text-white md:px-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-col gap-3 border-b border-slate-800 pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="mb-2 text-xs font-bold uppercase tracking-[0.3em] text-violet-400">ASTRA GENESIS · CONTEXT INTELLIGENCE</div>
            <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">WishCatcher Studio</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-400">
              Din conversații întregi către nevoi reale: actor, problemă, scop, constrângeri și dovezi.
              LLM local/API, RAG și cercetare externă sunt opționale.
            </p>
          </div>
          <Link href="/legacy" className="text-sm text-violet-300 underline underline-offset-4 hover:text-violet-200">
            Dashboard vechi (backend complet necesar)
          </Link>
        </header>

        <section className={section}>
          <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <h2 className="text-lg font-semibold">Conectare la plugin</h2>
              <p className="text-xs text-slate-400">Cheia de dashboard rămâne numai în memoria acestei pagini; nu este trimisă modelului AI.</p>
            </div>
            <button className={button} disabled={!!busy} onClick={() => execute('config')}>Verifică integrarea</button>
          </div>
          <label htmlFor="studio-key" className="mb-2 block text-sm text-slate-300">Dashboard access token</label>
          <input id="studio-key" type="password" autoComplete="off" className={control}
            value={accessToken} onChange={e => setAccessToken(e.target.value)} placeholder="Cheia din .env" />
          {status && (
            <div className="mt-3 flex flex-wrap gap-2 text-xs">
              <span className="rounded-lg bg-slate-800 px-3 py-2">Plugin {status.version}</span>
              <span className="rounded-lg bg-slate-800 px-3 py-2">LLM: {status.llm_enabled ? status.llm_endpoint_type : 'rule fallback'}</span>
              <span className="rounded-lg bg-slate-800 px-3 py-2">RAG: {status.rag}</span>
              <span className="rounded-lg bg-slate-800 px-3 py-2">Search: {status.web_search_enabled ? 'enabled' : 'off'}</span>
              <span className="rounded-lg bg-slate-800 px-3 py-2">MCP: {status.mcp_enabled ? 'enabled' : 'off'}</span>
            </div>
          )}
        </section>

        {error && <p role="alert" className="rounded-xl border border-rose-600/60 bg-rose-950 p-4 text-sm text-rose-200">{error}</p>}
        {notice && <p role="status" className="rounded-xl border border-emerald-700/60 bg-emerald-950/60 p-4 text-sm text-emerald-200">{notice}</p>}

        <nav className="flex gap-2" aria-label="Studio views">
          <button className={tab === 'analyze' ? button : 'rounded-xl border border-slate-700 px-5 py-3 text-sm text-slate-300'}
            onClick={() => setTab('analyze')}>Conversational Context</button>
          <button className={tab === 'knowledge' ? button : 'rounded-xl border border-slate-700 px-5 py-3 text-sm text-slate-300'}
            onClick={() => setTab('knowledge')}>Knowledge / Graph RAG</button>
        </nav>

        {tab === 'analyze' ? (
          <>
            <section className={section}>
              <h2 className="mb-1 text-lg font-semibold">Fir de conversație</h2>
              <p className="mb-4 text-sm text-slate-400">
                Scrie fiecare replică în forma „Autor: mesaj”. Folosește același autor în toate clarificările sale.
                Persoanele diferite nu vor fi amestecate într-o singură intenție.
              </p>
              <label htmlFor="thread" className="sr-only">Conversație</label>
              <textarea id="thread" rows={11} className={control + ' resize-y font-mono text-sm'}
                value={conversationText} onChange={e => setConversationText(e.target.value)} />
              <div className="mt-5 flex flex-wrap gap-5 text-sm text-slate-300">
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={retrieveKnowledge} onChange={e => setRetrieveKnowledge(e.target.checked)}/>
                  Caută în RAG local
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={research} onChange={e => setResearch(e.target.checked)}/>
                  Research extern (web/MCP, dacă sunt configurate)
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)}/>
                  Memorează local rezumatul
                </label>
              </div>
              <div className="mt-5 flex flex-wrap items-center gap-3">
                <button className={button} disabled={!!busy} onClick={() => execute('analyze')}>
                  {busy === 'analyze' ? 'Analizez contextul…' : 'Analizează conversația'}
                </button>
                <button className="rounded-xl border border-violet-400/60 px-5 py-3 text-sm text-violet-200 disabled:opacity-40"
                  disabled={!!busy} onClick={() => execute('solution')}>Generează schița Genesis</button>
                <button className="rounded-xl border border-slate-700 px-5 py-3 text-sm text-slate-300"
                  onClick={() => { setConversationText(SAMPLE); setAnalysis(null); setSolution(null) }}>
                  Exemplul contabilitate
                </button>
              </div>
            </section>

            {analysis && (
              <section className={section}>
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                  <h2 className="text-lg font-semibold">Rezultatul interpretării contextuale</h2>
                  <button className="rounded-lg border border-slate-600 px-4 py-2 text-xs hover:bg-slate-800"
                    onClick={() => downloadJSON(analysis, 'wishcatcher-analysis.json')}>Export JSON</button>
                </div>
                <div className="mb-4 flex flex-wrap gap-2 text-xs text-slate-300">
                  <span className="rounded-lg bg-slate-800 px-3 py-2">{analysis.frame.domain}</span>
                  <span className="rounded-lg bg-slate-800 px-3 py-2">{analysis.frame.epistemic_status}</span>
                  <span className="rounded-lg bg-slate-800 px-3 py-2">{analysis.frame.interpretation_method}</span>
                  <span className="rounded-lg bg-slate-800 px-3 py-2">{analysis.frame.message_count} mesaje</span>
                  <span className="rounded-lg bg-slate-800 px-3 py-2">{analysis.frame.actionable ? 'De investigat' : 'Fără verdict'}</span>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <Field title="Problema">{analysis.frame.problem || 'Nu a fost identificată suficient.'}</Field>
                  <Field title="Rezultatul dorit">{analysis.frame.desired_outcome || 'Necunoscut'}</Field>
                  <Field title="Intenția reconstruită">{analysis.frame.intent || 'Nu există dovezi suficiente.'}</Field>
                  <Field title="Constrângeri">{analysis.frame.constraints.length
                    ? analysis.frame.constraints.map((c, i) => <p key={i} className="mb-1">• {c}</p>) : 'Nedeterminate'}</Field>
                </div>
                <h3 className="mb-2 mt-6 text-sm font-semibold text-violet-300">Dovezi din conversație</h3>
                {analysis.frame.evidence.length ? (
                  <div className="space-y-2">
                    {analysis.frame.evidence.map((item, i) => (
                      <div key={item.message_id + i} className="rounded-xl bg-slate-950 p-3 text-sm">
                        <span className="mr-2 font-mono text-xs text-violet-300">{item.message_id}</span>
                        <span className="mr-2 text-xs text-slate-400">{item.author}</span>
                        <span className="text-slate-200">{item.excerpt}</span>
                      </div>
                    ))}
                  </div>
                ) : <p className="text-sm text-slate-400">Nicio dovadă relevantă.</p>}
                <p className="mt-5 text-xs text-amber-300">
                  Interpretarea nu dovedește existența cererii comerciale sau disponibilitatea de plată.
                </p>
                {analysis.memory_record_id && <p className="mt-2 text-xs text-emerald-300">Memorie locală: {analysis.memory_record_id}</p>}
                {analysis.knowledge.length > 0 && (
                  <div className="mt-5">
                    <h3 className="mb-2 text-sm font-semibold text-violet-300">Knowledge Graph RAG</h3>
                    {analysis.knowledge.map((item, i) => (
                      <Field key={i} title={item.id + ' · ' + item.matched_via}>{item.excerpt}</Field>
                    ))}
                  </div>
                )}
                {analysis.external_research.length > 0 && (
                  <div className="mt-5 space-y-2">
                    <h3 className="text-sm font-semibold text-violet-300">Research extern (date neverificate)</h3>
                    {analysis.external_research.map((item, i) => (
                      <div key={i} className="rounded-xl bg-slate-950 p-3 text-sm">
                        <div>{item.title || item.source_type}</div>
                        <p className="text-slate-400">{item.snippet}</p>
                        {item.url && <a href={item.url} target="_blank" rel="noreferrer noopener"
                          className="break-all text-violet-300 underline">{item.url}</a>}
                      </div>
                    ))}
                  </div>
                )}
                {analysis.warnings.map((warning, i) =>
                  <p key={i} className="mt-2 text-sm text-amber-300">⚠ {warning}</p>)}
              </section>
            )}

            {solution && (
              <section className={section}>
                <div className="mb-4 flex items-center justify-between gap-2">
                  <h2 className="text-lg font-semibold">ASTRA Genesis · schiță de oportunitate</h2>
                  <button className="rounded-lg border border-slate-600 px-4 py-2 text-xs"
                    onClick={() => downloadJSON(solution, 'astra-genesis-brief.json')}>Export JSON</button>
                </div>
                <pre className="overflow-x-auto whitespace-pre-wrap break-words rounded-xl bg-slate-950 p-4 text-xs text-slate-200">
                  {JSON.stringify(solution, null, 2)}
                </pre>
              </section>
            )}
          </>
        ) : (
          <section className={section}>
            <h2 className="mb-2 text-lg font-semibold">Bibliotecă locală</h2>
            <p className="mb-5 text-sm text-slate-400">
              Adaugă documente aprobate și creează relații între ele. Datele sunt stocate local în SQLite,
              fără să fie trimise unui provider LLM. Salvarea se face doar la acțiunea ta.
            </p>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label htmlFor="doc-id" className="mb-2 block text-sm">ID document</label>
                <input id="doc-id" className={control} value={docId} onChange={e => setDocId(e.target.value)}/>
              </div>
              <div>
                <label htmlFor="doc-source" className="mb-2 block text-sm">Proveniență</label>
                <input id="doc-source" className={control} value={docSource} onChange={e => setDocSource(e.target.value)}/>
              </div>
            </div>
            <label htmlFor="doc-text" className="mb-2 mt-4 block text-sm">Conținut</label>
            <textarea id="doc-text" rows={5} className={control} value={docText}
              onChange={e => setDocText(e.target.value)}/>
            <button disabled={!!busy} className={button + ' mt-4'} onClick={() => execute('knowledge')}>
              Adaugă documentul în RAG
            </button>
            <h3 className="mb-3 mt-8 text-sm font-semibold text-violet-300">Leagă două documente din graph</h3>
            <div className="grid gap-3 md:grid-cols-2">
              <input aria-label="Document sursă" className={control} placeholder="source_id" value={linkFrom}
                onChange={e => setLinkFrom(e.target.value)}/>
              <input aria-label="Document țintă" className={control} placeholder="target_id" value={linkTo}
                onChange={e => setLinkTo(e.target.value)}/>
            </div>
            <button className={button + ' mt-4'} disabled={!!busy || !linkFrom || !linkTo}
              onClick={() => execute('knowledgeLink')}>Salvează relația</button>
          </section>
        )}
        <footer className="pb-6 text-center text-xs text-slate-500">
          ASTRA Genesis WishCatcher · context ≠ demand · evidence ≠ assumption · local first
        </footer>
      </div>
    </main>
  )
}
