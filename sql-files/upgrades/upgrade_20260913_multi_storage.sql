-- PN multi-storage. (C) 2026 PN Development Team. GPL-3.0-or-later.
-- Source: https://github.com/patnawa/rathena_pn
-- Apply to the character database while game writers are stopped.
-- Back up existing tables first. Standard table names are used below.
-- Existing Storage I and cart rows are preserved; paid unlocks start empty.
ALTER TABLE `storage` ENGINE=InnoDB;
ALTER TABLE `cart_inventory` ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `pn_storage_02` LIKE `storage`;
ALTER TABLE `pn_storage_02` ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `pn_storage_03` LIKE `storage`;
ALTER TABLE `pn_storage_03` ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `pn_storage_04` LIKE `storage`;
ALTER TABLE `pn_storage_04` ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `pn_storage_05` LIKE `storage`;
ALTER TABLE `pn_storage_05` ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `pn_storage_06` LIKE `storage`;
ALTER TABLE `pn_storage_06` ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `pn_storage_07` LIKE `storage`;
ALTER TABLE `pn_storage_07` ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `pn_storage_08` LIKE `storage`;
ALTER TABLE `pn_storage_08` ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `pn_storage_09` LIKE `storage`;
ALTER TABLE `pn_storage_09` ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `pn_storage_10` LIKE `storage`;
ALTER TABLE `pn_storage_10` ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `pn_master_storage_01` LIKE `storage`;
ALTER TABLE `pn_master_storage_01` ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `pn_master_storage_02` LIKE `storage`;
ALTER TABLE `pn_master_storage_02` ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `pn_master_storage_03` LIKE `storage`;
ALTER TABLE `pn_master_storage_03` ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `pn_master_storage_04` LIKE `storage`;
ALTER TABLE `pn_master_storage_04` ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `pn_master_storage_05` LIKE `storage`;
ALTER TABLE `pn_master_storage_05` ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `pn_master_storage_06` LIKE `storage`;
ALTER TABLE `pn_master_storage_06` ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `pn_card_storage` LIKE `storage`;
ALTER TABLE `pn_card_storage` ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `pn_character_storage` LIKE `storage`;
ALTER TABLE `pn_character_storage` ENGINE=InnoDB;

-- Character-bound pages use a real character ownership column.
SET @pn_storage_sql = IF(EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='pn_character_storage' AND COLUMN_NAME='account_id'),
  'ALTER TABLE `pn_character_storage` CHANGE COLUMN `account_id` `char_id` int(11) unsigned NOT NULL DEFAULT 0', 'DO 0');
PREPARE pn_storage_statement FROM @pn_storage_sql;
EXECUTE pn_storage_statement;
DEALLOCATE PREPARE pn_storage_statement;

CREATE TABLE IF NOT EXISTS `pn_storage_commits` (
  `account_id` int(11) unsigned NOT NULL,
  `nonce_hi` bigint(20) unsigned NOT NULL,
  `nonce_lo` bigint(20) unsigned NOT NULL,
  `request_id` bigint(20) unsigned NOT NULL,
  `char_id` int(11) unsigned NOT NULL,
  `page` tinyint(3) unsigned NOT NULL,
  `action` tinyint(3) unsigned NOT NULL,
  `wallet_before` bigint(20) NOT NULL,
  `wallet_after` bigint(20) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_id`,`nonce_hi`,`nonce_lo`,`request_id`),
  KEY `char_id` (`char_id`)
) ENGINE=InnoDB;
