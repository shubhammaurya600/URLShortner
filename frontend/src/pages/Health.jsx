import React, { useState, useEffect, useCallback } from 'react';
import { Heart, CheckCircle, XCircle, RefreshCw, Database, Server, Activity } from 'lucide-react';
import { urlApi } from '../api/client';
import './Health.css';

function StatusIcon({ status }) {
    if (status === 'ok') return <CheckCircle size={18} color="var(--accent-emerald)" />;
    if (status === 'error') return <XCircle size={18} color="var(--accent-rose)" />;
    return <div className="spinner" />;
}

function ComponentCard({ name, status, icon: Icon, description }) {
    const isOk = status === 'ok';
    const isLoading = !status;
    return (
        <div className={`health-component glass-card ${isOk ? 'health-component--ok' : !isLoading ? 'health-component--error' : ''}`}>
            <div className={`health-component__icon ${isOk ? 'ok' : !isLoading ? 'error' : 'loading'}`}>
                <Icon size={20} />
            </div>
            <div className="health-component__info">
                <div className="health-component__name">{name}</div>
                <div className="health-component__desc">{description}</div>
            </div>
            <div className="health-component__status">
                <StatusIcon status={status} />
                <span className={`health-component__status-text ${isOk ? 'ok' : !isLoading ? 'error' : ''}`}>
                    {isLoading ? 'Checking…' : isOk ? 'Operational' : 'Error'}
                </span>
            </div>
        </div>
    );
}

export default function Health() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastChecked, setLastChecked] = useState(null);

    const check = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await urlApi.health();
            setData(res.data);
        } catch (err) {
            if (err.response?.data) {
                setData(err.response.data);
            } else {
                setError('Unable to reach the server.');
            }
        } finally {
            setLoading(false);
            setLastChecked(new Date());
        }
    }, []);

    useEffect(() => {
        check();
        const interval = setInterval(check, 30000);
        return () => clearInterval(interval);
    }, [check]);

    const overall = data?.status;
    const components = data?.components || {};

    return (
        <div className="page-container health-page">
            {/* Header */}
            <div className="health-header animate-fade-up">
                <div>
                    <h1 className="health-title">
                        <Heart size={22} className="health-title__icon" />
                        System Health
                    </h1>
                    <p className="health-subtitle">
                        Live status of all backend services · auto-refreshes every 30s
                    </p>
                </div>
                <button
                    id="health-refresh-btn"
                    className="btn-ghost"
                    onClick={check}
                    disabled={loading}
                >
                    <RefreshCw size={14} className={loading ? 'health-spin' : ''} />
                    Refresh
                </button>
            </div>

            {/* Overall status banner */}
            <div
                className={`health-banner glass-card animate-fade-up ${!data ? 'health-banner--loading' :
                        overall === 'ok' ? 'health-banner--ok' : 'health-banner--degraded'
                    }`}
                style={{ animationDelay: '0.05s' }}
            >
                <div className="health-banner__left">
                    <Activity size={28} className="health-banner__icon" />
                    <div>
                        <div className="health-banner__status">
                            {!data && !error ? 'Checking services…' :
                                error ? 'Cannot reach server' :
                                    overall === 'ok' ? 'All systems operational' : 'Service degraded'}
                        </div>
                        {lastChecked && (
                            <div className="health-banner__time">
                                Last checked {lastChecked.toLocaleTimeString()}
                            </div>
                        )}
                    </div>
                </div>
                <div className={`health-banner__badge ${overall === 'ok' ? 'ok' : 'error'}`}>
                    {overall === 'ok' ? '✓ ONLINE' : overall === 'degraded' ? '⚠ DEGRADED' : '—'}
                </div>
            </div>

            {/* Component breakdown */}
            <div className="health-components animate-fade-up" style={{ animationDelay: '0.1s' }}>
                <p className="section-heading">Components</p>
                <div className="health-components__list">
                    <ComponentCard
                        name="PostgreSQL"
                        status={components.postgres}
                        icon={Database}
                        description="Primary data store for URLs and click events"
                    />
                    <ComponentCard
                        name="Redis"
                        status={components.redis}
                        icon={Server}
                        description="Cache layer for fast URL redirects"
                    />
                </div>
            </div>

            {/* Error */}
            {error && (
                <div className="health-error glass-card animate-fade-in">
                    <XCircle size={20} color="var(--accent-rose)" />
                    <span>{error}</span>
                </div>
            )}
        </div>
    );
}
