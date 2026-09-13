-- Stop game writers and take a complete backup before applying this migration.
-- Substitute configured table names if char_db, inventory_db, or acc_reg_num_table differ.
-- All three sides of a bank exchange must support the same SQL transaction.
ALTER TABLE `char` ENGINE=InnoDB;
ALTER TABLE `inventory` ENGINE=InnoDB;
ALTER TABLE `acc_reg_num` ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `pn_bank_commits` (
  `account_id` INT UNSIGNED NOT NULL,
  `nonce_hi` BIGINT UNSIGNED NOT NULL,
  `nonce_lo` BIGINT UNSIGNED NOT NULL,
  `request_id` BIGINT UNSIGNED NOT NULL,
  `char_id` INT UNSIGNED NOT NULL,
  `action` INT UNSIGNED NOT NULL,
  `amount` BIGINT NOT NULL,
  `bank_before` BIGINT NOT NULL,
  `bank_after` BIGINT NOT NULL,
  `wallet_before` BIGINT NOT NULL,
  `wallet_after` BIGINT NOT NULL,
  `committed_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_id`,`nonce_hi`,`nonce_lo`,`request_id`),
  KEY `character_history` (`char_id`,`committed_at`)
) ENGINE=InnoDB;
