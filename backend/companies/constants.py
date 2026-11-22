"""The editable company-profile fields, in the order the prototype shows them.

key -> (label, html input type, Company attribute). Keys match the prototype's ``PROFILE_FIELDS``.
"""
PROFILE_FIELDS = [
    ('legal', 'Legal name', 'text', 'legal_name'),
    ('exch', 'Listed exchange', 'text', 'exchange'),
    ('shares', 'Shares outstanding', 'text', 'shares_outstanding'),
    ('float', 'Float', 'text', 'free_float'),
    ('insiders', 'Held by insiders', 'text', 'insiders_pct'),
    ('institutions', 'Held by institutions', 'text', 'institutions_pct'),
    ('email', 'Email', 'email', 'contact_email'),
    ('phone', 'Phone', 'tel', 'contact_phone'),
    ('address', 'Address', 'text', 'address'),
]
PROFILE_KEYS = [f[0] for f in PROFILE_FIELDS]
PROFILE_ATTR = {f[0]: f[3] for f in PROFILE_FIELDS}
PROFILE_LABEL = {f[0]: f[1] for f in PROFILE_FIELDS}

EMAIL_RE = r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$'
PHONE_RE = r'^[+()\d\s.\-]{5,25}$'
PERCENT_RE = r'^\d{1,3}(\.\d+)?%?$'
COUNT_RE = r'^[\d][\d,. ]*$'
CODE_RE = r'^[A-Z0-9][A-Z0-9.\-]{0,9}$'
