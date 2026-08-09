import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Settings - Autonomous Research Agent',
  description: 'Configure your research agent settings',
}

export default function SettingsPage() {
  // TODO: Fetch actual settings from API
  const settings = {
    mode: 'standard',
    autonomy: 'L1',
    maxCost: 5.0,
    maxIterations: 3,
    provider: 'auto'
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Settings</h1>
        
        <div className="space-y-6">
          {/* Research Mode */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Research Mode</h2>
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input type="radio" name="mode" value="quick" className="text-blue-600" />
                <span>Quick (fast, surface-level)</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" name="mode" value="standard" defaultChecked className="text-blue-600" />
                <span>Standard (balanced depth)</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" name="mode" value="deep" className="text-blue-600" />
                <span>Deep (comprehensive research)</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" name="mode" value="ultra-long" className="text-blue-600" />
                <span>Ultra-Long (24h+ with Temporal)</span>
              </label>
            </div>
          </div>

          {/* Autonomy Level */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Autonomy Level</h2>
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input type="radio" name="autonomy" value="L1" defaultChecked className="text-blue-600" />
                <span>L1 - Report only (default)</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" name="autonomy" value="L2" className="text-blue-600" />
                <span>L2 - Human approval gates</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" name="autonomy" value="L3" className="text-blue-600" />
                <span>L3 - Unattended with hard budgets</span>
              </label>
            </div>
          </div>

          {/* Budget Limits */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Budget Limits</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Max Cost ($)</label>
                <input
                  type="number"
                  defaultValue={settings.maxCost}
                  step="0.5"
                  min="0"
                  className="w-full px-4 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Max Iterations</label>
                <input
                  type="number"
                  defaultValue={settings.maxIterations}
                  min="1"
                  max="10"
                  className="w-full px-4 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
                />
              </div>
            </div>
          </div>

          {/* Provider Selection */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Provider Selection</h2>
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input type="radio" name="provider" value="auto" defaultChecked className="text-blue-600" />
                <span>Auto (gateway selects best)</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" name="provider" value="groq" className="text-blue-600" />
                <span>Groq (fast)</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" name="provider" value="openai" className="text-blue-600" />
                <span>OpenAI (quality)</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" name="provider" value="opencode" className="text-blue-600" />
                <span>OpenCode Zen (free)</span>
              </label>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end">
            <button className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
