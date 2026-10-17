import { Component, type ReactNode, type ErrorInfo } from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('YuktiOps Uncaught System Error:', error, errorInfo)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="h-screen w-screen bg-[#090D18] flex flex-col items-center justify-center p-6 text-center text-[#E7EDF7]">
          <div className="w-16 h-16 rounded-2xl bg-[#121824] border border-[#ED4245]/50 flex items-center justify-center text-[#ED4245] mb-6 shadow-2xl">
            <AlertTriangle className="w-8 h-8" />
          </div>

          <h2 className="font-display text-2xl font-bold text-white mb-2">
            System Execution Interrupted
          </h2>

          <p className="max-w-md text-sm text-[#8292AB] mb-6 leading-relaxed font-sans">
            YuktiOps encountered an unexpected runtime error. All backend webhooks and persistent states remain safe.
          </p>

          {this.state.error && (
            <div className="bg-[#121824] border border-[#202B3F] p-4 rounded-xl text-left max-w-lg w-full mb-6 text-xs font-mono text-[#ED4245] overflow-x-auto">
              <span className="text-[#8292AB] block mb-1">Diagnostic Detail:</span>
              {this.state.error.message}
            </div>
          )}

          <div className="flex items-center gap-3">
            <button
              onClick={this.handleRetry}
              className="px-5 py-2.5 bg-[#65D8FF] hover:bg-[#52c8ef] text-[#090D18] font-bold text-xs rounded-xl flex items-center gap-2 transition-colors font-mono"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Retry Component</span>
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-5 py-2.5 bg-[#151C2B] hover:bg-[#1A2335] text-white border border-[#202B3F] text-xs font-semibold rounded-xl flex items-center gap-2 transition-colors font-mono"
            >
              <Home className="w-4 h-4" />
              <span>Reload Workspace</span>
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
