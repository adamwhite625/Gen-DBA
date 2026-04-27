"use client";

import { useState, useEffect } from "react";
import { getPerformanceMetrics } from "@/services/api";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from "recharts";
import { Activity } from "lucide-react";

const COLORS = ['#0070F3', '#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE', '#DBEAFE'];

export default function PerformancePage() {
  const [metrics, setMetrics] = useState({ top_queries: [], table_sizes: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await getPerformanceMetrics();
        setMetrics(res.data);
      } catch (error) {
        console.error("Failed to fetch performance metrics:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    // Poll every 10 seconds for real-time updates
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="page-title">Loading performance data...</div>;
  }

  // Format data for Recharts, handling uppercase keys from Oracle
  const formatTableSizes = () => {
    return (metrics.table_sizes || [])
      .filter(t => t.TABLE_NAME && !t.TABLE_NAME.startsWith('BIN$'))
      .map(t => ({
        name: t.TABLE_NAME,
        value: t.EST_SIZE_MB || 0,
        rows: t.NUM_ROWS || 0
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 5); // Top 5
  };

  const formatQueries = () => {
    return (metrics.top_queries || [])
      .map((q, idx) => ({
        name: `Query ${idx + 1} (${q.SQL_ID})`,
        time: q.ELAPSED_MS || 0,
        gets: q.BUFFER_GETS || 0,
        reads: q.DISK_READS || 0,
        preview: q.SQL_PREVIEW || ""
      }))
      .sort((a, b) => b.time - a.time);
  };

  const tableData = formatTableSizes();
  const queryData = formatQueries();

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ backgroundColor: 'var(--bg-primary)', padding: '1rem', border: '1px solid var(--border-color)', borderRadius: 'var(--border-radius)', boxShadow: 'var(--shadow-md)' }}>
          <p style={{ fontWeight: 600, fontSize: '0.875rem', marginBottom: '0.5rem' }}>{payload[0].payload.name}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color, fontSize: '0.875rem' }}>
              {entry.name}: {entry.value.toLocaleString()} {entry.name === 'time' ? 'ms' : entry.name === 'value' ? 'MB' : ''}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ maxWidth: "1100px" }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
        <Activity color="var(--primary-blue)" size={28} />
        <h1 className="page-title" style={{ marginBottom: 0 }}>System Performance</h1>
      </div>
      <p className="page-subtitle">
        Real-time telemetry and resource consumption analytics from V$SQLAREA and DBA_TABLES.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2rem', marginBottom: '3rem' }}>
        
        {/* Table Sizes Chart */}
        <div className="card">
          <h3 style={{ fontSize: '1rem', fontWeight: 500, marginBottom: '1.5rem', color: 'var(--text-primary)' }}>
            Top Table Sizes (MB)
          </h3>
          <div style={{ height: '300px' }}>
            {tableData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={tableData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {tableData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                No table size data available
              </div>
            )}
          </div>
        </div>

        {/* Top Queries Chart */}
        <div className="card">
          <h3 style={{ fontSize: '1rem', fontWeight: 500, marginBottom: '1.5rem', color: 'var(--text-primary)' }}>
            Most Expensive Queries (Elapsed Time)
          </h3>
          <div style={{ height: '300px' }}>
            {queryData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={queryData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border-color)" />
                  <XAxis type="number" tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} />
                  <YAxis dataKey="name" type="category" width={120} tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--bg-secondary)' }} />
                  <Bar dataKey="time" name="Elapsed Time (ms)" fill="var(--primary-blue)" radius={[0, 4, 4, 0]} barSize={24} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                No active query data available
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Query Detailed Table */}
      <div className="table-container">
        <div className="table-header">
          <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>V$SQLAREA Top Consumers</span>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>SQL ID</th>
                <th>Elapsed Time (ms)</th>
                <th>Buffer Gets</th>
                <th>Disk Reads</th>
                <th style={{ width: '40%' }}>SQL Preview</th>
              </tr>
            </thead>
            <tbody>
              {queryData.length > 0 ? (
                queryData.map((q, idx) => (
                  <tr key={idx}>
                    <td style={{ fontFamily: 'monospace', fontWeight: 500 }}>{q.name.match(/\((.*?)\)/)?.[1] || q.name}</td>
                    <td>{q.time.toLocaleString()}</td>
                    <td>{q.gets.toLocaleString()}</td>
                    <td>{q.reads.toLocaleString()}</td>
                    <td style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '300px' }}>
                      {q.preview}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                    No expensive queries currently recorded.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
