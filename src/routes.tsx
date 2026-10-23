import type { RouteObject } from 'react-router';
import { Layout } from './pages/Layout';
import { LandingPage } from './pages/LandingPage';
import { OpportunitiesPage } from './pages/OpportunitiesPage';
import { OpportunityDetailPage } from './pages/OpportunityDetailPage';
import { StandardsPage } from './pages/StandardsPage';
import { AboutPage } from './pages/AboutPage';
import { AccessibilityPage, PrivacyPage, TermsPage } from './pages/LegalPages';
import { NotFoundPage, RouteErrorPage } from './pages/ErrorPages';
import { ProfilePage } from './pages/ProfilePage';
import { DashboardPage } from './pages/DashboardPage';

/** Sign-in, onboarding and employer pages are not built yet (see DESIGN.md). Profile and dashboard use a profile token, not accounts. */
export const routes: RouteObject[] = [
  {
    path: '/',
    element: <Layout />,
    errorElement: <RouteErrorPage />,
    children: [
      { index: true, element: <LandingPage /> },
      { path: 'opportunities', element: <OpportunitiesPage /> },
      { path: 'opportunities/:id', element: <OpportunityDetailPage /> },
      { path: 'profile', element: <ProfilePage /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'standards', element: <StandardsPage /> },
      { path: 'about', element: <AboutPage /> },
      { path: 'privacy', element: <PrivacyPage /> },
      { path: 'terms', element: <TermsPage /> },
      { path: 'accessibility', element: <AccessibilityPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
];
