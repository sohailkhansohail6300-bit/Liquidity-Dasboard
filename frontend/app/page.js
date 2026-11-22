import { redirect } from 'next/navigation';

/* index.html in the prototype redirected to login.html. */
export default function Home() { redirect('/login'); }
