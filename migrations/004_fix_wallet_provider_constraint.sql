-- Migration: Fix wallet provider constraint
-- Description: Updates the provider constraint to match the application enum values

-- Drop the existing constraint
ALTER TABLE wallets DROP CONSTRAINT IF EXISTS wallets_provider_check;

-- Add the correct constraint
ALTER TABLE wallets ADD CONSTRAINT wallets_provider_check 
    CHECK (provider IN ('MTN', 'Telecel', 'AirtelTigo'));
