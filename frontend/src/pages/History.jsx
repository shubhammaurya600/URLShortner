import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Trash2, ExternalLink, BarChart2, QrCode, Link2, Search } from 'lucide-react';
import { urlApi } from '../api/client';
import toast from 'react-hot-toast';
import './History.css';

export default function History() {
    const [history, setHistory] = useState([]);
    const [search, setSearch] = useState('');
    const [showQR, setShowQR] = useState(null); // shortCode for the visible QR

    useEffect(() => {
        const stored = JSON.parse(localStorage.getItem('url_history') || '[]');
        setHistory(stored);
    }, []);

    const removeItem = (shortCode) => {
        const next = history.filter(h => h.short_code !== shortCode);
        localStorage.setItem('url_history', JSON.stringify(next));
        setHistory(next);
        toast.success('Removed from history');
    };

    const clearAll = () => {
        localStorage.removeItem('url_history');
        setHistory([]);
        toast.success('History cleared');
    };

    const filtered = search.trim()
        ? history.filter(h =>
            h.short_code.toLowerCase().includes(search.toLowerCase()) ||
            h.original_url.toLowerCase().includes(search.toLowerCase())
        )
        : history;

    return (
        <div className="page-container history-page">
            {/* Header */}
            <div className="history-header animate-fade-up">
                <div>
                    <h1 className="history-title">
                        <Clock size={22} className="history-title__icon" />
                        Link History
                    </h1>
                    <p className="history-subtitle">Your recently shortened links (stored locally)</p>
                </div>
                {history.length > 0 && (
                    <button className="btn-ghost history-clear-btn" onClick={clearAll}>
                        <Trash2 size={14} />
                        Clear all
                    </button>
                )}
            </div>

            {/* Search */}
            {history.length > 0 && (
                <div className="history-search animate-fade-up" style={{ animationDelay: '0.05s' }}>
                    <div className="history-search__icon"><Search size={15} /></div>
                    <input
                        id="history-search"
                        type="text"
                        className="input-field history-search__input"
                        placeholder="Search by URL or code…"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                    />
                </div>
            )}

            {/* Empty state */}
            {history.length === 0 && (
                <div className="history-empty animate-fade-in">
                    <div className="history-empty__icon"><Clock size={40} /></div>
                    <h3>No history yet</h3>
                    <p>Links you shorten will appear here automatically.</p>
                    <Link to="/" className="btn-primary" style={{ marginTop: 8 }}>
                        <Link2 size={15} />
                        Shorten a link
                    </Link>
                </div>
            )}

            {/* History list */}
            {filtered.length > 0 && (
                <div className="history-list animate-fade-up" style={{ animationDelay: '0.1s' }}>
                    {filtered.map((item) => (
                        <div key={item.short_code} className="history-item glass-card">
                            <div className="history-item__main">
                                <div className="history-item__code-row">
                                    <div className="history-item__icon">
                                        <Link2 size={14} />
                                    </div>
                                    <span className="history-item__short mono">{item.short_url || urlApi.redirectUrl(item.short_code)}</span>
                                    {item.expires_at && (
                                        <span className={`badge ${new Date(item.expires_at) < new Date() ? 'badge-red' : 'badge-amber'}`} style={{ fontSize: 10 }}>
                                            {new Date(item.expires_at) < new Date() ? 'Expired' : 'Expires ' + new Date(item.expires_at).toLocaleDateString()}
                                        </span>
                                    )}
                                </div>
                                <div className="history-item__original" title={item.original_url}>
                                    {item.original_url}
                                </div>
                                <div className="history-item__meta">
                                    <span>Saved {new Date(item.saved_at).toLocaleString()}</span>
                                    {item.created_at && <span>·</span>}
                                    {item.created_at && <span>Created {new Date(item.created_at).toLocaleDateString()}</span>}
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="history-item__actions">
                                <a
                                    className="btn-ghost history-item__btn"
                                    href={item.short_url || urlApi.redirectUrl(item.short_code)}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    title="Open link"
                                >
                                    <ExternalLink size={14} />
                                </a>
                                <Link
                                    className="btn-ghost history-item__btn"
                                    to={`/analytics/${item.short_code}`}
                                    title="View analytics"
                                >
                                    <BarChart2 size={14} />
                                </Link>
                                <button
                                    className="btn-ghost history-item__btn"
                                    onClick={() => setShowQR(showQR === item.short_code ? null : item.short_code)}
                                    title="QR Code"
                                >
                                    <QrCode size={14} />
                                </button>
                                <button
                                    className="btn-ghost history-item__btn history-item__btn--delete"
                                    onClick={() => removeItem(item.short_code)}
                                    title="Remove"
                                >
                                    <Trash2 size={14} />
                                </button>
                            </div>

                            {/* Inline QR */}
                            {showQR === item.short_code && (
                                <div className="history-item__qr animate-fade-in">
                                    <img
                                        src={urlApi.qrcodeUrl(item.short_code)}
                                        alt={`QR for ${item.short_code}`}
                                        className="history-item__qr-img"
                                    />
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* No search results */}
            {history.length > 0 && filtered.length === 0 && (
                <div className="history-empty animate-fade-in" style={{ padding: '32px' }}>
                    <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>No links match "{search}"</p>
                </div>
            )}
        </div>
    );
}
