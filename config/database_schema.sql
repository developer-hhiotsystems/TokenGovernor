-- TokenGovernor Workflow Database Schema
-- SQLite database for persistent workflow data storage

-- Agent States Table
CREATE TABLE agent_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('online', 'offline', 'busy', 'error', 'initializing')),
    current_task TEXT,
    last_heartbeat DATETIME DEFAULT CURRENT_TIMESTAMP,
    token_usage_current INTEGER DEFAULT 0,
    token_budget INTEGER DEFAULT 0,
    performance_metrics TEXT, -- JSON blob
    error_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_id)
);

-- Message Queue Table
CREATE TABLE message_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel TEXT NOT NULL,
    from_agent_id TEXT,
    to_agent_id TEXT,
    message_type TEXT NOT NULL,
    payload TEXT, -- JSON blob
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'delivered', 'failed', 'expired')),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    delivered_at DATETIME,
    expires_at DATETIME DEFAULT (datetime(CURRENT_TIMESTAMP, '+1 hour'))
);

-- Token Usage Table
CREATE TABLE token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    workflow_template TEXT,
    tokens_consumed INTEGER NOT NULL,
    operation_start DATETIME NOT NULL,
    operation_end DATETIME,
    context_data TEXT, -- JSON blob with operation context
    ccusage_data TEXT, -- JSON blob with ccusage tracking data
    efficiency_score REAL, -- tokens per unit of work
    success BOOLEAN DEFAULT 1,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Workflow History Table
CREATE TABLE workflow_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL,
    workflow_name TEXT NOT NULL,
    phase TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('started', 'in_progress', 'completed', 'failed', 'cancelled')),
    step_name TEXT,
    step_order INTEGER,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration_seconds INTEGER,
    tokens_used INTEGER DEFAULT 0,
    input_data TEXT, -- JSON blob
    output_data TEXT, -- JSON blob
    error_details TEXT, -- JSON blob
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Error Logs Table
CREATE TABLE error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT,
    error_type TEXT NOT NULL CHECK (error_type IN ('api_error', 'agent_failure', 'resource_exhaustion', 'communication_error', 'system_error')),
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    error_code TEXT,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    context_data TEXT, -- JSON blob
    resolution_status TEXT DEFAULT 'open' CHECK (resolution_status IN ('open', 'investigating', 'resolved', 'ignored')),
    resolution_notes TEXT,
    resolved_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Performance Metrics Table
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT,
    aggregation_period TEXT DEFAULT 'instant' CHECK (aggregation_period IN ('instant', '1min', '5min', '15min', '1hour')),
    tags TEXT, -- JSON blob for metric tags
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Swarm Configuration Table
CREATE TABLE swarm_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_version TEXT NOT NULL,
    swarm_id TEXT NOT NULL,
    topology TEXT NOT NULL,
    agent_count INTEGER NOT NULL,
    configuration_data TEXT NOT NULL, -- JSON blob with full config
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    activated_at DATETIME,
    deactivated_at DATETIME
);

-- Budget Tracking Table
CREATE TABLE budget_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    total_budget INTEGER NOT NULL,
    allocated_budget INTEGER NOT NULL,
    consumed_budget INTEGER DEFAULT 0,
    remaining_budget INTEGER,
    budget_utilization_percent REAL,
    projection_data TEXT, -- JSON blob with consumption projections
    alert_thresholds TEXT, -- JSON blob with alert configurations
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- GitHub Integration Table
CREATE TABLE github_integration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_name TEXT NOT NULL,
    repository_url TEXT NOT NULL,
    branch_name TEXT NOT NULL,
    commit_hash TEXT,
    pr_number INTEGER,
    action_type TEXT NOT NULL CHECK (action_type IN ('repo_created', 'branch_created', 'pr_created', 'pr_merged', 'action_triggered')),
    action_data TEXT, -- JSON blob with action details
    github_response TEXT, -- JSON blob with GitHub API response
    tokens_consumed INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Performance
