-- Required before running map/char servers with durable item reform.
-- Stop writers and back up inventory first. If inventory_db is customized,
-- substitute its configured table name below. Leave other tables unchanged.
ALTER TABLE `inventory` ENGINE=InnoDB;
