'use client'

import { useState, useEffect } from 'react'
import { apiGet, apiPost } from '@/lib/api'
import { ModelPicker } from '@/components'

interface Provider {
  name: string
  base_url: string
  has_auth: boolean
  models: string[]
}

export default function SettingsPage() {
  const [providers, setProviders] = useState<Provider[]>([])
  const [mode, setMode] = useState('standard')
  const [autonomy, setAutonomy] = useState('L1')
  const [maxCost, setMaxCost] = useState(5.0)
  const [maxIterations, setMaxIterations] = useState(3)
  const [selectedModel, setSelectedModel] = useState('opencode_free/nemotron-3-ultra-free')
  
  // New Provider Form State
  const [showAddProvider, setShowAddProvider] = useState(false)
  const [newProvName, setNewProvName] = useState('')
  const [newProvUrl, setNewProvUrl] = useState('')
  const [newProvKey, setNewProvKey] = useState('')
  const [newProvModels, setNewProvModels] = useState('gpt-4o, llama-3.3-70b')
  const [statusMsg, setStatusMsg] = useState('')

  useEffect(() => {
    async function fetchProviders() {
      try {
        const data = await apiGet<Provider[]>('/api/providers')
        setProviders(data)
      } catch {
        setProviders([
          { name: 'OpenCode Zen (Free)', base_url: 'https://opencode.ai/zen/v1', has_auth: false, models: ['nemotron-3-ultra-free', 'hy3-free', 'big-pickle'] },
          { name: 'Groq', base_url: 'https://api.groq.com/openai', has_auth: true, models: ['llama-3.3-70b-versatile'] },
        ])
      }
    }
    async function fetchSettings() {
      try {
        const data = await apiGet<any>('/api/settings')
        if (data.mode) setMode(data.mode)
        if (data.autonomy) setAutonomy(data.autonomy)
        if (data.max_cost != null) setMaxCost(data.max_cost)
        if (data.max_iterations != null) setMaxIterations(data.max_iterations)
        if (data.default_model) setSelectedModel(data.default_model)
      } catch {
        /* ignore */
      }
    }
    fetchProviders()
    fetchSettings()
  }, [])

  async function handleAddProvider(e: React.FormEvent) {
    e.preventDefault()
    if (!newProvName || !newProvUrl) return

    const modelsList = newProvModels.split(',').map((m) => m.trim()).filter(Boolean)
    
    try {
      await apiPost('/api/providers', {
        name: newProvName,
        base_url: newProvUrl,
        api_key: newProvKey,
        models: modelsList,
      })
      setStatusMsg(`✅ Provider '${newProvName}' added successfully!`)
      setShowAddProvider(false)
      setNewProvName('')
      setNewProvUrl('')
      setNewProvKey('')
      setProviders(await apiGet('/api/providers'))
    } catch (err: any) {
      setStatusMsg(`❌ Error: ${err.message}`)
    }
  }

  async function handleSaveSettings() {
    try {
      await apiPost('/api/settings', {
        mode,
        autonomy,
        max_cost: maxCost,
        max_iterations: maxIterations,
        default_model: selectedModel,
      })
      setStatusMsg(`✅ Settings saved. Default model: ${selectedModel}`)
    } catch (err: any) {
      setStatusMsg(`❌ Failed to save: ${err.message}`)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8 text-gray-900 dark:text-gray-100">
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold">Engine & Gateway Settings</h1>
          <p className="text-sm text-gray-500 mt-1">Configure LLM provider slots, research modes, budgets, and autonomy</p>
        </div>

        {statusMsg && (
          <div className="p-4 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-lg text-sm">
            {statusMsg}
          </div>
        )}

        {/* Model picker — Zen free first, then Groq / NIM / etc. */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
          <ModelPicker
            selected={selectedModel}
            onSelect={(provider, model) => setSelectedModel(`${provider}/${model}`)}
          />
          <p className="text-xs text-gray-500 mt-3">
            Selected default: <code className="font-mono">{selectedModel}</code>
          </p>
        </div>

        {/* Dynamic Provider Management */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">LLM Providers & Catalog Slots</h2>
            <button
              onClick={() => setShowAddProvider(!showAddProvider)}
              className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition"
            >
              {showAddProvider ? 'Cancel' : '+ Add Provider'}
            </button>
          </div>

          {showAddProvider && (
            <form onSubmit={handleAddProvider} className="mb-6 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg space-y-4 border">
              <h3 className="font-semibold text-sm">Register New Provider</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium mb-1">Provider Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Local vLLM / NVIDIA NIM"
                    value={newProvName}
                    onChange={(e) => setNewProvName(e.target.value)}
                    required
                    className="w-full px-3 py-2 text-sm rounded border bg-white dark:bg-gray-800"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">Base Endpoint URL</label>
                  <input
                    type="text"
                    placeholder="https://api.provider.com/v1"
                    value={newProvUrl}
                    onChange={(e) => setNewProvUrl(e.target.value)}
                    required
                    className="w-full px-3 py-2 text-sm rounded border bg-white dark:bg-gray-800"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">API Key (Optional)</label>
                  <input
                    type="password"
                    placeholder="sk-..."
                    value={newProvKey}
                    onChange={(e) => setNewProvKey(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded border bg-white dark:bg-gray-800"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">Models (Comma-separated)</label>
                  <input
                    type="text"
                    placeholder="model-a, model-b"
                    value={newProvModels}
                    onChange={(e) => setNewProvModels(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded border bg-white dark:bg-gray-800"
                  />
                </div>
              </div>
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition"
              >
                Register & Save Provider
              </button>
            </form>
          )}

          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {providers.map((p, i) => (
              <div key={i} className="py-3 flex justify-between items-center text-sm">
                <div>
                  <span className="font-medium">{p.name}</span>
                  <span className="ml-2 text-xs font-mono text-gray-500">{p.base_url || 'Default Free Tier'}</span>
                </div>
                <div className="flex gap-2">
                  {p.models.map((m, j) => (
                    <span key={j} className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-xs rounded font-mono">
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Research Mode Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold mb-4">Research Mode Defaults</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Mode Profile</label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className="w-full px-3 py-2 rounded border bg-white dark:bg-gray-800"
              >
                <option value="quick">Quick (fast summary)</option>
                <option value="standard">Standard (balanced research)</option>
                <option value="deep">Deep (multi-wave verification)</option>
                <option value="academic">Academic (arXiv-first, scholarly)</option>
                <option value="recency">Recency (fast-moving topics)</option>
                <option value="compare">Compare (A vs B matrix)</option>
                <option value="ultra-long">Ultra-Long (Temporal 24h)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Autonomy Level</label>
              <select
                value={autonomy}
                onChange={(e) => setAutonomy(e.target.value)}
                className="w-full px-3 py-2 rounded border bg-white dark:bg-gray-800"
              >
                <option value="L1">L1 - Autonomous report generation</option>
                <option value="L2">L2 - Human approval gates</option>
                <option value="L3">L3 - Unattended with hard budget cap</option>
              </select>
            </div>
          </div>
        </div>

        {/* Budget Limits */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold mb-4">Budget & Limit Controls</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Max Cost Cap ($ USD)</label>
              <input
                type="number"
                value={maxCost}
                onChange={(e) => setMaxCost(parseFloat(e.target.value) || 0)}
                step="0.5"
                min="0"
                className="w-full px-4 py-2 rounded border bg-white dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Max Graph Iterations</label>
              <input
                type="number"
                value={maxIterations}
                onChange={(e) => setMaxIterations(parseInt(e.target.value) || 1)}
                min="1"
                max="10"
                className="w-full px-4 py-2 rounded border bg-white dark:bg-gray-800"
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={handleSaveSettings}
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition"
          >
            Save All Settings
          </button>
        </div>
      </div>
    </div>
  )
}
