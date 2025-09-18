-- Migration to support both SafeLock and MyGoal accounts in auto-save settings
-- This migration updates the auto_save_settings table to support both goal types

-- First, let's add a goal_type column to distinguish between SafeLock and MyGoal
ALTER TABLE auto_save_settings 
ADD COLUMN goal_type VARCHAR(20) DEFAULT 'safelock';

-- Update existing records to have the correct goal_type
UPDATE auto_save_settings 
SET goal_type = 'safelock' 
WHERE goal_type IS NULL;

-- Make goal_type NOT NULL
ALTER TABLE auto_save_settings 
ALTER COLUMN goal_type SET NOT NULL;

-- Add constraint to ensure goal_type is valid
ALTER TABLE auto_save_settings 
ADD CONSTRAINT check_goal_type 
CHECK (goal_type IN ('safelock', 'mygoal'));

-- Add a comment to explain the new structure
COMMENT ON COLUMN auto_save_settings.goal_type IS 'Type of goal: safelock or mygoal';
COMMENT ON COLUMN auto_save_settings.goal_id IS 'ID of the goal (can be from safeLock_account or myGoal_account)';

-- Update the auto_save_transactions table as well
ALTER TABLE auto_save_transactions 
ADD COLUMN goal_type VARCHAR(20) DEFAULT 'safelock';

-- Update existing records
UPDATE auto_save_transactions 
SET goal_type = 'safelock' 
WHERE goal_type IS NULL;

-- Make goal_type NOT NULL
ALTER TABLE auto_save_transactions 
ALTER COLUMN goal_type SET NOT NULL;

-- Add constraint
ALTER TABLE auto_save_transactions 
ADD CONSTRAINT check_transaction_goal_type 
CHECK (goal_type IN ('safelock', 'mygoal'));

-- Add comments
COMMENT ON COLUMN auto_save_transactions.goal_type IS 'Type of goal: safelock or mygoal';
COMMENT ON COLUMN auto_save_transactions.goal_id IS 'ID of the goal (can be from safeLock_account or myGoal_account)';
