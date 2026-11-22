"""Authentication, registration, account and people-management rules, migrated from js/app.js
(``loginEmail``, ``registerFromLink``, ``acceptInvite``, ``updateAccount``, ``changePassword``, ``inviteMember``,
``updateMemberAccess``, ``removeMember``, ``setAccessAdmin``, ``removePerson``, ``addAdmin``).
Messages are the prototype's own wording."""
import secrets

from django.conf import settings
from django.contrib.auth import authenticate, login as django_login
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from administration.models import AuditLog
from companies.models import Company, CompanyAccess, SignupLink
from companies.services import link_state, next_ref
from core.exceptions import fail
from core.utils import EMAIL_RE, clean_spaces, fmt_date, real_today

from .access import Access, access_for
from .models import User

DUP_MSG = ('An account with this email address already exists. Please log in to continue. '
           'If you need access to another company, contact your administrator.')


def lc(v):
    return str(v if v is not None else '').strip().lower()


def uniq(seq):
    out = []
    for x in seq or []:
        if x not in out:
            out.append(x)
    return out


def user_by_email(email):
    e = lc(email)
    return User.objects.filter(email__iexact=e).first() if e else None


def make_token(prefix):
    return '%s-%s' % (prefix, secrets.token_urlsafe(12).replace('_', 'x').replace('-', 'y'))


def validate_password(pw, pw2):
    """``validatePassword`` - returns an error message or ''."""
    if not pw or len(pw) < 12:
        return 'Use at least 12 characters for the password.'
    if pw != pw2:
        return 'The two passwords do not match.'
    return ''


# ------------------------------------------------------------------------------------------------ sign in
def sign_in(request, email, password, remember=False):
    typed = str(email or '').strip()
    reveal = settings.LOGIN_REVEAL_ACCOUNT_STATE
    generic = 'The email or password is incorrect.'
    user = user_by_email(typed)
    if user is None:
        raise fail('No account uses that email address. Ask your administrator, or request access.' if reveal else generic, code='login_failed', status_code=400)
    if user.status != User.ACTIVE:
        raise fail('That account has not been set up yet. Open the invitation link you were given.' if reveal else generic, code='login_failed', status_code=400)
    authed = authenticate(request, username=user.email, password=password or '')
    if authed is None:
        raise fail(generic, code='login_failed', status_code=400)
    django_login(request, authed)
    request.session.set_expiry(settings.REMEMBER_ME_AGE if remember else 0)   # 0 = until the browser closes
    return authed


def login_as(request, user):
    """Sign in without a password (demo persona switching only; the view guards DELTABLOCK_DEMO_MODE)."""
    django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    request.session.set_expiry(0)
    return user


# ------------------------------------------------------------------------------------------------ registration
@transaction.atomic
def register_from_link(request, token, data):
    link = SignupLink.objects.select_for_update().filter(token=token or '').first()
    if not token or not link:
        raise fail('This sign-up link is not valid.', code='invalid')
    st = link_state(link)
    if st == 'used':
        raise fail('This link was already used.', code='used')
    if st == 'expired':
        raise fail('This link has expired.', code='expired')
    name = clean_spaces(data.get('name'))
    email = str(data.get('email') or '').strip()
    if len(name) < 2:
        raise fail('Enter your name.', code='field', errors={'name': 'Enter your name.'}, field='name')
    if not EMAIL_RE.match(email):
        raise fail('Enter a valid email address.', code='field', errors={'email': 'Enter a valid email address.'}, field='email')
    pe = validate_password(data.get('password'), data.get('confirm'))
    if pe:
        raise fail(pe, code='field', errors={'password': pe}, field='password')
    if user_by_email(email):
        raise fail(DUP_MSG, code='duplicate')
    companies = list(link.companies.order_by('id'))
    if not companies:
        raise fail('The companies for this link no longer exist. Ask your administrator for a new link.', code='invalid')
    user = User(email=email.lower(), type=User.CLIENT, is_owner=True, status=User.ACTIVE, via='Sign-up link')
    user.set_name(name)
    user.set_password(data['password'])
    user.save()
    user.tenant_owner = user
    user.save(update_fields=['tenant_owner'])
    CompanyAccess.objects.bulk_create([CompanyAccess(user=user, company=c, can_manage=True) for c in companies])
    link.status = SignupLink.USED
    link.used_on = real_today()
    link.used_by = user
    link.used_by_email = user.email
    link.save()
    AuditLog.record(user, 'signup.link_used', 'SignupLink', link.ref, companies=[c.slug for c in companies])
    django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    request.session.set_expiry(0)
    return user


