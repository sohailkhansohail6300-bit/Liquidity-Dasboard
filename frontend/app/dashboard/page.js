'use client';
import Workspace from '@/components/Workspace';
import Dashboard from '@/features/dashboard/Dashboard';

export default function Page() {
  return (
    <Workspace page="dashboard" title="Overview" roles={['client', 'multi', 'guest', 'admin']} scoped needsData>
      <Dashboard />
    </Workspace>
  );
}
