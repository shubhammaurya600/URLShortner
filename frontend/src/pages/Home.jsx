import React, { useState } from 'react';
import { Link2, Zap, Settings2, Calendar, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';
import { urlApi } from '../api/client';
import ResultCard from '../components/ResultCard';
import './Home.css';

export default function Home() {
    const [url, setUrl] = useState('');
    const [alias, setAlias] = useState('');
    const [expiresAt, setExpiresAt] = useState('');
    const [showAdvanced, setShowAdvanced] = useState(false);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!url.trim()) {
            toast.error('Please enter a URL to shorten');
            return;
        }
        setLoading(true);
        setResult(null);
        try {
            const payload = { original_url: url.trim() };
            if (alias.trim()) payload.custom_alias = alias.trim();
            if (expiresAt) payload.expires_at = new Date(expiresAt).toISOString();

            const res = await urlApi.shorten(payload);
            const data = res.data;
            // Save to history
            const history = JSON.parse(localStorage.getItem('url_history') || '[]');
            history.unshift({ ...data, saved_at: new Date().toISOString() });
            localStorage.setItem('url_history', JSON.stringify(history.slice(0, 50)));

            setResult(data);
            setUrl('');
            setAlias('');
            setExpiresAt('');
            toast.success('Link shortened successfully!');
        } catch (err) {
            const msg =
                err.response?.data?.original_url?.[0] ||
                err.response?.data?.custom_alias?.[0] ||
                err.response?.data?.detail ||
                err.response?.data?.non_field_errors?.[0] ||
                'Failed to shorten URL. Please try again.';
            toast.error(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page-container home-page">
            {/* Hero section */}
            <div className="home-hero animate-fade-up">
                <div className="home-hero__badge">
                    <Zap size={12} />
                    <span>Fast, reliable URL shortening</span>
                </div>
                <h1 className="home-hero__title">
                    Turn long links into<br />
                    <span className="gradient-text">powerful shortcuts</span>
                </h1>
                <p className="home-hero__subtitle">
                    Shorten any URL, track clicks with analytics, generate QR codes — all in one place.
                </p>
            </div>

            {/* Shorten form card */}
            <div className="glass-card home-form-card animate-fade-up" style={{ animationDelay: '0.1s' }}>
                <form onSubmit={handleSubmit} className="home-form">
                    {/* Main URL input */}
                    <div className="home-form__url-row">
                        <div className="home-form__url-input-wrap">
                            <div className="home-form__url-icon">
                                <Link2 size={16} />
                            </div>
                            <input
                                id="url-input"
                                type="url"
                                className="input-field home-form__url-input"
                                placeholder="Paste your long URL here…"
                                value={url}
                                onChange={e => setUrl(e.target.value)}
                                autoFocus
                                required
                            />
                        </div>
                        <button
                            id="shorten-btn"
                            type="submit"
                            className="btn-primary home-form__submit"
                            disabled={loading}
                        >
                            {loading ? (
                                <div className="spinner" />
                            ) : (
                                <>Shorten <ArrowRight size={16} /></>
                            )}
                        </button>
                    </div>

                    {/* Advanced toggle */}
                    <button
                        type="button"
                        className="home-form__advanced-toggle"
                        onClick={() => setShowAdvanced(v => !v)}
                    >
                        <Settings2 size={13} />
                        {showAdvanced ? 'Hide' : 'Show'} advanced options
                    </button>

                    {/* Advanced options */}
                    {showAdvanced && (
                        <div className="home-form__advanced animate-fade-in">
                            <div className="home-form__advanced-grid">
                                <div className="home-form__field">
                                    <label htmlFor="alias-input" className="home-form__label">
                                        Custom alias <span className="home-form__optional">(optional)</span>
                                    </label>
                                    <div className="home-form__prefix-input">
                                        <span className="home-form__prefix">snip.ly/</span>
                                        <input
                                            id="alias-input"
                                            type="text"
                                            className="input-field"
                                            placeholder="my-link"
                                            value={alias}
                                            onChange={e => setAlias(e.target.value)}
                                            minLength={3}
                                            maxLength={16}
                                            pattern="[a-zA-Z0-9\-]+"
                                        />
                                    </div>
                                    <p className="home-form__hint">3–16 characters, letters, digits, hyphens only.</p>
                                </div>

                                <div className="home-form__field">
                                    <label htmlFor="expires-input" className="home-form__label">
                                        <Calendar size={13} />
                                        Expiration date <span className="home-form__optional">(optional)</span>
                                    </label>
                                    <input
                                        id="expires-input"
                                        type="datetime-local"
                                        className="input-field"
                                        value={expiresAt}
                                        onChange={e => setExpiresAt(e.target.value)}
                                        min={new Date(Date.now() + 60000).toISOString().slice(0, 16)}
                                    />
                                </div>
                            </div>
                        </div>
                    )}
                </form>
            </div>

            {/* Result */}
            {result && (
                <div style={{ animationDelay: '0.15s' }}>
                    <ResultCard result={result} onClose={() => setResult(null)} />
                </div>
            )}

            {/* Feature pills */}
            <div className="home-features animate-fade-up" style={{ animationDelay: '0.2s' }}>
                {[
                    { emoji: '⚡', label: 'Blazing fast redirects' },
                    { emoji: '📊', label: 'Real-time analytics' },
                    { emoji: '📱', label: 'QR code generation' },
                    { emoji: '🔒', label: 'Rate limited & secure' },
                    { emoji: '⏰', label: 'Link expiration' },
                ].map(({ emoji, label }) => (
                    <div key={label} className="home-feature-pill">
                        <span>{emoji}</span>
                        <span>{label}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