@transaction.atomic
def accept_invite(request, token, data):
    user = User.objects.select_for_update().filter(invite_token=token or '', status=User.PENDING).first()
    if not token or not user:
        raise fail('This invitation is not valid or was already used.', code='invalid')
    name = clean_spaces(data.get('name'))
    if len(name) < 2:
        raise fail('Enter your name.', code='field', errors={'name': 'Enter your name.'})
    pe = validate_password(data.get('password'), data.get('confirm'))
    if pe:
        raise fail(pe, code='field', errors={'password': pe})
    user.set_name(name)
    user.set_password(data['password'])
    user.status = User.ACTIVE
    user.invite_token = None
    user.save()
    AuditLog.record(user, 'invite.accepted', 'User', user.pk, type=user.type)
    django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    request.session.set_expiry(0)
    return user


# ------------------------------------------------------------------------------------------------ my account
def update_account(user, data):
    first = clean_spaces(data.get('first'))
    last = clean_spaces(data.get('last'))
    email = str(data.get('email') or '').strip()
    errors = {}
    if not first:
        errors['first'] = 'Enter your first name.'
    elif len(first) > 60:
        errors['first'] = 'Use at most 60 characters.'
    if not last:
        errors['last'] = 'Enter your last name.'
    elif len(last) > 60:
        errors['last'] = 'Use at most 60 characters.'
    if not EMAIL_RE.match(email):
        errors['email'] = 'Enter a valid email address.'
    if 'email' not in errors and lc(email) != lc(user.email) and User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
        errors['email'] = 'Another account already uses this email address.'
    if errors:
        raise fail('Please fix the highlighted fields.', errors=errors)
    user.first_name, user.last_name, user.email = first, last, email.lower()
    user.save(update_fields=['first_name', 'last_name', 'email', 'updated_at'])
    return user


def change_password(user, current, new, confirm):
    errors = {}
    if not current:
        errors['current'] = 'Enter your current password.'
    elif not user.check_password(current):
        errors['current'] = 'The current password is not correct.'
    pe = validate_password(new, confirm)
    if pe:
        errors['confirm' if 'match' in pe else 'next'] = pe
    elif 'current' not in errors and new == current:
        errors['next'] = 'Choose a password that is different from the current one.'
    if errors:
        raise fail('Your password was not changed. Please check the highlighted fields.', errors=errors)
    user.set_password(new)
    user.save(update_fields=['password', 'updated_at'])
    AuditLog.record(user, 'account.password_changed', 'User', user.pk)


# ------------------------------------------------------------------------------------------------ Team (company based)
def team_of(company):
    qs = (User.objects.filter(accesses__company=company).exclude(type=User.ADMIN)
          .filter(Q(status=User.ACTIVE) | Q(status=User.PENDING, via='Team invite')).distinct())
    managers = set(CompanyAccess.objects.filter(company=company, can_manage=True).values_list('user_id', flat=True))
    return sorted(qs, key=lambda p: (0 if p.pk in managers else 1, p.name.casefold())), managers


def managers_of(company):
    return list(User.objects.filter(accesses__company=company, accesses__can_manage=True, status=User.ACTIVE).exclude(type=User.ADMIN).distinct())


def _companies_by_slug(slugs):
    return {c.slug: c for c in Company.objects.filter(slug__in=slugs)}


def person_companies(person):
    rows = list(CompanyAccess.objects.filter(user=person).select_related('company').order_by('company_id'))
    return [r.company.slug for r in rows], [r.company.slug for r in rows if r.can_manage]


@transaction.atomic
def invite_member(actor, data):
    acc = access_for(actor)
    if acc.role == 'guest':
        raise fail('Guests have read-only access.', status_code=403)
    email = str(data.get('email') or '').strip()
    if not EMAIL_RE.match(email):
        raise fail('Enter a valid email address.')
    cos = uniq(data.get('companies'))
    if not cos:
        raise fail('Choose at least one company.')
    for c in cos:
        if not acc.can_manage(c):
            raise fail('You can only invite people to companies whose Team you manage.', status_code=403)
    if user_by_email(email):
        raise fail('That email already has an account or an invitation. An administrator can add company access from Users → Edit access.')
    ptype = User.GUEST if data.get('type') == 'guest' else User.COLLEAGUE
    name = clean_spaces(data.get('name')) or email.split('@')[0]
    person = User(email=email.lower(), type=ptype, status=User.PENDING, via='Team invite', invited_by=actor,
                  tenant_owner=actor.tenant_owner or (actor if actor.type != User.ADMIN else None),
                  invite_token=make_token(ptype))
    person.set_name(name)
    person.set_unusable_password()
    person.save()
    by_slug = _companies_by_slug(cos)
    CompanyAccess.objects.bulk_create([CompanyAccess(user=person, company=by_slug[c], can_manage=False) for c in cos])
    AuditLog.record(actor, 'team.invite', 'User', person.pk, type=ptype, companies=cos)
    return person


