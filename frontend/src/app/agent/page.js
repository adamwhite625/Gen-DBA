"use client";

import { useState } from "react";
import { triggerAgentAnalysis, approveAgentAction, executeAgentAction } from "@/services/api";
import { BrainCircuit, Play, CheckCircle, XCircle, Code, Loader2 } from "lucide-react";

export default function AgentPage() {
  const [phase, setPhase] = useState("idle"); // idle, analyzing, awaiting_approval, executing, done, error
  const [runId, setRunId] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [executionReport, setExecutionReport] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  const handleAnalyze = async () => {
    setPhase("analyzing");
    setErrorMessage("");
    setExecutionReport(null);
    setRecommendations([]);

    try {
      const res = await triggerAgentAnalysis();
      const data = res.data;
      setRunId(data.run_id);
      
      if (data.error) {
        setPhase("error");
        setErrorMessage(data.error);
        return;
      }
      
      setRecommendations(data.recommendations || []);
      setPhase("awaiting_approval");
    } catch (error) {
      setPhase("error");
      setErrorMessage(error.response?.data?.detail || error.message || "Failed to analyze workload");
    }
  };

  const handleApproval = async (approved) => {
    if (!runId) return;
    
    if (!approved) {
      setPhase("idle");
      setRecommendations([]);
      return;
    }

    setPhase("executing");
    try {
      await approveAgentAction(runId, true);
      const res = await executeAgentAction(runId);
      const data = res.data;

      if (data.error) {
        setPhase("error");
        setErrorMessage(data.error);
        return;
      }

      setExecutionReport({
        ddl: data.executed_ddl,
        report: data.improvement_report
      });
      setPhase("done");
    } catch (error) {
      setPhase("error");
      setErrorMessage(error.response?.data?.detail || error.message || "Failed to execute changes");
    }
  };

  return (
    <div style={{ maxWidth: "900px" }}>
      <h1 className="page-title">Agent Analysis</h1>
      <p className="page-subtitle">
        Trigger the Gen-DBA agent to analyze slow queries and automatically generate optimal partitioning strategies.
      </p>

      {/* Control Panel */}
      <div className="card" style={{ marginBottom: "2rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h3 style={{ fontSize: "1.125rem", fontWeight: 500, marginBottom: "0.25rem" }}>
              Workload Optimizer
            </h3>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
              The agent will inspect V$SQLAREA to find full table scans and suggest partitions.
            </p>
          </div>
          <button 
            onClick={handleAnalyze} 
            disabled={phase === "analyzing" || phase === "executing"}
            style={{
              backgroundColor: phase === "analyzing" || phase === "executing" ? "var(--bg-secondary)" : "var(--primary-blue)",
              color: phase === "analyzing" || phase === "executing" ? "var(--text-secondary)" : "white",
              padding: "0.625rem 1.25rem",
              borderRadius: "var(--border-radius)",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              fontWeight: 500,
              fontSize: "0.875rem",
              transition: "all 0.2s ease"
            }}
          >
            {phase === "analyzing" ? (
              <><Loader2 className="spinner" size={16} /> Analyzing...</>
            ) : phase === "executing" ? (
              <><Loader2 className="spinner" size={16} /> Executing...</>
            ) : (
              <><Play size={16} /> Run Analysis</>
            )}
          </button>
        </div>
      </div>

      {/* Error State */}
      {phase === "error" && (
        <div style={{ 
          backgroundColor: "var(--danger-bg)", 
          border: "1px solid #f8b4b4", 
          padding: "1rem", 
          borderRadius: "var(--border-radius)",
          marginBottom: "2rem",
          display: "flex",
          gap: "0.75rem",
          alignItems: "flex-start"
        }}>
          <XCircle color="var(--danger-text)" size={20} style={{ marginTop: "0.125rem" }} />
          <div>
            <h4 style={{ color: "var(--danger-text)", fontWeight: 500, marginBottom: "0.25rem" }}>Analysis Failed</h4>
            <p style={{ color: "var(--danger-text)", fontSize: "0.875rem", opacity: 0.9 }}>{errorMessage}</p>
          </div>
        </div>
      )}

      {/* Recommendations State */}
      {phase === "awaiting_approval" && recommendations.length > 0 && (
        <div style={{ animation: "fadeIn 0.5s ease" }}>
          <h2 className="page-title" style={{ fontSize: "1.25rem", marginBottom: "1rem" }}>
            Proposed Partitioning Strategy
          </h2>
          
          {recommendations.map((rec, idx) => (
            <div key={idx} className="card" style={{ marginBottom: "1.5rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
                <Code size={18} color="var(--primary-blue)" />
                <span style={{ fontWeight: 600 }}>Target Table: {rec.table_name}</span>
                <span className="badge badge-neutral" style={{ marginLeft: "auto" }}>{rec.partition_type}</span>
              </div>
              
              <div style={{ marginBottom: "1.5rem" }}>
                <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", marginBottom: "0.5rem", fontWeight: 500 }}>
                  Reasoning:
                </p>
                <p style={{ fontSize: "0.875rem", lineHeight: 1.6, color: "var(--text-primary)" }}>
                  {rec.reasoning}
                </p>
              </div>

              <div style={{ backgroundColor: "var(--bg-secondary)", padding: "1rem", borderRadius: "6px", overflowX: "auto" }}>
                <pre style={{ fontSize: "0.875rem", fontFamily: "monospace", color: "var(--text-primary)" }}>
                  <code>{rec.proposed_ddl}</code>
                </pre>
              </div>
            </div>
          ))}

          <div style={{ display: "flex", gap: "1rem", justifyContent: "flex-end", marginTop: "1rem" }}>
            <button 
              onClick={() => handleApproval(false)}
              style={{
                padding: "0.625rem 1.25rem",
                borderRadius: "var(--border-radius)",
                border: "1px solid var(--border-color)",
                backgroundColor: "var(--bg-primary)",
                fontWeight: 500,
                fontSize: "0.875rem",
              }}
            >
              Reject
            </button>
            <button 
              onClick={() => handleApproval(true)}
              style={{
                backgroundColor: "var(--success-text)",
                color: "white",
                padding: "0.625rem 1.5rem",
                borderRadius: "var(--border-radius)",
                fontWeight: 500,
                fontSize: "0.875rem",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem"
              }}
            >
              <CheckCircle size={16} />
              Approve & Execute
            </button>
          </div>
        </div>
      )}

      {/* No Recommendations Found */}
      {phase === "awaiting_approval" && recommendations.length === 0 && (
        <div className="card" style={{ textAlign: "center", padding: "3rem 1rem" }}>
          <BrainCircuit size={48} color="var(--border-color)" style={{ margin: "0 auto 1rem auto" }} />
          <h3 style={{ fontWeight: 500, marginBottom: "0.5rem" }}>No Changes Needed</h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
            The agent analyzed the workload but did not find any tables that would benefit from partitioning at this time.
          </p>
        </div>
      )}

      {/* Done State */}
      {phase === "done" && executionReport && (
        <div style={{ animation: "fadeIn 0.5s ease" }}>
          <div style={{ 
            backgroundColor: "var(--success-bg)", 
            padding: "1.5rem", 
            borderRadius: "var(--border-radius)",
            marginBottom: "2rem",
            display: "flex",
            gap: "1rem",
            alignItems: "flex-start"
          }}>
            <CheckCircle color="var(--success-text)" size={24} style={{ flexShrink: 0 }} />
            <div>
              <h4 style={{ color: "var(--success-text)", fontWeight: 600, fontSize: "1.125rem", marginBottom: "0.5rem" }}>
                Execution Successful
              </h4>
              <p style={{ color: "var(--success-text)", fontSize: "0.875rem", opacity: 0.9 }}>
                The partitioning strategy has been successfully applied to the database.
              </p>
            </div>
          </div>

          <h2 className="page-title" style={{ fontSize: "1.25rem", marginBottom: "1rem" }}>
            Post-Execution Report
          </h2>
          <div className="card">
            <pre style={{ fontSize: "0.875rem", fontFamily: "monospace", color: "var(--text-primary)", whiteSpace: "pre-wrap" }}>
              {executionReport.report}
            </pre>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .spinner {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
