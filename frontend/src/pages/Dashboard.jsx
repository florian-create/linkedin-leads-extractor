import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiService from '../services/api';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [statsData, postsData] = await Promise.all([
        apiService.getStats(),
        apiService.getPosts(),
      ]);

      setStats(statsData);
      setPosts(postsData);
    } catch (err) {
      setError(err.message || 'Failed to load data');
      console.error('Error loading dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (postId) => {
    if (!confirm('Are you sure you want to delete this post and all its leads?')) {
      return;
    }

    try {
      await apiService.deletePost(postId);
      loadData(); // Reload data
    } catch (err) {
      alert('Failed to delete post: ' + err.message);
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  if (error) {
    return (
      <div className="error">
        <strong>Error:</strong> {error}
        <button onClick={loadData} className="btn btn-secondary" style={{ marginLeft: '10px' }}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <h2>Dashboard</h2>
        <Link to="/extract" className="btn btn-primary">
          + Extract New Leads
        </Link>
      </div>

      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Posts</h3>
            <div className="value">{stats.total_posts}</div>
          </div>
          <div className="stat-card">
            <h3>Total Leads</h3>
            <div className="value">{stats.total_leads}</div>
          </div>
          <div className="stat-card">
            <h3>Total Likes</h3>
            <div className="value">{stats.total_likes}</div>
          </div>
          <div className="stat-card">
            <h3>Total Comments</h3>
            <div className="value">{stats.total_comments}</div>
          </div>
        </div>
      )}

      <div className="card">
        <h3 style={{ marginBottom: '20px' }}>Recent Posts</h3>

        {posts.length === 0 ? (
          <div className="empty-state">
            <h3>No posts yet</h3>
            <p>Start by extracting leads from a LinkedIn post</p>
            <Link to="/extract" className="btn btn-primary" style={{ marginTop: '20px', display: 'inline-block' }}>
              Extract Leads
            </Link>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Post URL</th>
                <th>Likes</th>
                <th>Comments</th>
                <th>Status</th>
                <th>Last Scraped</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {posts.map((post) => (
                <tr key={post.id}>
                  <td>
                    <a href={post.post_url} target="_blank" rel="noopener noreferrer">
                      {post.post_url.substring(0, 60)}...
                    </a>
                  </td>
                  <td>{post.total_likes}</td>
                  <td>{post.total_comments}</td>
                  <td>
                    <span className={`badge badge-${post.status}`}>
                      {post.status}
                    </span>
                  </td>
                  <td>
                    {post.last_scraped_at
                      ? new Date(post.last_scraped_at).toLocaleString()
                      : 'Never'}
                  </td>
                  <td>
                    <Link to={`/posts/${post.id}`} className="btn btn-secondary" style={{ marginRight: '8px' }}>
                      View Leads
                    </Link>
                    <button
                      onClick={() => handleDelete(post.id)}
                      className="btn"
                      style={{ background: '#c62828', color: 'white' }}
                    >
                      Delete
                    </button>
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

export default Dashboard;