def _member_guard(person, acc):
    if not person or person.type == User.ADMIN:
        return 'That person cannot be changed here.', 404
    if lc(person.email) == lc(acc.user.email):
        return 'You cannot change your own access.', 403
    scope = acc.scope()
    pcos, pmanages = person_companies(person)
    if not any(c in scope for c in pcos):
        return 'That person is not on a company you manage.', 403
    if not acc.is_admin and any(c in scope for c in pmanages):
        return 'Only an administrator can change a company manager’s access.', 403
    return '', 0


@transaction.atomic
def update_member_access(actor, person_id, selected):
    acc = access_for(actor)
    person = User.objects.select_for_update().filter(pk=person_id).first()
    msg, code = _member_guard(person, acc)
    if msg:
        raise fail(msg, status_code=code)
    selected = uniq(selected)
    for c in selected:
        if not acc.can_manage(c):
            raise fail('You can only change access for companies you manage.', status_code=403)
    scope = acc.scope()
    pcos, _ = person_companies(person)
    keep = [c for c in pcos if c not in scope]
    nxt = keep + selected
    if not nxt:
        raise fail('Keep at least one company, or use Remove to take away all access.')
    by_slug = _companies_by_slug(nxt)
    CompanyAccess.objects.filter(user=person).exclude(company__slug__in=nxt).delete()
    for c in nxt:
        CompanyAccess.objects.get_or_create(user=person, company=by_slug[c], defaults={'can_manage': False})
    AuditLog.record(actor, 'team.access_updated', 'User', person.pk, companies=nxt)
    return person


@transaction.atomic
def remove_member(actor, person_id, company_slug=None):
    acc = access_for(actor)
    person = User.objects.select_for_update().filter(pk=person_id).first()
    msg, code = _member_guard(person, acc)
    if msg:
        raise fail(msg, status_code=code)
    if company_slug and not acc.can_manage(company_slug):
        raise fail('You can only remove people from companies you manage.', status_code=403)
    scope = [company_slug] if company_slug else acc.scope()
    CompanyAccess.objects.filter(user=person, company__slug__in=scope).delete()
    deleted = not CompanyAccess.objects.filter(user=person).exists()
    AuditLog.record(actor, 'team.removed', 'User', person.pk, companies=scope, deleted=deleted, email=person.email)
    if deleted:
        person.delete()
    return deleted


# ------------------------------------------------------------------------------------------------ Users (admin)
@transaction.atomic
def set_access_admin(actor, person_id, companies, manages):
    acc = access_for(actor)
    if not acc.is_admin:
        raise fail('Only administrators can change company access here.', status_code=403)
    person = User.objects.select_for_update().filter(pk=person_id).first()
    if not person or person.type == User.ADMIN:
        raise fail('That person cannot be changed here.', status_code=404)
    existing = _companies_by_slug(uniq(companies))
    cos = [c for c in uniq(companies) if c in existing]
    if not cos:
        raise fail('Choose at least one company.')
    mg = [] if person.type == User.GUEST else [c for c in uniq(manages) if c in cos]
    CompanyAccess.objects.filter(user=person).delete()
    CompanyAccess.objects.bulk_create([CompanyAccess(user=person, company=existing[c], can_manage=c in mg) for c in cos])
    AuditLog.record(actor, 'users.access_set', 'User', person.pk, companies=cos, manages=mg)
    return person


@transaction.atomic
def remove_person(actor, person_id):
    acc = access_for(actor)
    if not acc.is_admin:
        raise fail('Only administrators can remove users.', status_code=403)
    person = User.objects.select_for_update().filter(pk=person_id).first()
    if not person:
        raise fail('User not found.', status_code=404)
    if person.pk == actor.pk or lc(person.email) == lc(actor.email):
        raise fail('You cannot remove your own account.')
    if person.type == User.ADMIN and person.status != User.PENDING:
        raise fail('Active administrators cannot be removed here.')
    AuditLog.record(actor, 'users.removed', 'User', person.pk, email=person.email, type=person.type)
    person.delete()


@transaction.atomic
def add_admin(actor, data):
    acc = access_for(actor)
    if not acc.is_admin:
        raise fail('Only administrators can add administrators.', status_code=403)
    first, last, email = clean_spaces(data.get('first')), clean_spaces(data.get('last')), str(data.get('email') or '').strip()
    for field, ok, msg in (('first', bool(first), 'Enter a first name.'), ('last', bool(last), 'Enter a last name.'),
                           ('email', bool(EMAIL_RE.match(email)), 'Enter a valid email address.')):
        if not ok:
            raise fail(msg, errors={field: msg}, field=field)
    if user_by_email(email):
        msg = 'A user with this email address already exists. Existing clients are not converted to administrators.'
        raise fail(msg, errors={'email': msg}, field='email')
    person = User(email=email.lower(), type=User.ADMIN, status=User.PENDING, first_name=first, last_name=last,
                  via='Added by ' + actor.name, invited_by=actor, invite_token=make_token('admin'))
    person.set_unusable_password()
    person.save()
    AuditLog.record(actor, 'users.admin_added', 'User', person.pk, email=person.email)
    return person
