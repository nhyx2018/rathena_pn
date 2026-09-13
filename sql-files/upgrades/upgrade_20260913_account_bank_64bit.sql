-- Apply to the configured map log database with game writers stopped.
-- Account balances and bank journal amounts already use signed BIGINT.
-- Character wallet storage and MAX_ZENY are deliberately unchanged.
-- Substitute the configured zeny log table name if it differs.
ALTER TABLE `zenylog` MODIFY `amount` BIGINT NOT NULL DEFAULT '0';
