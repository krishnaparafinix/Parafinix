import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Button from '../components/Button'
import Card from '../components/Card'
import Logo from '../components/Logo'
import { register } from '../api/auth'
import { apiErrorMessage } from '../api/client'

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', full_name: '', firm_name: '' })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form)
      setSuccess(true)
    } catch (err) {
      setError(apiErrorMessage(err, 'Registration failed. Please try again.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <Logo size="lg" />
        </div>
        <Card>
          {success ? (
            <div className="text-center">
              <h1 className="text-lg font-semibold text-navy">Account created</h1>
              <p className="mt-2 text-sm text-text-secondary">You can now sign in.</p>
              <Button className="mt-6 w-full" onClick={() => navigate('/login')}>Go to sign in</Button>
            </div>
          ) : (
            <>
              <h1 className="text-lg font-semibold text-navy">Create an account</h1>
              <p className="mt-1 text-sm text-text-secondary">For advisers and paraplanners.</p>

              <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-navy" htmlFor="full_name">Full name</label>
                  <input id="full_name" value={form.full_name} onChange={update('full_name')}
                    className="w-full rounded-lg border border-border px-3 py-2.5 text-sm outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20" />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-navy" htmlFor="firm_name">Firm name</label>
                  <input id="firm_name" value={form.firm_name} onChange={update('firm_name')}
                    className="w-full rounded-lg border border-border px-3 py-2.5 text-sm outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20" />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-navy" htmlFor="email">Email</label>
                  <input id="email" type="email" required autoComplete="email" value={form.email} onChange={update('email')}
                    className="w-full rounded-lg border border-border px-3 py-2.5 text-sm outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20" />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-navy" htmlFor="password">Password</label>
                  <input id="password" type="password" required minLength={6} autoComplete="new-password" value={form.password} onChange={update('password')}
                    className="w-full rounded-lg border border-border px-3 py-2.5 text-sm outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20" />
                </div>

                {error && <p className="text-sm text-red">{error}</p>}

                <Button type="submit" className="w-full" loading={loading}>Create account</Button>
              </form>
            </>
          )}
        </Card>
        <p className="mt-4 text-center text-sm text-text-secondary">
          Already have an account? <Link to="/login" className="font-medium text-brand-blue hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
