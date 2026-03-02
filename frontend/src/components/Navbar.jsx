import React from 'react';
import { NavLink } from 'react-router-dom';
import { Link2, BarChart2, Clock, Heart } from 'lucide-react';
import HealthDot from './HealthDot';
import './Navbar.css';

const NAV_LINKS = [
    { to: '/', label: 'Shorten', icon: Link2, end: true },
    { to: '/history', label: 'History', icon: Clock },
    { to: '/health', label: 'Health', icon: Heart },
];

export default function Navbar() {
    return (
        <header className="navbar">
            <div className="navbar-inner">
                {/* Logo */}
                <NavLink to="/" className="navbar-logo">
                    <div className="logo-icon">
                        <Link2 size={18} />
                    </div>
                    <span className="logo-text">
                        <span className="gradient-text">snip</span>
                        <span>.ly</span>
                    </span>
                </NavLink>

                {/* Nav links */}
                <nav className="navbar-links">
                    {NAV_LINKS.map(({ to, label, icon: Icon, end }) => (
                        <NavLink
                            key={to}
                            to={to}
                            end={end}
                            className={({ isActive }) =>
                                `nav-link${isActive ? ' nav-link--active' : ''}`
                            }
                        >
                            <Icon size={15} />
                            {label}
                        </NavLink>
                    ))}
                </nav>

                {/* Health indicator */}
                <HealthDot />
            </div>
        </header>
    );
}
