-- Run against the configured map LOG database, with game writers stopped.
-- Append K (bank exchange) without reordering or removing existing enum values.
SET @bank_picklog_type = (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='picklog' AND COLUMN_NAME='type');
SET @bank_picklog_upgrade = IF(LOCATE("'K'", @bank_picklog_type)>0, 'SELECT 1',
  CONCAT('ALTER TABLE `picklog` MODIFY `type` ', LEFT(@bank_picklog_type,LENGTH(@bank_picklog_type)-1), ",'K') NOT NULL DEFAULT 'P'"));
PREPARE bank_picklog_statement FROM @bank_picklog_upgrade;
EXECUTE bank_picklog_statement;
DEALLOCATE PREPARE bank_picklog_statement;
