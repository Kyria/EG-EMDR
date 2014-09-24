CREATE TABLE IF NOT EXISTS `emdr_price_history` (
  `type_id` int(11) NOT NULL,
  `date` datetime NOT NULL,
  `orders` int(7),
  `quantity` BIGINT,
  `low` float,
  `high` float,
  `average` float,
  `region_id` int(11) NOT NULL,
  CONSTRAINT pk PRIMARY KEY (`type_id`,`date`,`region_id`)
);

CREATE TABLE IF NOT EXISTS `emdr_daily_price` (
  `type_id` int(11) NOT NULL,
  `generated_at` datetime NOT NULL,
  `orders` int(5),
  `sell_price` float,
  `buy_price` float,
  `vol_remaining` BIGINT,
  `vol_entered` BIGINT,
  `region_id` int(11),
  `solar_system_id` int(11),
  CONSTRAINT pk PRIMARY KEY (`type_id`, solar_system_id)
);
