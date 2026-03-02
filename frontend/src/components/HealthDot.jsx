import React, { useEffect, useState } from 'react';
import { urlApi } from '../api/client';

export default function HealthDot() {
    const [status, setStatus] = useState('loading'); // 'ok' | 'degraded' | 'loading'

    useEffect(() => {
        let mounted = true;
        const check = () => {
            urlApi.health()
                .then(res => { if (mounted) setStatus(res.data.status === 'ok' ? 'ok' : 'degraded'); })
                .catch(() => { if (mounted) setStatus('degraded'); });
        };
        check();
        const interval = setInterval(check, 30000);
        return () => { mounted = false; clearInterval(interval); };
    }, []);

    const colors = {
        ok: '#10b981',
        degraded: '#f43f5e',
        loading: '#8b9cc8',
    };

    const labels = {
        ok: 'All systems operational',
        degraded: 'Service degraded',
        loading: 'Checking...',
    };

    return (
        <div className="health-dot-wrapper" title={labels[status]} style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <div style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: colors[status],
                boxShadow: status === 'ok'
                    ? '0 0 8px rgba(16, 185, 129, 0.7)'
                    : status === 'degraded'
                        ? '0 0 8px rgba(244, 63, 94, 0.7)'
                        : 'none',
                transition: 'all 0.3s ease',
                flexShrink: 0,
                ...(status === 'ok' ? { animation: 'pulse-glow 2s ease-in-out infinite' } : {}),
            }} />
            <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 500 }}>
                {status === 'ok' ? 'Live' : status === 'degraded' ? 'Issue' : '...'}
            </span>
        </div>
    );
}
