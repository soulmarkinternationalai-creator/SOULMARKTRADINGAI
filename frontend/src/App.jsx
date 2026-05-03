import { useState, useEffect, useCallback } from 'react';
import TopBar from './components/dashboard/TopBar';
import MarketView from './components/dashboard/MarketView';
import AIDecisionPanel from './components/dashboard/AIDecisionPanel';
import StrategyPanel from './components/dashboard/StrategyPanel';
import RiskPanel from './components/dashboard/RiskPanel';
import SignalHistory from './components/dashboard/SignalHistory';
import EquityCurve from './components/dashboard/EquityCurve';
import StrategyHeatmap from './components/dashboard/StrategyHeatmap';
import ConfidenceGauge from './components/dashboard/ConfidenceGauge';
import NotificationsPanel from './components/dashboard/NotificationsPanel';
import './App.css';

const API_BASE = '/api';

function App() {
  const [status, setStatus] = useState(null);
  const [currentSignal, setCurrentSignal] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [risk, setRisk] = useState(null);
  const [signalHistory, setSignalHistory] = useState([]);
  const [chartData, setChartData] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [equityCurve, setEquityCurve] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [selectedTimeframe, setSelectedTimeframe] = useState('15m');
  const [activeTab, setActiveTab] = useState('main');
  const [notifications, setNotifications] = useState([]);

  const fetchData = useCallback(async () => {
    try {
      const [statusRes, strategiesRes, riskRes, historyRes, analyticsRes, equityRes] =
        await Promise.all([
          fetch(`${API_BASE}/status`),
          fetch(`${API_BASE}/strategies`),
          fetch(`${API_BASE}/risk`),
          fetch(`${API_BASE}/signals/history?limit=50`),
          fetch(`${API_BASE}/analytics`),
          fetch(`${API_BASE}/analytics/equity-curve`),
        ]);

      if (statusRes.ok) setStatus(await statusRes.json());
      if (strategiesRes.ok) setStrategies(await strategiesRes.json());
      if (riskRes.ok) setRisk(await riskRes.json());
      if (historyRes.ok) setSignalHistory(await historyRes.json());
      if (analyticsRes.ok) setAnalytics(await analyticsRes.json());
      if (equityRes.ok) setEquityCurve(await equityRes.json());
    } catch (err) {
      console.error('Fetch error:', err);
    }
  }, []);

  const analyzeSymbol = useCallback(async (symbol) => {
    try {
      const res = await fetch(`${API_BASE}/analyze/${symbol}`);
      if (res.ok) {
        const data = await res.json();
        setCurrentSignal(data.signal);
        setChartData(data.chart_data);
        addNotification(`Analysis complete for ${symbol}: ${data.signal?.signal || 'NONE'}`);
      }
    } catch (err) {
      console.error('Analysis error:', err);
    }
  }, []);

  const addNotification = (message) => {
    setNotifications(prev => [{
      id: Date.now(),
      message,
      timestamp: new Date().toISOString(),
    }, ...prev].slice(0, 50));
  };

  useEffect(() => {
    fetchData();
    analyzeSymbol(selectedSymbol);
    const interval = setInterval(() => {
      fetchData();
      analyzeSymbol(selectedSymbol);
    }, 30000);
    return () => clearInterval(interval);
  }, [fetchData, analyzeSymbol, selectedSymbol]);

  const toggleStrategy = async (name, active) => {
    await fetch(`${API_BASE}/strategies/${encodeURIComponent(name)}/toggle?active=${active}`, { method: 'POST' });
    fetchData();
  };

  const toggleAutoTrade = async (enabled) => {
    await fetch(`${API_BASE}/execution/auto-trade?enabled=${enabled}`, { method: 'POST' });
  };

  return (
    <div className="app">
      <TopBar status={status} />

      <div className="tab-bar">
        <button className={activeTab === 'main' ? 'active' : ''} onClick={() => setActiveTab('main')}>
          Dashboard
        </button>
        <button className={activeTab === 'strategies' ? 'active' : ''} onClick={() => setActiveTab('strategies')}>
          Strategies
        </button>
        <button className={activeTab === 'analytics' ? 'active' : ''} onClick={() => setActiveTab('analytics')}>
          Analytics
        </button>
        <button className={activeTab === 'ai' ? 'active' : ''} onClick={() => setActiveTab('ai')}>
          AI Models
        </button>
      </div>

      <div className="main-content">
        {activeTab === 'main' && (
          <div className="dashboard-grid">
            <div className="panel market-panel">
              <MarketView
                chartData={chartData}
                symbol={selectedSymbol}
                timeframe={selectedTimeframe}
                onSymbolChange={(s) => { setSelectedSymbol(s); analyzeSymbol(s); }}
                onTimeframeChange={setSelectedTimeframe}
              />
            </div>

            <div className="panel decision-panel">
              <AIDecisionPanel signal={currentSignal} />
              <ConfidenceGauge confidence={currentSignal?.confidence || 0} />
            </div>

            <div className="panel risk-panel">
              <RiskPanel risk={risk} onToggleAutoTrade={toggleAutoTrade} />
            </div>

            <div className="panel heatmap-panel">
              <StrategyHeatmap signal={currentSignal} />
            </div>

            <div className="panel history-panel">
              <SignalHistory signals={signalHistory} />
            </div>

            <div className="panel notifications-panel">
              <NotificationsPanel notifications={notifications} />
            </div>
          </div>
        )}

        {activeTab === 'strategies' && (
          <div className="strategies-view">
            <StrategyPanel strategies={strategies} onToggle={toggleStrategy} />
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="analytics-view">
            <EquityCurve data={equityCurve} analytics={analytics} />
          </div>
        )}

        {activeTab === 'ai' && (
          <div className="ai-view">
            <div className="panel">
              <h3>AI / Model Panel</h3>
              <div className="ai-info">
                <div className="info-card">
                  <h4>ML Classifier</h4>
                  <p>Model Confidence: <strong>{(currentSignal?.confidence || 0).toFixed(2)}</strong></p>
                  <div className="feature-importance">
                    <h5>Top Features:</h5>
                    {currentSignal?.top_strategies?.slice(0, 5).map((s, i) => (
                      <div key={i} className="feature-bar">
                        <span>{s.name}</span>
                        <div className="bar-container">
                          <div className="bar" style={{ width: `${Math.abs(s.confidence) * 100}%` }}></div>
                        </div>
                        <span>{(Math.abs(s.confidence) * 100).toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="info-card">
                  <h4>RL Agent Decision</h4>
                  <p>Policy: <strong>{currentSignal?.signal || 'NONE'}</strong></p>
                  <p>Score: <strong>{currentSignal?.score?.toFixed(2) || '0.00'}</strong></p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
