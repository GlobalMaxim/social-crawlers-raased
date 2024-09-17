#!/bin/sh
mysql -u user1 -puGYswLtj2SlkcvGLodaasl4I social_crawlers_raased1 -e "DELETE FROM social_posts_stats;DELETE FROM social_posts_reactions;DELETE FROM social_posts_requests; DELETE FROM social_posts_attachments; DELETE FROM social_parsing_posts; UPDATE social_requests SET crawling_last_run_date = Null;"
