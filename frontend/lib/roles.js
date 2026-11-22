/* UI constants carried over from js/app.js: persona labels, navigation per role, landing pages. No permissions live here:
   the Django API enforces every role and company rule, these only decide what the interface shows. */
export const ROLES = {
  client: { label: 'Client', name: 'Aisha Khan', email: 'aisha.khan@gmail.com', home: '/dashboard', homeName: 'Overview', area: 'Client workspace', member: { name: 'Mia Fischer', email: 'mia.fischer@company1.example' } },
  multi: { label: 'Multi-company client', name: 'Diego Alvarez', email: 'diego@acme.co', home: '/companies', homeName: 'Companies', area: 'Client workspace', member: { name: 'Priya Shah', email: 'priya.shah@acme.co' } },
  guest: { label: 'Guest', name: 'Jordan Lee', email: 'jordan@example.com', home: '/dashboard', homeName: 'Overview', area: 'Guest access' },
  admin: { label: 'Admin', name: 'Khan Abid', email: 'khan@gmail.com', home: '/admin', homeName: 'Admin overview', area: 'Admin' }
};

const CLIENT_NAV = [['/dashboard', 'Overview'], ['/market', 'Market activity'], ['/trades', 'Trade history'], ['/comparison', 'Peer comparison'], ['/reports', 'Reports'], ['/accounting', 'Statements'], ['/subscription', 'Subscription'], ['/company', 'Company profile'], ['/team', 'Team'], ['/tickets', 'Support']];
export const NAV = {
  client: CLIENT_NAV,
  multi: [['/companies', 'Companies']].concat(CLIENT_NAV),
  guest: [['/dashboard', 'Overview'], ['/market', 'Market activity'], ['/trades', 'Trade history'], ['/comparison', 'Peer comparison'], ['/reports', 'Reports'], ['/company', 'Company profile']],
  admin: [['/admin', 'Admin overview'], ['/companies', 'Companies'], ['/signup-links', 'Client sign-up links'], ['/access-requests', 'Access requests'], ['/profile-reviews', 'Profile reviews'], ['/users', 'Users'], ['/admin-subscriptions', 'Subscriptions'], ['/data-health', 'Data health'], ['/access-log', 'Access log'], ['/tickets', 'Support tickets'], ['/wireframes', 'Screen map']]
};

export const TICKET_STATUS = { ours: ['warn', 'Needs our reply'], client: ['inf', 'Waiting on client'], done: ['ok', 'Resolved'] };

export const PROFILE_FIELDS = [['legal', 'Legal name', 'text'], ['exch', 'Listed exchange', 'text'], ['shares', 'Shares outstanding', 'text'], ['float', 'Float', 'text'], ['insiders', 'Held by insiders', 'text'], ['institutions', 'Held by institutions', 'text'], ['email', 'Email', 'email'], ['phone', 'Phone', 'tel'], ['address', 'Address', 'text']];

export const MEASURES = [['Average daily volume', 'shares', 'vol'], ['Average spread', 'bps', 'spr'], ['Time at minimum spread', '%', 'tim'], ['Market turnover', '%', 'turn']];
