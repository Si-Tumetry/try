import { useEffect, useState, type FormEvent } from 'react';
import { Link } from 'react-router';
import { ArrowRightIcon } from '../components/Icon';
import { PhotoBand } from '../components/PhotoBand';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import {
  ApiError,
  createProfile,
  deleteProfile,
  getProfile,
  updateProfile,
  type CreatedProfile,
  type Profile,
} from '../lib/api';
import { AVAILABILITY_OPTIONS, COUNTRY_OPTIONS } from '../lib/matching';
import { clearProfileToken, getProfileToken, saveProfileToken } from '../lib/session';

const inputClass =
  'min-h-11 w-full rounded-lg border border-accent-blue/30 bg-blue-50 px-3 py-2 text-sm text-ink-900 focus:border-accent-blue';
const labelClass = 'flex flex-col gap-1.5 text-xs font-semibold text-ink-500';
const buttonClass =
  'inline-flex min-h-11 items-center justify-center rounded-full bg-accent-navy px-6 text-sm font-semibold text-white transition-colors hover:bg-ink-900 disabled:cursor-not-allowed disabled:opacity-50';

function describeError(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return 'Something went wrong. Check your connection and try again.';
}

function ProfileFields({ profile }: { profile?: Profile | null }) {
  return (
    <>
      <label className={labelClass}>
        Country you live in
        <select name="country" required defaultValue={profile?.country ?? ''} className={inputClass}>
          <option value="" disabled>
            Choose a country
          </option>
          {COUNTRY_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label className={labelClass}>
        When you can start
        <select name="availability" defaultValue={profile?.availability ?? 'flexible'} className={inputClass}>
          {AVAILABILITY_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label className="flex items-start gap-3 text-sm text-ink-700">
        <input
          type="checkbox"
          name="searchable"
          defaultChecked={profile?.searchable ?? false}
          className="mt-1 h-4 w-4 accent-accent-blue"
        />
        <span>
          Let employers find my skills. Employers see skills and evidence only, never my name or contact details.
          Off by default.
        </span>
      </label>
    </>
  );
}

function CreateProfile({ onCreated }: { onCreated: (created: CreatedProfile) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError(null);
    try {
      onCreated(await createProfile(form));
    } catch (err) {
      setError(describeError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="grid gap-6" aria-labelledby="create-heading" encType="multipart/form-data">
      <h2 id="create-heading" className="font-serif text-2xl font-medium text-ink-900">
        Upload your CV
      </h2>
      <p className="text-sm text-ink-600">
        NextStep reads your CV to find the skills you can show, then scores every listing against them. The file is
        read in memory and is not kept. Only the skills we recognise are saved. Upload a PDF, Word document or plain
        text file, up to 5 MB.
      </p>

      <label className={labelClass}>
        CV file
        <input
          type="file"
          name="cv"
          required
          accept=".pdf,.docx,.txt,.md,application/pdf,text/plain,text/markdown,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="min-h-11 w-full rounded-lg border border-dashed border-accent-blue/40 bg-blue-50 px-3 py-2 text-sm text-ink-700 file:mr-3 file:rounded-full file:border-0 file:bg-accent-navy file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white"
        />
      </label>

      <ProfileFields />

      <label className="flex items-start gap-3 text-sm text-ink-700">
        <input type="checkbox" name="consent" value="true" required className="mt-1 h-4 w-4 accent-accent-blue" />
        <span>
          I agree that NextStep reads the skills in my CV to score me against listings. I can change this or delete my
          profile at any time.
        </span>
      </label>

      {error && (
        <p role="alert" className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900">
          {error}
        </p>
      )}

      <div>
        <button type="submit" disabled={busy} className={buttonClass}>
          {busy ? 'Reading your CV…' : 'Create my profile'}
        </button>
      </div>
    </form>
  );
}

function ManageProfile({
  token,
  profile,
  onProfile,
  onDeleted,
}: {
  token: string;
  profile: Profile;
  onProfile: (profile: Profile) => void;
  onDeleted: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      onProfile(await updateProfile(token, form));
      setSaved(true);
    } catch (err) {
      setError(describeError(err));
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    setBusy(true);
    setError(null);
    try {
      await deleteProfile(token);
      onDeleted();
    } catch (err) {
      setError(describeError(err));
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_360px]">
      <section aria-labelledby="skills-heading" className="space-y-6">
        <div>
          <h2 id="skills-heading" className="font-serif text-2xl font-medium text-ink-900">
            Skills from your CV
          </h2>
          <p className="mt-2 text-sm text-ink-600">
            {profile.skills.length === 0
              ? 'No skills saved yet.'
              : `${profile.skills.length} ${profile.skills.length === 1 ? 'skill' : 'skills'} recognised. Skills named more than once in your CV carry more weight.`}
          </p>
        </div>

        <ul className="flex flex-wrap gap-2" aria-label="Skills">
          {profile.skills.map((skill) => (
            <li
              key={skill.skill_id}
              className={`rounded-full px-3 py-1 text-sm ${skill.level >= 3 ? 'bg-accent-blue text-white' : 'border border-accent-blue/30 bg-blue-50 text-accent-navy'}`}
            >
              {skill.name}
            </li>
          ))}
        </ul>

        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 rounded-full bg-accent-navy px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-ink-900"
        >
          See my matches <ArrowRightIcon aria-hidden="true" />
        </Link>
      </section>

      <aside className="space-y-8">
        <form onSubmit={save} className="grid gap-5 rounded-2xl border border-blue-300/60 bg-blue-50 p-6" aria-labelledby="update-heading" encType="multipart/form-data">
          <h2 id="update-heading" className="font-serif text-xl font-medium text-ink-900">
            Update your profile
          </h2>
          <ProfileFields profile={profile} />
          <label className={labelClass}>
            Replace CV (optional)
            <input
              type="file"
              name="cv"
              accept=".pdf,.docx,.txt,.md"
              className="min-h-11 w-full rounded-lg border border-dashed border-accent-blue/40 bg-blue-100 px-3 py-2 text-sm text-ink-700 file:mr-3 file:rounded-full file:border-0 file:bg-accent-navy file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white"
            />
          </label>
          {error && (
            <p role="alert" className="text-sm text-red-900">
              {error}
            </p>
          )}
          {saved && (
            <p role="status" className="text-sm text-accent-navy">
              Saved. Your matches have been updated.
            </p>
          )}
          <button type="submit" disabled={busy} className={buttonClass}>
            Save changes
          </button>
        </form>

        <div className="rounded-2xl border border-blue-300/60 bg-blue-50 p-6">
          <h2 className="font-serif text-xl font-medium text-ink-900">Delete my profile</h2>
          <p className="mt-2 text-sm text-ink-600">
            Removes your skills and your matches. This cannot be undone.
          </p>
          {confirming ? (
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={remove}
                disabled={busy}
                className="min-h-11 rounded-full bg-red-800 px-5 text-sm font-semibold text-white hover:bg-red-900 disabled:opacity-50"
              >
                Yes, delete everything
              </button>
              <button
                type="button"
                onClick={() => setConfirming(false)}
                className="min-h-11 rounded-full border border-accent-blue/30 px-5 text-sm font-semibold text-ink-900 hover:bg-blue-200"
              >
                Keep my profile
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setConfirming(true)}
              className="mt-4 min-h-11 rounded-full border border-red-300 px-5 text-sm font-semibold text-red-900 hover:bg-red-50"
            >
              Delete profile
            </button>
          )}
        </div>
      </aside>
    </div>
  );
}

export function ProfilePage() {
  useDocumentTitle('My profile');
  const [token, setToken] = useState<string | null>(() => getProfileToken());
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [ready, setReady] = useState(!token);

  useEffect(() => {
    if (!token) return;
    let active = true;
    getProfile(token)
      .then((found) => {
        if (active) setProfile(found);
      })
      .catch((err: unknown) => {
        if (!active) return;
        if (err instanceof ApiError && err.status === 401) {
          clearProfileToken();
          setToken(null);
        } else {
          setLoadError(describeError(err));
        }
      })
      .finally(() => {
        if (active) setReady(true);
      });
    return () => {
      active = false;
    };
  }, [token]);

  function handleCreated({ token: newToken, profile: created }: CreatedProfile) {
    saveProfileToken(newToken);
    setToken(newToken);
    setProfile(created);
  }

  function handleDeleted() {
    clearProfileToken();
    setToken(null);
    setProfile(null);
  }

  return (
    <>
      <PhotoBand image="/images/about-office.jpg" innerClassName="py-14 md:py-16">
        <p className="mb-3 font-mono text-xs tracking-wider text-blue-200 uppercase">Your profile</p>
        <h1 className="max-w-3xl font-serif text-4xl leading-tight font-normal text-white md:text-5xl">
          {token && profile ? 'Your skills, ready to match.' : 'Upload your CV to get scored.'}
        </h1>
        <p className="mt-4 max-w-2xl text-base text-blue-100">
          Every listing gets a score from the skills you can show, with the gaps and the next project for each one.
        </p>
      </PhotoBand>

      <div className="mx-auto max-w-6xl px-6 py-14 lg:px-12">
        {!ready && <p role="status" className="text-sm text-ink-600">Loading your profile…</p>}

        {ready && loadError && (
          <p role="alert" className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900">
            {loadError}
          </p>
        )}

        {ready && !token && (
          <div className="mx-auto max-w-2xl rounded-2xl border border-blue-300/60 bg-blue-50 p-8">
            <CreateProfile onCreated={handleCreated} />
          </div>
        )}

        {ready && token && profile && (
          <ManageProfile token={token} profile={profile} onProfile={setProfile} onDeleted={handleDeleted} />
        )}
      </div>
    </>
  );
}
