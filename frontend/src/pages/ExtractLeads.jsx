import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';

function ExtractLeads() {
  const [postUrl, setPostUrl] = useState('');
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState('');
  const [enrich, setEnrich] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      const data = await apiService.getAccounts();
      setAccounts(data.accounts || []);
      if (data.accounts && data.accounts.length > 0) {
        setSelectedAccount(data.accounts[0].id);
      }
    } catch (err) {
      console.error('Error loading accounts:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!postUrl.trim()) {
      setError('Please enter a LinkedIn post URL');
      return;
    }

    // Validate LinkedIn URL
    if (!postUrl.includes('linkedin.com')) {
      setError('Please enter a valid LinkedIn post URL');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const result = await apiService.extractLeads(
        postUrl,
        selectedAccount || null,
        enrich
      );

      setSuccess(result.message);

      // Redirect to post details after 2 seconds
      setTimeout(() => {
        navigate(`/posts/${result.data.post_id}`);
      }, 2000);

    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to extract leads');
      console.error('Error extracting leads:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="extract-leads">
      <h2>Extract Leads from LinkedIn Post</h2>
      <p style={{ color: '#666', marginBottom: '30px' }}>
        Enter a LinkedIn post URL to extract all likes and comments as leads
      </p>

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {success && (
        <div className="success">
          <strong>Success!</strong> {success}
          <br />
          <small>Redirecting to post details...</small>
        </div>
      )}

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              LinkedIn Post URL *
            </label>
            <input
              type="url"
              placeholder="https://www.linkedin.com/posts/username_activity-..."
              value={postUrl}
              onChange={(e) => setPostUrl(e.target.value)}
              disabled={loading}
              required
            />
            <small style={{ color: '#666', display: 'block', marginTop: '8px' }}>
              Example: https://www.linkedin.com/posts/username_activity-1234567890-abcd
            </small>
          </div>

          {accounts.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Unipile Account
              </label>
              <select
                value={selectedAccount}
                onChange={(e) => setSelectedAccount(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '14px',
                }}
                disabled={loading}
              >
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.username || account.id} ({account.provider})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div style={{ marginBottom: '30px' }}>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={enrich}
                onChange={(e) => setEnrich(e.target.checked)}
                disabled={loading}
                style={{ marginRight: '8px', width: 'auto' }}
              />
              <span>Enrich leads with additional profile data (slower but more complete)</span>
            </label>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ width: '100%', fontSize: '16px', padding: '14px' }}
          >
            {loading ? 'Extracting Leads...' : 'Extract Leads'}
          </button>
        </form>
      </div>

      <div className="card" style={{ marginTop: '30px', background: '#f8f9fa' }}>
        <h3 style={{ marginBottom: '16px' }}>How it works</h3>
        <ol style={{ paddingLeft: '20px', lineHeight: '1.8' }}>
          <li>Enter a LinkedIn post URL above</li>
          <li>We'll extract all the people who liked the post</li>
          <li>We'll extract all the people who commented on the post</li>
          <li>You'll get a list of unique leads with their LinkedIn profiles</li>
          <li>Optionally, we can enrich each lead with additional profile data</li>
          <li>Export your leads to CSV or Excel format</li>
        </ol>

        <div style={{ marginTop: '20px', padding: '16px', background: 'white', borderRadius: '6px' }}>
          <strong>Note:</strong> Make sure you have a valid Unipile account connected and that your LinkedIn account has access to view the post.
        </div>
      </div>
    </div>
  );
}

export default ExtractLeads;
