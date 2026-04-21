import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { v2Routes } from './routes';
import { LayoutShell } from '../../components/v2/layout/LayoutShell';

export function AppV2Content() {
  return (
    <div className="v2-root">
      <LayoutShell>
        <Routes>
          {v2Routes.map((route) => (
            <Route key={route.path} path={route.path} element={route.element} />
          ))}
        </Routes>
      </LayoutShell>
    </div>
  );
}

export function AppV2() {
  return (
    <BrowserRouter>
      <AppV2Content />
    </BrowserRouter>
  );
}

export default AppV2;
