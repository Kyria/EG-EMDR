CREATE TABLE IF NOT EXISTS `emdr_price_history` (
  `type_id` int(11) NOT NULL,
  `date` datetime NOT NULL,
  `orders` int(5),
  `quantity` int(12),
  `low` float,
  `high` float,
  `average` float,
  `region_id` int(11) NOT NULL,
  CONSTRAINT pk PRIMARY KEY (`type_id`,`date`,`region_id`)
);

CREATE TABLE IF NOT EXISTS `emdr_raw_price` (
  `type_id` int(11) NOT NULL,
  `generated_at` datetime NOT NULL,
  `orders` int(5),
  `quantity` int(12),
  `sell_price` float,
  `buy_price` float,
  `vol_remaining` int(12),
  `vol_entered` int(12),
  `region_id` int(11),
  `station_id` int(11) NOT NULL,
  `solar_system_id` int(11),
  CONSTRAINT pk PRIMARY KEY (`type_id`,`generated_at`,`station_id`)
);
