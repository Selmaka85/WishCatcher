import { createHash, timingSafeEqual } from 'node:crypto'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'
export const maxDuration = 300

type Action = 'analyze' | 'knowledge' | 'knowledgeLink' | 'config' | 'solution'
const ROUTES: Record<Action, { method: 'POST' | 'GET'; path: string }> = {
  analyze: { method: 'POST', path: '/api/context/analyze' },
  knowledge: { method: 'POST', path: '/api/context/knowledge' },
  knowledgeLink: { method: 'POST', path: '/api/context/knowledge/link' },
  config: { method: 'GET', path: '/api/context/config' },
  solution: { method: 'POST', path: '/api/context/solution' },
}

function jsonError(message: string, status: number): Response {
  return Response.json({ detail: message }, {
    status, headers: { 'Cache-Control': 'no-store' },
  })
}

function sameSecret(value: string, expected: string): boolean {
  const a = createHash('sha256').update(value, 'utf8').digest()
  const b = createHash('sha256').update(expected, 'utf8').digest()
  return timingSafeEqual(a, b) && value.length === expected.length
}

export async function POST(request: Request): Promise<Response> {
  // Browser never gets the backend service token. A separate operator-entered
  // dashboard secret is checked server-side and never persisted in the browser.
  const dashboardSecret = process.env.WISHCATCHER_DASHBOARD_ACCESS_TOKEN || ''
  const backendSecret = process.env.WISHCATCHER_PLUGIN_ACCESS_TOKEN || ''
  if (!dashboardSecret || !backendSecret) {
    return jsonError('Dashboard not configured. Set both server secrets.', 503)
  }
  const supplied = request.headers.get('x-wishcatcher-admin') || ''
  if (!supplied || !sameSecret(supplied, dashboardSecret)) {
    return jsonError('Unauthorized: enter the dashboard access token.', 401)
  }
  const raw = await request.text()
  if (Buffer.byteLength(raw, 'utf8') > 210_000) {
    return jsonError('Request too large: maximum 210 KB.', 413)
  }

  let submitted: { action?: unknown; payload?: unknown }
  try {
    submitted = JSON.parse(raw)
  } catch {
    return jsonError('Invalid JSON input', 400)
  }
  const action = submitted.action
  if (typeof action !== 'string' || !(action in ROUTES)) {
    return jsonError('Unknown action', 400)
  }
  const route = ROUTES[action as Action]
  const configuredBase = process.env.WISHCATCHER_INTERNAL_API_URL || 'http://127.0.0.1:8000'
  let base: URL
  try {
    base = new URL(configuredBase)
    if (!['http:', 'https:'].includes(base.protocol) || base.username || base.password) {
      throw new Error('Invalid backend URL')
    }
  } catch {
    return jsonError('Backend URL configuration invalid', 503)
  }

  const target = new URL(route.path, base)
  try {
    const response = await fetch(target, {
      method: route.method,
      headers: {
        'x-wishcatcher-key': backendSecret,
        'Content-Type': 'application/json',
      },
      body: route.method === 'POST' ? JSON.stringify(submitted.payload ?? {}) : undefined,
      cache: 'no-store',
      redirect: 'error',
      signal: AbortSignal.timeout(240_000),
    })
    const answer = await response.text()
    if (Buffer.byteLength(answer, 'utf8') > 3_000_000) {
      return jsonError('Backend response too large; download using API instead.', 502)
    }
    return new Response(answer, {
      status: response.status,
      headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
    })
  } catch {
    return jsonError('Backend unavailable or timed out; check the plugin service.', 502)
  }
}
