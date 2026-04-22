import type { ReactElement } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import HomeV2 from '../../pages/v2/HomeV2';
import MatchesV2 from '../../pages/v2/MatchesV2';
import MatchDetailV2 from '../../pages/v2/MatchDetailV2';
import PremiumV2 from '../../pages/v2/PremiumV2';
import AccountV2 from '../../pages/v2/AccountV2';
import ProfileTab from '../../pages/v2/account/ProfileTab';
import SubscriptionTab from '../../pages/v2/account/SubscriptionTab';
import BankrollTab from '../../pages/v2/account/BankrollTab';
import NotificationsTab from '../../pages/v2/account/NotificationsTab';
import LoginV2 from '../../pages/v2/LoginV2';
import RegisterV2 from '../../pages/v2/RegisterV2';
import { V2_REDIRECTS, buildRedirectTarget, type RedirectEntry } from './redirects';

export interface V2Route {
  path: string;
  element: ReactElement;
  isPublic: boolean;
  children?: readonly V2RouteChild[];
}

export interface V2RouteChild {
  path?: string;
  index?: boolean;
  element: ReactElement;
}

/**
 * Wrapper that converts a legacy URL into a V2 `<Navigate replace>` at render.
 *
 * Reads the current location (via `useLocation`) so that query-string
 * preservation and `:id` substitution stay stateless and test-friendly.
 */
function LegacyRedirect({ entry }: { entry: RedirectEntry }) {
  const location = useLocation();
  const target = buildRedirectTarget(
    entry.from,
    location.pathname,
    location.search,
    entry.preserveQuery,
    entry.to,
  );
  return <Navigate to={target} replace />;
}

export const v2Routes: readonly V2Route[] = [
  { path: '/', element: <HomeV2 />, isPublic: true },
  { path: '/matchs', element: <MatchesV2 />, isPublic: true },
  { path: '/matchs/:fixtureId', element: <MatchDetailV2 />, isPublic: true },
  { path: '/premium', element: <PremiumV2 />, isPublic: true },
  {
    path: '/compte',
    element: <AccountV2 />,
    isPublic: false,
    children: [
      { index: true, element: <Navigate to="profil" replace /> },
      { path: 'profil', element: <ProfileTab /> },
      { path: 'abonnement', element: <SubscriptionTab /> },
      { path: 'bankroll', element: <BankrollTab /> },
      { path: 'notifications', element: <NotificationsTab /> },
    ],
  },
  { path: '/login', element: <LoginV2 />, isPublic: true },
  { path: '/register', element: <RegisterV2 />, isPublic: true },
  // Legacy redirects (Lot 6 Bloc A) — keep last so real routes take precedence.
  ...V2_REDIRECTS.map<V2Route>((entry) => ({
    path: entry.from,
    element: <LegacyRedirect entry={entry} />,
    isPublic: true,
  })),
] as const;
