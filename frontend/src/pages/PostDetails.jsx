import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import apiService from '../services/api';

function PostDetails() {
  const { postId } = useParams();
  const [post, setPost] = useState(null);
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [enriching, setEnriching] = useState(false);

  useEffect(() => {
    loadData();
  }, [postId, filterType]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [postData, leadsData] = await Promise.all([
        apiService.getPost(postId),
        apiService.getPostLeads(
          postId,
          0,
          1000,
          filterType === 'all' ? null : filterType
        ),
      ]);

      setPost(postData);
      setLeads(leadsData);
    } catch (err) {
      setError(err.message || 'Failed to load post details');
      console.error('Error loading post details:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleEnrich = async () => {
    if (!confirm('This will enrich all leads with additional profile data. Continue?')) {
      return;
    }

    try {
      setEnriching(true);
      await apiService.enrichLeads(postId);
      alert('Enrichment started in background. Refresh the page in a few minutes to see updated data.');
    } catch (err) {
      alert('Failed to start enrichment: ' + err.message);
    } finally {
      setEnriching(false);
    }
  };

  const handleExport = (format) => {
    const url = format === 'csv'
      ? apiService.exportLeadsCSV(postId)
      : apiService.exportLeadsExcel(postId);

    window.open(url, '_blank');
  };

  if (loading) {
    return <div className="loading">Loading post details...</div>;
  }

  if (error) {
    return (
      <div className="error">
        <strong>Error:</strong> {error}
        <Link to="/" className="btn btn-secondary" style={{ marginLeft: '10px' }}>
          Back to Dashboard
        </Link>
      </div>
    );
  }

  if (!post) {
    return <div>Post not found</div>;
  }

  const enrichedCount = leads.filter(l => l.enriched).length;

  return (
    <div className="post-details">
      <div style={{ marginBottom: '20px' }}>
        <Link to="/" style={{ color: '#0a66c2', textDecoration: 'none' }}>
          ← Back to Dashboard
        </Link>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '20px' }}>
          <div>
            <h2 style={{ marginBottom: '10px' }}>Post Details</h2>
            <a href={post.post_url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '14px' }}>
              {post.post_url}
            </a>
          </div>
          <span className={`badge badge-${post.status}`} style={{ fontSize: '14px', padding: '8px 16px' }}>
            {post.status}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '20px', marginTop: '20px' }}>
          <div>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>Total Likes</div>
            <div style={{ fontSize: '24px', fontWeight: '700', color: '#0a66c2' }}>{post.total_likes}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>Total Comments</div>
            <div style={{ fontSize: '24px', fontWeight: '700', color: '#0a66c2' }}>{post.total_comments}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>Unique Leads</div>
            <div style={{ fontSize: '24px', fontWeight: '700', color: '#0a66c2' }}>{leads.length}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>Enriched</div>
            <div style={{ fontSize: '24px', fontWeight: '700', color: '#0a66c2' }}>
              {enrichedCount} / {leads.length}
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3>Leads ({leads.length})</h3>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              style={{
                padding: '8px 12px',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '14px',
              }}
            >
              <option value="all">All Interactions</option>
              <option value="like">Likes Only</option>
              <option value="comment">Comments Only</option>
              <option value="both">Both Like & Comment</option>
            </select>

            <button
              onClick={handleEnrich}
              className="btn btn-secondary"
              disabled={enriching}
            >
              {enriching ? 'Enriching...' : 'Enrich All'}
            </button>

            <button
              onClick={() => handleExport('csv')}
              className="btn btn-success"
            >
              Export CSV
            </button>

            <button
              onClick={() => handleExport('excel')}
              className="btn btn-success"
            >
              Export Excel
            </button>
          </div>
        </div>

        {leads.length === 0 ? (
          <div className="empty-state">
            <h3>No leads found</h3>
            <p>Try changing the filter or re-extract this post</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Headline</th>
                <th>Company</th>
                <th>Location</th>
                <th>Interaction</th>
                <th>Comments</th>
                <th>Enriched</th>
                <th>Profile</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => (
                <tr key={lead.id}>
                  <td>
                    <strong>{lead.full_name || 'Unknown'}</strong>
                  </td>
                  <td>{lead.headline || lead.job_title || '-'}</td>
                  <td>{lead.company || '-'}</td>
                  <td>{lead.location || '-'}</td>
                  <td>
                    <span className={`badge badge-${lead.interaction_type}`}>
                      {lead.interaction_type}
                    </span>
                  </td>
                  <td>{lead.comment_count}</td>
                  <td>{lead.enriched ? '✓' : '✗'}</td>
                  <td>
                    {lead.linkedin_profile_url && (
                      <a
                        href={lead.linkedin_profile_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-secondary"
                        style={{ padding: '4px 12px', fontSize: '12px' }}
                      >
                        View Profile
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default PostDetails;
