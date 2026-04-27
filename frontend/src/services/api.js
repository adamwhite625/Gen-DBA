import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 60000, // 60 seconds because agent analysis takes time
});

export const getHealth = () => api.get('/api/metrics/health/oracle');
export const getPartitionsSummary = () => api.get('/api/metrics/partitions/summary');
export const getAuditLog = () => api.get('/api/metrics/audit');

// Agent Endpoints
export const triggerAgentAnalysis = () => api.post('/api/agent/analyze');
export const approveAgentAction = (runId, approved = true, notes = "") => 
  api.post(`/api/partitions/approve/${runId}`, { approved, notes });
export const executeAgentAction = (runId) => api.post(`/api/agent/execute/${runId}`);

// Performance Endpoint
export const getPerformanceMetrics = () => api.get('/api/metrics/performance');

export default api;
