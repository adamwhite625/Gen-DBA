"use client";

import { useState, useEffect } from "react";
import { getHealth, getPartitionsSummary, getAuditLog } from "@/services/api";
import { Database, LayoutTemplate, ActivitySquare, CheckCircle2, XCircle } from "lucide-react";

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [partitions, setPartitions] = useState({ partitioned_tables: [] });
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [healthRes, partRes, auditRes] = await Promise.all([
          getHealth().catch(() => ({ data: { status: "error" } })),
          getPartitionsSummary().catch(() => ({ data: { partitioned_tables: [] } })),
          getAuditLog().catch(() => ({ data: { audit_entries: [] } }))
        ]);

        setHealth(healthRes.data);
        setPartitions(partRes.data);
        // Show only last 10 logs
        const logs = auditRes.data.audit_entries || auditRes.data || [];
        setAuditLogs(Array.isArray(logs) ? logs.slice(0, 10) : []);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="page-title">Loading dashboard data...</div>;
  }

  const isHealthy = health?.connected === true || health?.status === "healthy" || health?.status === "connected";
  
  // Lọc bỏ các bảng recycle bin (bắt đầu bằng BIN$) và lấy các thuộc tính uppercase do cx_Oracle trả về
  const tables = (partitions.partitioned_tables || []).filter(t => t.TABLE_NAME && !t.TABLE_NAME.startsWith('BIN$'));
  const totalPartitions = tables.reduce((sum, t) => sum + (t.PARTITION_COUNT || 0), 0);

  return (
    <div>
      <h1 className="page-title">Database Overview</h1>
      <p className="page-subtitle">Real-time status and partition metadata for the connected Oracle instance.</p>

      {/* Metrics Cards */}
      <div className="card-grid">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Oracle Connection</span>
            <Database className="card-icon" size={20} />
          </div>
          <div className="card-value" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {isHealthy ? (
              <><CheckCircle2 color="var(--success-text)" size={28} /> Healthy</>
            ) : (
              <><XCircle color="var(--danger-text)" size={28} /> Offline</>
            )}
          </div>
          <p style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            {health?.version || health?.database?.version || "Connected"}
          </p>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Total Partitions</span>
            <LayoutTemplate className="card-icon" size={20} />
          </div>
          <div className="card-value">{totalPartitions}</div>
          <p style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            Active across the schema
          </p>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Partitioned Tables</span>
            <ActivitySquare className="card-icon" size={20} />
          </div>
          <div className="card-value">{tables.length}</div>
          <p style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            {tables.length > 0 
              ? tables.map(t => t.TABLE_NAME).join(', ') 
              : "No tables partitioned yet"}
          </p>
        </div>
      </div>

      {/* Audit Log Table */}
      <h2 className="page-title" style={{ fontSize: '1.25rem', marginTop: '2rem' }}>Recent Agent Actions</h2>
      <div className="table-container" style={{ marginTop: '1rem' }}>
        <div className="table-header">
          <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>Execution Audit Log</span>
        </div>
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Target Table</th>
              <th>Action Type</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {auditLogs.length > 0 ? (
              auditLogs.map((log) => (
                <tr key={log.id}>
                  <td>{new Date(log.timestamp).toLocaleString()}</td>
                  <td style={{ fontWeight: 500 }}>{log.table_name}</td>
                  <td>{log.action}</td>
                  <td>
                    <span className={`badge ${log.status === 'SUCCESS' ? 'badge-success' : 'badge-danger'}`}>
                      {log.status}
                    </span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="4" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                  No automated actions have been recorded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
