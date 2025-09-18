-- Migration: Create auto-save related tables
-- Description: Creates auto_save_settings and auto_save_transactions tables

CREATE TABLE auto_save_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES "safeLock_account"(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wallet_id UUID NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('daily', 'weekly', 'monthly')),
    time TIME NOT NULL,
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    is_active BOOLEAN DEFAULT TRUE,
    next_execution TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(goal_id) -- One auto-save setting per goal
);

-- Indexes for performance
CREATE INDEX idx_auto_save_next_execution ON auto_save_settings(next_execution) WHERE is_active = TRUE;
CREATE INDEX idx_auto_save_user_id ON auto_save_settings(user_id);
CREATE INDEX idx_auto_save_goal_id ON auto_save_settings(goal_id);

-- Add updated_at trigger
CREATE TRIGGER update_auto_save_settings_updated_at 
    BEFORE UPDATE ON auto_save_settings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE auto_save_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auto_save_id UUID NOT NULL REFERENCES auto_save_settings(id) ON DELETE CASCADE,
    goal_id UUID NOT NULL REFERENCES "safeLock_account"(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'success', 'failed', 'cancelled')),
    payment_reference VARCHAR(100),
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_auto_save_transactions_auto_save_id ON auto_save_transactions(auto_save_id);
CREATE INDEX idx_auto_save_transactions_goal_id ON auto_save_transactions(goal_id);
CREATE INDEX idx_auto_save_transactions_status ON auto_save_transactions(status);
CREATE INDEX idx_auto_save_transactions_executed_at ON auto_save_transactions(executed_at);
