/* Delete default site */
LOCK TABLES `wagtailcore_site` WRITE;
DELETE FROM `wagtailcore_site`;
UNLOCK TABLES;
