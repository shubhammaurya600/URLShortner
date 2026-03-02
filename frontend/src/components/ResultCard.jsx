import React, { useState } from 'react';
import { Copy, Check, ExternalLink, QrCode, BarChart2, X, Calendar, Link } from 'lucide-react';
import { urlApi } from '../api/client';
import './ResultCard.css';

export default function ResultCard({ result, onClose }) {
    const [copied, setCopied] = useState(false);
    const [showQR, setShowQR] = useState(false);

    const shortUrl = result.short_url;

    const copy = async () => {
        try {
            await navigator.clipboard.writeText(shortUrl);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (_) {
            // fallback
            const el = document.createElement('input');
            el.value = shortUrl;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    return (
        <div className="result-card glass-card animate-fade-up">
            {/* Header */}
            <div className="result-card__header">
                <div className="result-card__title-row">
                    <span className="badge badge-green">✓ Link Created</span>
                    {result.expires_at && (
                        <span className="badge badge-amber">
                            <Calendar size={10} />
                            Expires {new Date(result.expires_at).toLocaleDateString()}
                        </span>
                    )}
                </div>
                <button className="result-card__close btn-ghost" onClick={onClose}>
                    <X size={16} />
                </button>
            </div>

            {/* Short URL row */}
            <div className="result-card__url-row">
                <div className="result-card__short-url">
                    <div className="result-card__url-icon">
                        <Link size={14} />
                    </div>
                    <span className="result-card__url-text mono">{shortUrl}</span>
                </div>
                <div className="result-card__actions">
                    <button className="btn-ghost" onClick={copy} title="Copy to clipboard">
                        {copied ? <Check size={15} color="var(--accent-emerald)" /> : <Copy size={15} />}
                        {copied ? 'Copied!' : 'Copy'}
                    </button>
                    <a
                        className="btn-ghost"
                        href={shortUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        title="Open link"
                    >
                        <ExternalLink size={15} />
                        Open
                    </a>
                </div>
            </div>

            {/* Original URL */}
            <div className="result-card__original">
                <span className="result-card__original-label">Original URL</span>
                <span className="result-card__original-url" title={result.original_url}>
                    {result.original_url}
                </span>
            </div>

            {/* Meta info */}
            <div className="result-card__meta">
                <div className="result-card__meta-item">
                    <span className="result-card__meta-label">Short code</span>
                    <span className="result-card__meta-value mono">{result.short_code}</span>
                </div>
                <div className="result-card__meta-item">
                    <span className="result-card__meta-label">Created</span>
                    <span className="result-card__meta-value">
                        {new Date(result.created_at).toLocaleString()}
                    </span>
                </div>
            </div>

            {/* QR/Analytics quick-links */}
            <div className="result-card__footer">
                <button
                    className="btn-ghost"
                    onClick={() => setShowQR(v => !v)}
                >
                    <QrCode size={15} />
                    {showQR ? 'Hide QR' : 'Show QR Code'}
                </button>
                <a
                    className="btn-ghost"
                    href={`/analytics/${result.short_code}`}
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    <BarChart2 size={15} />
                    Analytics
                </a>
            </div>

            {/* QR Code panel */}
            {showQR && (
                <div className="result-card__qr animate-fade-in">
                    <div className="result-card__qr-wrap">
                        <img
                            src={urlApi.qrcodeUrl(result.short_code)}
                            alt={`QR code for ${result.short_code}`}
                            className="result-card__qr-img"
                        />
                    </div>
                    <p className="result-card__qr-hint">Scan to open the shortened link</p>
                </div>
            )}
        </div>
    );
}
