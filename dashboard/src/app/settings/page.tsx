'use client';

import { Save, UserPlus, Key } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-description text-muted">Manage tenant configuration, users, and API keys.</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="flex-col gap-6" style={{ display: 'flex' }}>
          
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Tenant Configuration</h2>
            </div>
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label className="label">Organization Name</label>
              <input type="text" defaultValue="CosmicIon FinServe" className="input" />
            </div>
            <div className="form-group" style={{ marginBottom: '1.5rem' }}>
              <label className="label">Contact Email</label>
              <input type="email" defaultValue="admin@cosmicion.com" className="input" />
            </div>
            <button className="btn btn-primary"><Save size={16} /> Save Changes</button>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="card-title">API Keys</h2>
              <p className="card-description">Keys for integrating the backend with your systems.</p>
            </div>
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label className="label">Production API Key</label>
              <div className="flex gap-2">
                <input type="password" defaultValue="sk_prod_1234567890abcdef" className="input" readOnly />
                <button className="btn btn-outline"><Key size={16} /> Rotate</button>
              </div>
            </div>
          </div>

        </div>

        <div className="flex-col gap-6" style={{ display: 'flex' }}>
          
          <div className="card">
            <div className="card-header flex justify-between items-center">
              <h2 className="card-title">User Management (RBAC)</h2>
              <button className="btn btn-outline btn-sm"><UserPlus size={14} /> Invite User</button>
            </div>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Role</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="font-medium text-primary">admin@cosmicion.com</td>
                    <td><span className="badge badge-warning">Admin</span></td>
                    <td><span className="badge badge-success">Active</span></td>
                  </tr>
                  <tr>
                    <td className="font-medium text-primary">analyst@cosmicion.com</td>
                    <td><span className="badge badge-neutral">Analyst</span></td>
                    <td><span className="badge badge-success">Active</span></td>
                  </tr>
                  <tr>
                    <td className="font-medium text-primary">reviewer@cosmicion.com</td>
                    <td><span className="badge badge-neutral">Reviewer</span></td>
                    <td><span className="badge badge-neutral">Invited</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Notification Channels</h2>
            </div>
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label className="label">Slack Webhook URL</label>
              <input type="text" placeholder="https://hooks.slack.com/services/..." className="input" />
            </div>
            <div className="form-group" style={{ marginBottom: '1.5rem' }}>
              <label className="label">Critical Alert Email</label>
              <input type="email" defaultValue="soc@cosmicion.com" className="input" />
            </div>
            <button className="btn btn-primary"><Save size={16} /> Save Channels</button>
          </div>

        </div>
      </div>
    </div>
  );
}
