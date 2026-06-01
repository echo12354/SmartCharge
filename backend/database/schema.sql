CREATE DATABASE IF NOT EXISTS `smartcharge`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `smartcharge`;

CREATE TABLE IF NOT EXISTS `users` (
  `username` VARCHAR(64) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `role` VARCHAR(32) NOT NULL DEFAULT 'user',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_login` DATETIME NULL,
  PRIMARY KEY (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `charging_requests` (
  `request_id` VARCHAR(64) NOT NULL,
  `user_id` VARCHAR(64) NOT NULL,
  `charge_mode` VARCHAR(32) NOT NULL,
  `requested_amount` DECIMAL(10, 3) NOT NULL,
  `status` VARCHAR(32) NOT NULL DEFAULT 'WAITING',
  `queue_number` VARCHAR(32) NOT NULL DEFAULT '',
  `assigned_pile_id` VARCHAR(32) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`request_id`),
  KEY `idx_charging_requests_user_id` (`user_id`),
  KEY `idx_charging_requests_status` (`status`),
  KEY `idx_charging_requests_queue_number` (`queue_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `waiting_cars` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` VARCHAR(64) NOT NULL,
  `request_id` VARCHAR(64) NOT NULL,
  `charge_mode` VARCHAR(32) NOT NULL,
  `requested_amount` DECIMAL(10, 3) NOT NULL,
  `queue_number` VARCHAR(32) NOT NULL DEFAULT '',
  `queue_position` VARCHAR(32) NOT NULL DEFAULT 'WAITING_AREA',
  `assigned_pile_id` VARCHAR(32) NULL,
  `join_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_waiting_cars_request_id` (`request_id`),
  KEY `idx_waiting_cars_user_id` (`user_id`),
  KEY `idx_waiting_cars_mode_join_time` (`charge_mode`, `join_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `charging_piles` (
  `pile_id` VARCHAR(32) NOT NULL,
  `pile_type` VARCHAR(32) NOT NULL,
  `power` DECIMAL(10, 3) NOT NULL,
  `status` VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
  `is_enabled` TINYINT(1) NOT NULL DEFAULT 1,
  `parameters` JSON NULL,
  `total_sessions` INT UNSIGNED NOT NULL DEFAULT 0,
  `total_energy` DECIMAL(12, 3) NOT NULL DEFAULT 0,
  `total_hours` DECIMAL(12, 3) NOT NULL DEFAULT 0,
  `current_session_id` VARCHAR(64) NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`pile_id`),
  KEY `idx_charging_piles_type_status` (`pile_type`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `pile_queues` (
  `pile_id` VARCHAR(32) NOT NULL,
  `capacity` INT NOT NULL DEFAULT 2,
  `charging_request_id` VARCHAR(64) NULL,
  `waiting_request_id` VARCHAR(64) NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`pile_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `charging_sessions` (
  `session_id` VARCHAR(64) NOT NULL,
  `request_id` VARCHAR(64) NULL,
  `user_id` VARCHAR(64) NOT NULL,
  `pile_id` VARCHAR(32) NOT NULL,
  `target_amount` DECIMAL(10, 3) NOT NULL,
  `current_amount` DECIMAL(10, 3) NOT NULL DEFAULT 0,
  `pile_power` DECIMAL(10, 3) NOT NULL,
  `status` VARCHAR(32) NOT NULL DEFAULT 'PREPARING',
  `start_time` DATETIME NULL,
  `end_time` DATETIME NULL,
  `stop_reason` VARCHAR(255) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`session_id`),
  KEY `idx_charging_sessions_user_id` (`user_id`),
  KEY `idx_charging_sessions_pile_id` (`pile_id`),
  KEY `idx_charging_sessions_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `bills` (
  `bill_id` VARCHAR(64) NOT NULL,
  `session_id` VARCHAR(64) NOT NULL,
  `user_id` VARCHAR(64) NOT NULL,
  `pile_id` VARCHAR(32) NOT NULL,
  `energy_amount` DECIMAL(10, 3) NOT NULL,
  `start_time` DATETIME NOT NULL,
  `end_time` DATETIME NOT NULL,
  `duration_hours` DECIMAL(10, 3) NOT NULL DEFAULT 0,
  `price_type` VARCHAR(32) NOT NULL,
  `unit_price` DECIMAL(10, 3) NOT NULL,
  `charge_fee` DECIMAL(10, 2) NOT NULL,
  `service_fee` DECIMAL(10, 2) NOT NULL,
  `total_fee` DECIMAL(10, 2) NOT NULL,
  `status` VARCHAR(32) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`bill_id`),
  KEY `idx_bills_session_id` (`session_id`),
  KEY `idx_bills_user_id` (`user_id`),
  KEY `idx_bills_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dispatch_decisions` (
  `decision_id` VARCHAR(64) NOT NULL,
  `request_id` VARCHAR(64) NOT NULL,
  `user_id` VARCHAR(64) NOT NULL,
  `selected_pile_id` VARCHAR(32) NOT NULL,
  `strategy` VARCHAR(64) NOT NULL,
  `reason` VARCHAR(255) NOT NULL,
  `expected_completion_hours` DECIMAL(10, 3) NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`decision_id`),
  KEY `idx_dispatch_decisions_request_id` (`request_id`),
  KEY `idx_dispatch_decisions_pile_id` (`selected_pile_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `fault_records` (
  `fault_id` VARCHAR(64) NOT NULL,
  `pile_id` VARCHAR(32) NOT NULL,
  `reason` VARCHAR(255) NOT NULL,
  `affected_car_ids` JSON NULL,
  `status` VARCHAR(32) NOT NULL DEFAULT 'FAULT',
  `fault_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `recovery_time` DATETIME NULL,
  PRIMARY KEY (`fault_id`),
  KEY `idx_fault_records_pile_id` (`pile_id`),
  KEY `idx_fault_records_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `users` (`username`, `password`, `role`)
VALUES
  ('admin', '123', 'admin'),
  ('user', '123', 'user'),
  ('test1', '123', 'user'),
  ('test2', '123', 'user')
ON DUPLICATE KEY UPDATE
  `password` = VALUES(`password`),
  `role` = VALUES(`role`);

INSERT INTO `charging_piles` (`pile_id`, `pile_type`, `power`, `status`, `is_enabled`, `parameters`)
VALUES
  ('A', 'fast', 30.0, 'ACTIVE', 1, JSON_OBJECT()),
  ('B', 'fast', 30.0, 'ACTIVE', 1, JSON_OBJECT()),
  ('C', 'slow', 7.0, 'ACTIVE', 1, JSON_OBJECT()),
  ('D', 'slow', 7.0, 'ACTIVE', 1, JSON_OBJECT()),
  ('E', 'slow', 7.0, 'ACTIVE', 1, JSON_OBJECT())
ON DUPLICATE KEY UPDATE
  `pile_type` = VALUES(`pile_type`),
  `power` = VALUES(`power`);

INSERT INTO `pile_queues` (`pile_id`, `capacity`)
VALUES
  ('A', 2),
  ('B', 2),
  ('C', 2),
  ('D', 2),
  ('E', 2)
ON DUPLICATE KEY UPDATE
  `capacity` = VALUES(`capacity`);
