import type { CSSProperties } from 'react';
import { Link, useLocation } from 'react-router-dom';
import type { UserRole } from '../../../types/v2/common';

export interface HeaderV2Props {
  userRole: UserRole;
  trialDaysLeft?: number;
}

function roleBadge(role: UserRole, trialDaysLeft?: number): string {
  if (role === 'trial' && typeof trialDaysLeft === 'number') {
    return `Trial J-${trialDaysLeft}`;
  }
  if (role === 'premium') return 'Premium';
  if (role === 'free') return 'Free';
  if (role === 'admin') return 'Admin';
  return '';
}

function isActive(pathname: string, target: 'home' | 'matchs' | 'compte' | 'admin'): boolean {
  if (target === 'home') return pathname === '/';
  if (target === 'matchs') return pathname === '/matchs' || pathname.startsWith('/matchs/');
  if (target === 'compte') return pathname === '/compte' || pathname.startsWith('/compte/');
  if (target === 'admin') return pathname === '/admin' || pathname === '/performance';
  return false;
}

const navItemBase: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  borderRadius: 999,
  padding: '9px 14px',
  fontSize: 14,
  fontWeight: 800,
  letterSpacing: '-0.01em',
  transition: 'background 160ms ease, color 160ms ease, box-shadow 160ms ease',
};

function navItemStyle(active: boolean): CSSProperties {
  return {
    ...navItemBase,
    color: active ? '#eaf6ff' : 'var(--text-muted)',
    background: active
      ? 'linear-gradient(135deg, rgba(96,165,250,0.24), rgba(34,211,238,0.12))'
      : 'transparent',
    boxShadow: active ? 'inset 0 0 0 1px rgba(96,165,250,0.34)' : 'none',
  };
}

export function HeaderV2({ userRole, trialDaysLeft }: HeaderV2Props) {
  const badge = roleBadge(userRole, trialDaysLeft);
  const { pathname } = useLocation();
  const homeActive = isActive(pathname, 'home');
  const matchsActive = isActive(pathname, 'matchs');
  const compteActive = isActive(pathname, 'compte');
  const adminActive = isActive(pathname, 'admin');

  const showPremiumCta = userRole === 'free' || userRole === 'trial' || userRole === 'visitor';
  const showAdminAccess = userRole === 'admin';

  return (
    <header
      aria-label="Navigation principale"
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 40,
        borderBottom: '1px solid rgba(96,165,250,0.16)',
        background:
          'linear-gradient(180deg, rgba(8,13,24,0.96), rgba(8,13,24,0.82))',
        backdropFilter: 'blur(22px)',
        boxShadow: '0 18px 60px rgba(0,0,0,0.22)',
      }}
    >
      <div
        style={{
          maxWidth: 'var(--container-max)',
          margin: '0 auto',
          padding: '10px 18px',
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1fr) auto minmax(0, 1fr)',
          alignItems: 'center',
          gap: 16,
        }}
      >
        <Link
          to="/"
          aria-label="ProbaLab"
          style={{
            minWidth: 0,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            color: 'var(--text)',
          }}
        >
          <span
            data-testid="header-brand-mark"
            aria-hidden="true"
            style={{
              width: 34,
              height: 34,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 12,
              background:
                'radial-gradient(circle at 28% 18%, rgba(255,255,255,0.38), transparent 24%), linear-gradient(135deg, #60a5fa, #22d3ee)',
              color: '#061014',
              fontSize: 17,
              fontWeight: 950,
              letterSpacing: '-0.08em',
              boxShadow: '0 12px 30px rgba(34,211,238,0.22)',
            }}
          >
            P
          </span>
          <span style={{ display: 'flex', minWidth: 0, flexDirection: 'column', lineHeight: 1 }}>
            <span
              style={{
                fontSize: 18,
                fontWeight: 950,
                letterSpacing: '-0.07em',
              }}
            >
              Proba<span style={{ color: 'var(--primary)' }}>Lab</span>
            </span>
            <span
              className="hidden sm:inline"
              style={{
                marginTop: 4,
                color: 'var(--text-faint)',
                fontSize: 10,
                fontWeight: 800,
                letterSpacing: '0.14em',
                textTransform: 'uppercase',
              }}
            >
              Analyses & probabilités
            </span>
          </span>
        </Link>
        <nav
          aria-label="Navigation"
          className="hidden md:flex"
          data-testid="header-nav-pill-group"
          style={{
            gap: 4,
            padding: 4,
            borderRadius: 999,
            border: '1px solid rgba(148,163,184,0.16)',
            background: 'rgba(15,23,42,0.62)',
            boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.04)',
          }}
        >
          <Link
            to="/"
            aria-label="Accueil"
            aria-current={homeActive ? 'page' : undefined}
            data-active={homeActive ? 'true' : 'false'}
            style={navItemStyle(homeActive)}
          >
            Accueil
          </Link>
          <Link
            to="/matchs"
            aria-label="Matchs"
            aria-current={matchsActive ? 'page' : undefined}
            data-active={matchsActive ? 'true' : 'false'}
            style={navItemStyle(matchsActive)}
          >
            Matchs
          </Link>
          <Link
            to="/compte"
            aria-label="Compte"
            aria-current={compteActive ? 'page' : undefined}
            data-active={compteActive ? 'true' : 'false'}
            style={navItemStyle(compteActive)}
          >
            Compte
          </Link>
          {showAdminAccess && (
            <Link
              to="/admin"
              aria-label="Admin"
              aria-current={adminActive ? 'page' : undefined}
              data-active={adminActive ? 'true' : 'false'}
              style={navItemStyle(adminActive)}
            >
              Admin
            </Link>
          )}
        </nav>
        <div
          className="hidden md:flex"
          style={{
            justifySelf: 'end',
            alignItems: 'center',
            gap: 8,
          }}
        >
          {badge && (
            <span
              aria-label={`Statut : ${badge}`}
              className="hidden md:inline-flex"
              style={{
                alignItems: 'center',
                gap: 6,
                fontSize: 12,
                fontWeight: 800,
                padding: '7px 10px',
                borderRadius: 999,
                border: '1px solid rgba(148,163,184,0.18)',
                background: 'rgba(255,255,255,0.04)',
                color: 'var(--text-muted)',
              }}
            >
              <span
                aria-hidden="true"
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: 999,
                  background: userRole === 'premium' ? '#f59e0b' : 'var(--primary)',
                  boxShadow:
                    userRole === 'premium'
                      ? '0 0 14px rgba(245,158,11,0.55)'
                      : '0 0 14px rgba(34,211,238,0.5)',
                }}
              />
              {badge}
            </span>
          )}
          {showPremiumCta && (
            <Link
              to="/premium"
              className="hidden md:inline-flex"
              style={{
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: 999,
                padding: '8px 12px',
                background: 'linear-gradient(135deg, #fbbf24, #f59e0b)',
                color: '#101624',
                fontSize: 12,
                fontWeight: 900,
                boxShadow: '0 12px 26px rgba(245,158,11,0.22)',
              }}
            >
              Passer Premium
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}

export default HeaderV2;
