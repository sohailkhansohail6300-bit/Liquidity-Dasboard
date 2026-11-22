'use client';

import { useParams } from 'next/navigation';
import PortalPage from '@/features/portal/PortalPage';

export default function Page() {
  const { ticketId } = useParams();
  return <PortalPage ticketId={ticketId} />;
}