CREATE INDEX idx_agent_states_agent_id ON agent_states(agent_id);
CREATE INDEX idx_agent_states_status ON agent_states(status);
CREATE INDEX idx_message_queue_channel ON message_queue(channel);
CREATE INDEX idx_message_queue_status ON message_queue(status);
CREATE INDEX idx_message_queue_priority ON message_queue(priority DESC);
CREATE INDEX idx_token_usage_agent_id ON token_usage(agent_id);
CREATE INDEX idx_token_usage_operation_type ON token_usage(operation_type);
CREATE INDEX idx_token_usage_created_at ON token_usage(created_at);
CREATE INDEX idx_workflow_history_workflow_id ON workflow_history(workflow_id);
CREATE INDEX idx_workflow_history_agent_id ON workflow_history(agent_id);
CREATE INDEX idx_workflow_history_status ON workflow_history(status);
CREATE INDEX idx_error_logs_agent_id ON error_logs(agent_id);
CREATE INDEX idx_error_logs_severity ON error_logs(severity);
CREATE INDEX idx_error_logs_created_at ON error_logs(created_at);
CREATE INDEX idx_performance_metrics_agent_id ON performance_metrics(agent_id);
CREATE INDEX idx_performance_metrics_collected_at ON performance_metrics(collected_at);
CREATE INDEX idx_budget_tracking_project_id ON budget_tracking(project_id);
CREATE INDEX idx_github_integration_repository_name ON github_integration(repository_name);

-- Triggers for Automatic Updates
CREATE TRIGGER update_agent_states_timestamp 
AFTER UPDATE ON agent_states
BEGIN
    UPDATE agent_states SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_remaining_budget
AFTER UPDATE ON budget_tracking
BEGIN
    UPDATE budget_tracking 
    SET remaining_budget = total_budget - consumed_budget,
        budget_utilization_percent = (consumed_budget * 100.0 / total_budget)
    WHERE id = NEW.id;
END;

-- Views for Common Queries
CREATE VIEW agent_status_summary AS
SELECT 
    agent_id,
    agent_type,
    status,
    current_task,
    token_usage_current,
    token_budget,
    ROUND((token_usage_current * 100.0 / NULLIF(token_budget, 0)), 2) as budget_utilization_percent,
    error_count,
    last_heartbeat,
    CASE 
        WHEN datetime(last_heartbeat, '+5 minutes') > datetime('now') THEN 'healthy'
        ELSE 'stale'
    END as health_status
FROM agent_states;

CREATE VIEW recent_errors AS
SELECT 
    e.agent_id,
    e.error_type,
    e.severity,
    e.error_message,
    e.resolution_status,
    e.created_at,
    a.agent_type
FROM error_logs e
LEFT JOIN agent_states a ON e.agent_id = a.agent_id
WHERE e.created_at >= datetime('now', '-24 hours')
ORDER BY e.created_at DESC;

CREATE VIEW token_usage_summary AS
SELECT 
    agent_id,
    operation_type,
    COUNT(*) as operation_count,
    SUM(tokens_consumed) as total_tokens,
    AVG(tokens_consumed) as avg_tokens_per_operation,
    AVG(efficiency_score) as avg_efficiency,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_operations,
    ROUND((SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2) as success_rate
FROM token_usage
WHERE created_at >= datetime('now', '-24 hours')
GROUP BY agent_id, operation_type;

-- Insert Initial Configuration
INSERT INTO swarm_config (config_version, swarm_id, topology, agent_count, configuration_data, status, activated_at) 
VALUES (
    '1.0.0',
    'tokengovernor-phase0-swarm',
    'hierarchical',
    3,
    '{"phase": "Phase 0", "agents": ["setup-agent-01", "pr-agent-01", "monitor-agent-01"]}',
    'active',
    CURRENT_TIMESTAMP
);

INSERT INTO budget_tracking (project_id, phase, total_budget, allocated_budget, alert_thresholds)
VALUES (
    'tokengovernor-mvp',
    'Phase 0',
    100000,
    45000,
    '{"warning": 80, "critical": 95}'
);

-- Initial Agent States
INSERT INTO agent_states (agent_id, agent_type, status, token_budget) VALUES
('setup-agent-01', 'setup', 'initializing', 35000),
('pr-agent-01', 'pr_management', 'initializing', 40000),
('monitor-agent-01', 'monitoring', 'initializing', 25000);