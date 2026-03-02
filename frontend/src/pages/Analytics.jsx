import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
    BarChart2, MousePointerClick, Globe, Smartphone, Clock,
    ArrowLeft, AlertCircle, RefreshCw, Calendar, Link2
} from 'lucide-react';
import { urlApi } from '../api/client';
import './Analytics.css';

export default function Analytics() {
    const { shortCode: paramCode } = useParams();
    const [shortCode, setShortCode] = useState(paramCode || '');
    const [inputCode, setInputCode] = useState(paramCode || '');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(!!paramCode);
    const [error, setError] = useState(null);

    const fetchAnalytics = async (code) => {
        if (!code.trim()) return;
        setLoading(true);
        setError(null);
        setData(null);
        try {
            const res = await urlApi.analytics(code.trim());
            setData(res.data);
            setShortCode(code.trim());
        } catch (err) {
            if (err.response?.status === 404) {
                setError('Short code not found. Please check and try again.');
            } else if (err.response?.status === 410) {
                setError('This link has expired or been deactivated.');
            } else {
                setError('Failed to fetch analytics. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (paramCode) fetchAnalytics(paramCode);
    }, [paramCode]);

    const handleSearch = (e) => {
        e.preventDefault();
        fetchAnalytics(inputCode);
    };

    return (
        <div className="page-container analytics-page">
            {/* Header */}
            <div className="analytics-header animate-fade-up">
                <div className="analytics-header__left">
                    <Link to="/" className="btn-ghost analytics-back-btn">
                        <ArrowLeft size={15} />
                        Back
                    </Link>
                    <div>
                        <h1 className="analytics-title">
                            <BarChart2 size={22} className="analytics-title__icon" />
                            Analytics
                        </h1>
                        <p className="analytics-subtitle">View click stats for any short link</p>
                    </div>
                </div>
            </div>

            {/* Search bar */}
            <form className="glass-card analytics-search animate-fade-up" onSubmit={handleSearch} style={{ animationDelay: '0.05s' }}>
                <div className="analytics-search__wrap">
                    <div className="analytics-search__icon"><Link2 size={15} /></div>
                    <input
                        id="analytics-code-input"
                        type="text"
                        className="input-field analytics-search__input"
                        placeholder="Enter short code (e.g. aB3xY7z)"
                        value={inputCode}
                        onChange={e => setInputCode(e.target.value)}
                    />
                </div>
                <button id="analytics-search-btn" type="submit" className="btn-primary" disabled={loading}>
                    {loading ? <div className="spinner" /> : <><RefreshCw size={14} /> Fetch</>}
                </button>
            </form>

            {/* Error state */}
            {error && (
                <div className="analytics-error glass-card animate-fade-in">
                    <AlertCircle size={20} color="var(--accent-rose)" />
                    <span>{error}</span>
                </div>
            )}

            {/* Results */}
            {data && (
                <div className="analytics-results animate-fade-up">
                    {/* Stats cards row */}
                    <div className="analytics-stats-grid">
                        <div className="analytics-stat-card glass-card">
                            <div className="analytics-stat-card__icon" style={{ background: 'rgba(99, 102, 241, 0.15)', color: 'var(--accent-indigo)' }}>
                                <MousePointerClick size={20} />
                            </div>
                            <div>
                                <div className="analytics-stat-card__value">{data.total_clicks.toLocaleString()}</div>
                                <div className="analytics-stat-card__label">Total Clicks</div>
                            </div>
                        </div>

                        <div className="analytics-stat-card glass-card">
                            <div className="analytics-stat-card__icon" style={{ background: 'rgba(6, 182, 212, 0.15)', color: 'var(--accent-cyan)' }}>
                                <Calendar size={20} />
                            </div>
                            <div>
                                <div className="analytics-stat-card__value">
                                    {new Date(data.created_at).toLocaleDateString()}
                                </div>
                                <div className="analytics-stat-card__label">Created</div>
                            </div>
                        </div>

                        <div className="analytics-stat-card glass-card">
                            <div className="analytics-stat-card__icon" style={{ background: 'rgba(244, 63, 94, 0.12)', color: 'var(--accent-rose)' }}>
                                <Clock size={20} />
                            </div>
                            <div>
                                <div className="analytics-stat-card__value">
                                    {data.expires_at ? new Date(data.expires_at).toLocaleDateString() : 'Never'}
                                </div>
                                <div className="analytics-stat-card__label">Expires</div>
                            </div>
                        </div>
                    </div>

                    {/* URL info */}
                    <div className="glass-card analytics-url-info">
                        <div className="analytics-url-row">
                            <span className="analytics-url-label">SHORT CODE</span>
                            <span className="analytics-url-value mono">{data.short_code}</span>
                        </div>
                        <div className="analytics-url-row">
                            <span className="analytics-url-label">ORIGINAL URL</span>
                            <a
                                href={data.original_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="analytics-url-link"
                            >
                                {data.original_url}
                            </a>
                        </div>
                    </div>

                    {/* Recent events */}
                    <div className="glass-card analytics-events">
                        <div className="analytics-events__header">
                            <h3 className="analytics-events__title">Recent Click Events</h3>
                            <span className="badge badge-purple">{data.recent_events.length} events</span>
                        </div>

                        {data.recent_events.length === 0 ? (
                            <div className="analytics-events__empty">
                                <MousePointerClick size={32} />
                                <p>No click events yet</p>
                                <span>Share your link to start tracking</span>
                            </div>
                        ) : (
                            <div className="analytics-events__table-wrap">
                                <table className="analytics-events__table">
                                    <thead>
                                        <tr>
                                            <th>Time</th>
                                            <th>IP Address</th>
                                            <th>User Agent</th>
                                            <th>Event ID</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.recent_events.map((event) => (
                                            <tr key={event.event_id}>
                                                <td className="mono" style={{ whiteSpace: 'nowrap', color: 'var(--text-secondary)', fontSize: 12 }}>
                                                    {new Date(event.clicked_at).toLocaleString()}
                                                </td>
                                                <td>
                                                    <span className="badge badge-cyan mono" style={{ fontWeight: 400, fontSize: 11 }}>
                                                        {event.ip_address || '—'}
                                                    </span>
                                                </td>
                                                <td className="analytics-events__ua" title={event.user_agent}>
                                                    {event.user_agent ? (
                                                        <span className="analytics-events__ua-text">{event.user_agent}</span>
                                                    ) : '—'}
                                                </td>
                                                <td className="mono" style={{ color: 'var(--text-muted)', fontSize: 11 }}>
                                                    {String(event.event_id).slice(0, 8)}…
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Initial state */}
            {!data && !loading && !error && (
                <div className="analytics-empty animate-fade-in">
                    <div className="analytics-empty__icon">
                        <BarChart2 size={40} />
                    </div>
                    <h3>Enter a short code above</h3>
                    <p>Paste any short code to view detailed click analytics and statistics.</p>
                </div>
            )}
        </div>
    );
}
