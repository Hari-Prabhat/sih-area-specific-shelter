import React, { lazy, Suspense, useEffect, useState } from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { LocaleProvider } from './i18n'
import './index.css'

const LandingPage = lazy(() => import('./LandingPage'));

/**
 * Product-hardening pass: path-based landing vs studio routing. `/` renders
 * the landing page; `/studio` renders the Design Studio. History-API routing
 * only — two routes do not justify a router dependency.
 */
function RouteRoot() {
  const [path, setPath] = useState(window.location.pathname);

  useEffect(() => {
    const onPop = () => setPath(window.location.pathname);
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  const isStudio = path.replace(/\/+$/, '') === '/studio';

  const enterStudio = () => {
    window.history.pushState({}, '', '/studio');
    setPath('/studio');
  };

  if (!isStudio) {
    return (
      <Suspense fallback={null}>
        <LandingPage onEnter={enterStudio} />
      </Suspense>
    );
  }
  return <App />;
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <LocaleProvider>
      <RouteRoot />
    </LocaleProvider>
  </React.StrictMode>,
)
